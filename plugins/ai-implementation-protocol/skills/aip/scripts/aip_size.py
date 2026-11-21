from __future__ import annotations

"""体积上限：每次都读的封顶，按需读的也不能大到读一次就占满上下文。

数值来自真实项目：整读 49KB 的 reference.md 一次要 2.5–3 万 token，大半和手上任务无关。
按字符数算不按行数：表格一行能塞几 KB。超了 aip_check 报红；快到了（九成）只在到期提醒里提一句，
免得像只超 113 字那样，到了提交时才发现要再拆一刀。
"""

import re
from dataclasses import dataclass
from pathlib import Path

from _aip_common import (
    RETIRED_SKILL_NAMES, SKILL_NAMES, TOPIC_DIR, WIDER_CHECK_VERSION, aip_root, aip_version, project_living_path,
    read_text, split_layout,
)

MUST_READ_FILE = "conventions.md"
MUST_READ_LIMIT = 8000          # 每次动手前都读的 conventions.md，整篇字符数上限
SECTION_LIMIT = 3000            # conventions.md 单节（## 开头）字符数上限
ON_DEMAND_LIMIT = 30000         # 按需读的单个文件字符数上限
LINE_LIMIT = 1000               # 单行字符数：超了多半是表格格子或一条要点里塞了一整段话
TABLE_ROW_LIMIT = 30            # 表格行数：超了说明是追加型内容，该一条一个文件
SKILL_LIMIT = 8000              # 技能正文 SKILL.md：每次调技能都整篇进上下文
NEAR_RATIO = 0.9                # 到了上限的这个比例就提醒一句
# 中文一个字大约这么多 token（用 claude CLI 回报的 input_tokens 实测：0.77–0.80）。
# 字数本身看不出代价，所以整篇超限/接近超限时顺手把 token 估出来。
TOKENS_PER_CHAR = 0.8

# 项目级技能的目录（Claude Code / Codex / 通用约定）
PROJECT_SKILL_ROOTS = (".claude/skills", ".codex/skills", ".agents/skills")
ENGINE_SKILL = "plugins/ai-implementation-protocol/skills/aip/SKILL.md"
SIZE_PATHS_RE = re.compile(r"^size_check_paths:\s*[\"']?([^\"'#\n]*)", re.M)

MUST_READ_FIX = (f"它每次动手前都要读，只留不管做什么任务都会踩到的规则，"
                 f"其余挪到 .aip/{TOPIC_DIR}/ 的主题文件")
ON_DEMAND_FIX = "按主题拆成几个文件；末尾不断追加的记录（状态注记、变更记录）挪成一条一个文件"
SKILL_FIX = "正文只留流程，细节挪到技能目录的 reference/ 下按需读"


@dataclass(frozen=True)
class Measure:
    rel: str
    what: str       # 「有」「的「铁律」一节有」「第 12 行有」……
    value: int
    limit: int
    unit: str       # 字 / 行
    fix: str
    warn_near: bool = True  # 快到上限时要不要提醒（单行长度没必要）

    @property
    def over(self) -> bool:
        return self.value > self.limit

    @property
    def near(self) -> bool:
        return self.warn_near and not self.over and self.value >= self.limit * NEAR_RATIO

    @property
    def tokens(self) -> str:
        """整篇的字数顺手换成 token：真正花掉的是 token，不是字。"""
        return f"≈{round(self.value * TOKENS_PER_CHAR / 100) * 100} token，" if self.what == "有" else ""

    def over_text(self) -> str:
        return (f"{self.rel} {self.what} {self.value} {self.unit}（{self.tokens}上限 {self.limit}，"
                f"超了 {self.value - self.limit}）：{self.fix}")

    def near_text(self) -> str:
        return (f"{self.rel} {self.what} {self.value} {self.unit}（{self.tokens}上限 {self.limit}），快到了："
                f"再往里加之前先想好怎么拆（{self.fix}）")


def sections(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for part in re.split(r"(?m)^(?=## )", text):
        if part.startswith("## "):
            out.append((part.splitlines()[0][3:].strip(), part))
    return out


def longest_table(text: str) -> int:
    best = run = 0
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            run += 1
            best = max(best, run)
        else:
            run = 0
    return max(best - 2, 0)  # 表头和分隔行不算


def size_check_paths(repo: Path) -> list[str]:
    cfg = project_living_path(repo, "config.yaml")
    m = SIZE_PATHS_RE.search(read_text(cfg)) if cfg.exists() else None
    return [p.strip() for p in (m.group(1).split(",") if m else []) if p.strip()]


def doc_targets(repo: Path) -> list[Path]:
    """要查体积的文档：.aip/ 下全部 .md，加上 config.yaml 里 size_check_paths 列的（逗号分隔的通配）。"""
    files = {p for p in aip_root(repo).rglob("*.md") if p.is_file()}
    for pattern in size_check_paths(repo):
        files |= {p for p in repo.glob(pattern) if p.is_file() and p.suffix == ".md"}
    return sorted(files)


def project_skill_files(repo: Path, pattern: str = "*/SKILL.md") -> list[Path]:
    """项目自己的技能下的文件。装进仓库的 aip 技能是引擎的拷贝，在引擎仓库里查过，这里不重复。"""
    skip = set(SKILL_NAMES) | set(RETIRED_SKILL_NAMES)
    out: list[Path] = []
    for root in PROJECT_SKILL_ROOTS:
        base = repo / root
        out += sorted(p for p in base.glob(pattern) if p.is_file() and p.relative_to(base).parts[0] not in skip)
    return out


def skill_targets(repo: Path) -> list[Path]:
    """要查体积的技能正文：引擎仓库自己的 aip 技能（一直查），项目自己的技能（0.8.1 起查）。"""
    out = [repo / ENGINE_SKILL] if (repo / ENGINE_SKILL).is_file() else []
    if aip_version(repo) >= WIDER_CHECK_VERSION:
        out += project_skill_files(repo)
    return out


def measures(repo: Path) -> list[Measure]:
    out: list[Measure] = []
    if split_layout(repo):
        must = project_living_path(repo, MUST_READ_FILE)
        for path in doc_targets(repo):
            rel = path.relative_to(repo).as_posix()
            text = read_text(path)
            if path == must:
                out.append(Measure(rel, "有", len(text), MUST_READ_LIMIT, "字", MUST_READ_FIX))
                out += [Measure(rel, f"的「{name}」一节有", len(body), SECTION_LIMIT, "字", "拆到主题文件")
                        for name, body in sections(text)]
            else:
                out.append(Measure(rel, "有", len(text), ON_DEMAND_LIMIT, "字", ON_DEMAND_FIX))
            lines = text.splitlines()
            if lines:
                n, longest = max(enumerate(lines, 1), key=lambda x: len(x[1]))
                count = sum(len(l) > LINE_LIMIT for l in lines)
                out.append(Measure(rel, f"第 {n} 行有", len(longest), LINE_LIMIT, "字",
                                   f"共 {count} 行超长。一行里塞了整段话（表格格子或一条要点），按句号拆成多条要点，"
                                   "或挪到单独的文件", warn_near=False))
            out.append(Measure(rel, "最长的一张表有", longest_table(text), TABLE_ROW_LIMIT, "行",
                               "往表尾追加的内容改成一条一个文件（可复用实现用 reuse 条目），或按小标题拆成几张表"))
    for path in skill_targets(repo):
        out.append(Measure(path.relative_to(repo).as_posix(), "有", len(read_text(path)), SKILL_LIMIT, "字", SKILL_FIX))
    return out


def over_limits(repo: Path) -> list[str]:
    return [m.over_text() for m in measures(repo) if m.over]


def near_limits(repo: Path) -> list[str]:
    return [m.near_text() for m in measures(repo) if m.near]
