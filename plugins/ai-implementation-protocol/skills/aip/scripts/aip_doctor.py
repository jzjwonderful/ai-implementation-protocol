from __future__ import annotations

"""aip doctor —— 安装与环境健康检查（诊断用，不挡提交；硬闸门是 aip check）。

四类检查：
1. 项目 .aip/ 健康（文档和条目目录齐全、条目格式、无旧机制残留、到期提醒汇总）
2. 安装健康（~/.claude/skills 与 Codex 技能目录里的 aip 技能是否完整、装的版本 vs 引擎版本）
3. hook 健康（pre-commit 是否在、是否 AIP 管理、指向的引擎还在不在）
4. 引擎仓库健康（两份 plugin.json 的 version 与技能目录 VERSION 一致）

输出分级：ERROR（AIP 用不了）/ WARN（体验差或有漂移风险）/ INFO（可选建议），
每条带修复命令；有 ERROR 时退出码 1，否则 0。
"""

import argparse
import os
import re
from collections import Counter
from pathlib import Path

import aip_check
from _aip_common import RETIRED_SKILL_NAMES, SKILL_NAMES, aip_root, force_utf8, read_text
from aip_upkeep import collect
from install_hooks import PRE_COMMIT_MARK

# 引擎根 = aip 技能目录（scripts/ 与 templates/ 都在它下面），装到哪都成立。
ENGINE_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "ai-implementation-protocol"

Item = tuple[str, str, str | None]  # (级别, 说明, 修复命令)


def _read_version(path: Path) -> str | None:
    try:
        return read_text(path).strip() or None
    except OSError:
        return None


def default_codex_home(home: Path) -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return home / ".codex"


def codex_skill_paths(home: Path, skill: str, codex_home: Path | None = None) -> list[Path]:
    roots = [home / ".agents" / "skills"]
    roots.append((codex_home or default_codex_home(home)) / "skills")
    out: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        path = (root / skill / "SKILL.md").expanduser().resolve()
        key = str(path).casefold()
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


def check_project(repo: Path, engine: Path) -> list[Item]:
    out: list[Item] = []
    if not aip_root(repo).is_dir():
        out.append(("INFO", f"项目未初始化 AIP（无 {aip_root(repo)}）",
                    f"python {engine}/scripts/aip_init.py --repo-root {repo}"))
        return out
    old = aip_check.check_old_layout(repo)
    if old:
        return [("ERROR", v, f"python {engine}/scripts/aip_migrate.py --repo-root {repo}") for v in old]
    init_fix = f"python {engine}/scripts/aip_init.py --repo-root {repo}"
    for v in aip_check.check_project_files(repo):
        out.append(("ERROR", v, init_fix))
    for v in aip_check.check_item_names(repo) + aip_check.check_items(repo):
        out.append(("ERROR", v, "按提示改条目文件；改状态用 aip_item.py status"))
    for v in aip_check.check_no_orphan_slots(repo):
        out.append(("ERROR", v, "内容迁入现行活文档后删除该文件"))
    out.extend(check_due(repo, engine))
    return out


def check_due(repo: Path, engine: Path) -> list[Item]:
    """到期提醒只汇总成一行：逐条列出来一个项目能刷上百行，反而没人看。"""
    dues = collect(repo)
    if not dues:
        return []
    summary = "、".join(f"{k} {n}" for k, n in Counter(d.kind for d in dues).items())
    return [("WARN", f"有 {len(dues)} 项到期要处理（{summary}）",
             f"python {engine}/scripts/aip_upkeep.py --repo-root {repo} --all 看完整清单")]


def check_install(home: Path, engine: Path, codex_home: Path | None = None) -> list[Item]:
    out: list[Item] = []
    # 安装器只在 AIP 仓库里，不随技能分发，所以这里不能写 engine 的路径。
    reinstall = "在 AIP 仓库根跑 python scripts/install_all.py（或分端 install_claude/codex/grok_plugin.py）"
    claude_skills = home / ".claude" / "skills"
    for skill in SKILL_NAMES:
        if not (claude_skills / skill / "SKILL.md").exists():
            out.append(("WARN", f"Claude 技能未安装：~/.claude/skills/{skill}/SKILL.md", reinstall))
    claude_aip = claude_skills / "aip"
    if (claude_aip / "SKILL.md").exists() and not (claude_aip / "scripts" / "aip_init.py").exists():
        out.append(("WARN", "Claude 的 aip 技能是旧版布局（技能目录里没有 scripts/），脚本路径会找不到", reinstall))
    for skill in SKILL_NAMES:
        paths = codex_skill_paths(home, skill, codex_home)
        if not any(path.exists() for path in paths):
            pretty = " 或 ".join(str(path) for path in paths)
            out.append(("INFO", f"Codex 技能未安装：{pretty}（不用 Codex 可忽略）",
                        "在 AIP 仓库根跑 python scripts/install_codex_plugin.py"))
        if not (home / ".grok" / "skills" / skill / "SKILL.md").exists():
            out.append(("INFO", f"Grok 技能未安装：~/.grok/skills/{skill}/SKILL.md（不用 Grok 可忽略）",
                        "在 AIP 仓库根跑 python scripts/install_grok_plugin.py"))
    for skill in RETIRED_SKILL_NAMES:
        leftovers = [claude_skills / skill, home / ".grok" / "skills" / skill,
                     *(p.parent for p in codex_skill_paths(home, skill, codex_home))]
        for skill_dir in leftovers:
            if (skill_dir / "SKILL.md").exists():
                out.append(("WARN", f"已从 AIP 删掉的技能 {skill} 还装着：{skill_dir}", reinstall + "，会顺手清掉"))
    engine_ver = _read_version(engine / "VERSION")
    installs = ([("Claude", claude_aip)]
                + [("Codex", p.parent) for p in codex_skill_paths(home, "aip", codex_home)]
                + [("Grok", home / ".grok" / "skills" / "aip")])
    for label, skill_dir in installs:
        if not (skill_dir / "SKILL.md").exists():
            continue
        installed_ver = _read_version(skill_dir / "VERSION")
        if installed_ver is None:
            out.append(("WARN", f"{label} 已装的 aip 技能没有 VERSION（旧版安装）：{skill_dir}", reinstall))
        elif engine_ver and installed_ver != engine_ver:
            out.append(("WARN", f"{label} 技能版本不一致：引擎 {engine_ver}，已安装 {installed_ver}（{skill_dir}）", reinstall))
    return out


def check_hooks(repo: Path, engine: Path) -> list[Item]:
    out: list[Item] = []
    if not (repo / ".git").exists():
        out.append(("INFO", f"{repo} 不是 git 仓库，跳过 hook 检查", None))
        return out
    install_fix = f"python {engine}/scripts/install_hooks.py --repo-root {repo}"
    hook = repo / ".git" / "hooks" / "pre-commit"
    if not hook.exists():
        out.append(("WARN", "未装 pre-commit 钩子，aip check 只能靠自觉", install_fix))
        return out
    body = hook.read_text(encoding="utf-8", errors="ignore")
    if PRE_COMMIT_MARK not in body:
        out.append(("WARN", "pre-commit 钩子存在但不是 AIP 管理的（不会自动跑 aip check）",
                    f"{install_fix} --force（会覆盖现有钩子，先确认）"))
        return out
    m = re.search(r'"([^"]+/scripts/aip_check\.py)"', body)
    if m and not Path(m.group(1)).exists():
        out.append(("WARN", f"钩子指向的引擎脚本不存在：{m.group(1)}（引擎搬家或删了）", install_fix))
    return out


def check_engine_repo(repo: Path) -> list[Item]:
    # 只在 AIP 引擎自身仓库里有意义；消费方项目直接返回空。
    return [("ERROR", v, "让各端 plugin.json 的 version 与 skills/aip/VERSION 一致")
            for v in aip_check.check_engine_versions(repo)]


def run_all(repo: Path, home: Path, engine: Path, codex_home: Path | None = None) -> list[Item]:
    return (check_project(repo, engine) + check_install(home, engine, codex_home)
            + check_hooks(repo, engine) + check_engine_repo(repo))


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="AIP install/environment health check.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--home", default=str(Path.home()), help="含 .claude/、.agents/、.codex/、.grok/ 的用户主目录。")
    ap.add_argument("--codex-home", default=None,
                    help="Codex home；默认取 CODEX_HOME，未设置则为 <home>/.codex。")
    ap.add_argument("--engine-root", default=str(ENGINE_ROOT))
    a = ap.parse_args()
    home = Path(a.home).resolve()
    codex_home = Path(a.codex_home).expanduser().resolve() if a.codex_home else None
    items = run_all(Path(a.repo_root).resolve(), home,
                    Path(a.engine_root).resolve(), codex_home)
    for level, msg, fix in items:
        print(f"[{level}] {msg}" + (f"\n        修复：{fix}" if fix else ""))
    errors = sum(1 for lv, _, _ in items if lv == "ERROR")
    warns = sum(1 for lv, _, _ in items if lv == "WARN")
    print(f"aip doctor：{errors} 个 ERROR，{warns} 个 WARN，{len(items) - errors - warns} 个 INFO"
          if items else "aip doctor：一切健康")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
