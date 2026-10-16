from __future__ import annotations

"""按需查：主题资料目录、按改动的文件找相关条目。

上下文按读进来的字数花。整篇文档每次全读，大半和手上的任务无关；所以资料按主题拆成
`.aip/reference/<主题>.md`，会话开始只打印目录（主题 + 什么时候读），AI 挑相关的读。

光靠 AI 开工时按任务字面挑文件会漏：很多坑和任务的说法对不上，改动却正好踩在上面。
所以再按改动的文件反查一遍——主题和条目文件头里的 paths、改动文件里写的条目锚点
（`.aip/knowledge/<时间戳_简述>`）——改代码前、提交前都能跑，只列出来，不挡任何事。
"""

import argparse
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from _aip_common import TOPIC_DIR, aip_root, force_utf8, read_text, resolve_path
from aip_item import Item, find, list_items, split_front

# 什么时候读写一句话就够；写长了目录本身又成了要整读的大文件
READ_WHEN_LIMIT = 80
# 读改动文件找锚点时跳过太大的（压缩产物、锁文件）
MAX_SCAN_BYTES = 2_000_000
# 代码注释和文档里指向条目的写法：.aip/<目录>/<时间戳_简述>，后面可以带 .md
ANCHOR = re.compile(r"\.aip/(knowledge|decisions|inbox|reuse)/(\d{8}-\d{6}_[^\s`'\"<>()（）\[\]{}，。；、,;:：*\\]+)")
# 这些状态的条目已经不算数，按 paths 反查时不列
INACTIVE = {"superseded", "closed"}


@dataclass
class Topic:
    path: Path
    meta: dict[str, str] = field(default_factory=dict)
    body: str = ""

    @property
    def title(self) -> str:
        return self.meta.get("title") or self.path.stem

    @property
    def read_when(self) -> str:
        return self.meta.get("read_when", "")

    def values(self, key: str) -> list[str]:
        return [v.strip() for v in self.meta.get(key, "").split(",") if v.strip()]


def topic_dir(repo: Path) -> Path:
    return aip_root(repo) / TOPIC_DIR


def list_topics(repo: Path) -> list[Topic]:
    d = topic_dir(repo)
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.glob("*.md")):
        meta, body = split_front(read_text(p))
        out.append(Topic(p, meta, body))
    return out


def index_lines(repo: Path) -> list[str]:
    """主题目录：一个主题一行，写清什么时候读。"""
    return [f"- {t.path.name}：{t.read_when or '（没写什么时候读）'}" for t in list_topics(repo)]


# ---------- 按改动的文件反查 ----------

@dataclass(frozen=True)
class Hit:
    target: str   # 该读的文件，相对仓库根
    title: str
    reason: str


def _rel(repo: Path, p: Path) -> str:
    return p.relative_to(repo).as_posix()


def _path_hits(paths: list[str], changed: list[str]) -> list[str]:
    return sorted({f for p in paths for f in resolve_path(p, changed)})


def anchors_in(repo: Path, rel: str) -> list[str]:
    path = repo / rel
    if not path.is_file() or path.stat().st_size > MAX_SCAN_BYTES:
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    return list(dict.fromkeys(m.group(2).removesuffix(".md") for m in ANCHOR.finditer(text)))


def relevant(repo: Path, changed: list[str]) -> tuple[list[Hit], list[str]]:
    """改这些文件该看的主题和条目，外加改动文件里指向不存在条目的锚点。"""
    changed = [c.replace("\\", "/").removeprefix("./") for c in changed]
    hits: dict[str, Hit] = {}

    def add(target: str, title: str, reason: str) -> None:
        hits.setdefault(target, Hit(target, title, reason))

    for t in list_topics(repo):
        files = _path_hits(t.values("paths"), changed)
        if files:
            add(_rel(repo, t.path), t.title, f"{t.read_when or '涉及'}：{', '.join(files[:3])}")
    items = list_items(repo)
    for i in items:
        if i.status in INACTIVE or i.type == "track":
            continue
        files = _path_hits(i.values("paths"), changed)
        if files:
            add(_rel(repo, i.path), i.title, f"涉及 {', '.join(files[:3])}")
    broken = []
    for rel in changed:
        for ref in anchors_in(repo, rel):
            try:
                item: Item = find(items, ref)
            except LookupError:
                # 文档里常拿锚点举例；.aip/ 下文档的锚点由 aip_check 查，这里只报代码里断掉的
                if not rel.endswith(".md"):
                    broken.append(f"{rel} 里的锚点「{ref}」找不到对应条目")
                continue
            add(_rel(repo, item.path), item.title, f"{rel} 里写了它的锚点")
    return list(hits.values()), broken


def staged_files(repo: Path) -> list[str]:
    try:
        r = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], cwd=repo,
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=20, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return []
    return [l for l in r.stdout.splitlines() if l] if r.returncode == 0 else []


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="按需查 .aip/：主题资料目录、改这些文件该看哪些主题和条目（只列出来，不挡任何事）。")
    ap.add_argument("--repo-root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index", help=f"列 .aip/{TOPIC_DIR}/ 下的主题和各自什么时候读")
    p = sub.add_parser("relevant", help="改这些文件该看哪些主题和条目：按文件头的 paths 和改动文件里的条目锚点")
    p.add_argument("files", nargs="*", help="要改或改了的文件，相对仓库根")
    p.add_argument("--staged", action="store_true", help="用暂存区里的改动（提交前钩子用）")
    a = ap.parse_args()
    repo = Path(a.repo_root).resolve()
    if a.cmd == "index":
        lines = index_lines(repo)
        print("\n".join(lines) if lines else f"（.aip/{TOPIC_DIR}/ 下还没有主题文件）")
        return 0
    changed = list(a.files) + (staged_files(repo) if a.staged else [])
    hits, broken = relevant(repo, changed)
    if hits:
        print("AIP：这些改动相关的主题和条目（确认没踩到再继续）：")
        for h in hits:
            print(f"- {h.target}  {h.title}  ← {h.reason}")
    if broken:
        print("AIP：锚点指向的条目不存在（改成完整的「时间戳_简述」，或删掉）：")
        for b in broken:
            print(f"- {b}")
    if not hits and not broken and not a.staged:
        print("（没有找到相关的主题和条目：用 aip_item.py list --grep 关键词 再按说法查一遍）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
