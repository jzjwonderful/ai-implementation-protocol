from __future__ import annotations

"""按需查：主题资料目录、按改动的文件找相关条目。

上下文按读进来的字数花。整篇文档每次全读，大半和手上的任务无关；所以资料按主题拆成
`.aip/reference/<主题>.md`，会话开始只打印目录（主题 + 什么时候读），AI 挑相关的读。

光靠 AI 开工时按任务字面挑文件会漏：很多坑和任务的说法对不上，改动却正好踩在上面。
所以再按改动的文件反查一遍——主题和条目文件头里的 paths、条目正文里用反引号写的文件路径、
改动文件里写的条目锚点（`.aip/knowledge/<时间戳_简述>`）——改代码前、提交前都能跑，只列出来，
不挡任何事。提交前只看改动处附近的锚点：大文档改两行，不该把整篇里提到的条目全列出来。

正文里的路径比文件头的松：决策的「影响」一栏会顺手点名一串文件，正文也常提目录、只写文件名。
所以正文路径只认带目录的文件路径，只拿改动里的代码文件去比——改一句文档的措辞、改一条条目，
不该列出十几条提过它的决策。文件头的 paths 是专门写给反查用的，照常比所有改动。
"""

import argparse
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from _aip_common import TOPIC_DIR, aip_root, force_utf8, read_text, resolve_path
from aip_item import Item, find, list_items, split_front
from aip_upkeep import BACKTICK, _clean_path, is_code

# 什么时候读写一句话就够；写长了目录本身又成了要整读的大文件
READ_WHEN_LIMIT = 80
# 读改动文件找锚点时跳过太大的（压缩产物、锁文件）
MAX_SCAN_BYTES = 2_000_000
# 代码注释和文档里指向条目的写法：.aip/<目录>/<时间戳_简述>，后面可以带 .md
ANCHOR = re.compile(r"\.aip/(knowledge|decisions|inbox|reuse)/(\d{8}-\d{6}_[^\s`'\"<>()（）\[\]{}，。；、,;:：*\\]+)")
# 这些状态的条目已经不算数，按 paths 反查时不列
INACTIVE = {"superseded", "closed"}
# 提交前看改动处前后多少行里的锚点
HUNK_CONTEXT = 20


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


def anchors_in(repo: Path, rel: str, text: str | None = None) -> list[str]:
    """文件里写的条目锚点；给了 text（改动处附近的几段）就只在它里面找。"""
    if text is None:
        path = repo / rel
        if not path.is_file() or path.stat().st_size > MAX_SCAN_BYTES:
            return []
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return []
    return list(dict.fromkeys(m.group(2).removesuffix(".md") for m in ANCHOR.finditer(text)))


def body_paths(repo: Path, item: Item) -> list[str]:
    """条目正文（含标题）里用反引号写的、带目录的文件路径；只写文件名的（`SKILL.md`）和目录不算。"""
    out = []
    for tok in BACKTICK.findall(item.title + "\n" + item.body):
        p = _clean_path(tok)
        if p and "/" in p and not tok.strip().endswith("/") and not (repo / p).is_dir():
            out.append(p)
    return list(dict.fromkeys(out))


def relevant(repo: Path, changed: list[str], hunks: dict[str, str] | None = None) -> tuple[list[Hit], list[str]]:
    """改这些文件该看的主题和条目，外加改动文件里指向不存在条目的锚点。

    hunks：文件 → 改动处附近的文本（提交前用）；有的文件只在这段里找锚点。
    """
    changed = [c.replace("\\", "/").removeprefix("./") for c in changed]
    hunks = hunks or {}
    hits: dict[str, Hit] = {}

    def add(target: str, title: str, reason: str) -> None:
        hits.setdefault(target, Hit(target, title, reason))

    for t in list_topics(repo):
        files = _path_hits(t.values("paths"), changed)
        if files:
            add(_rel(repo, t.path), t.title, f"{t.read_when or '涉及'}：{', '.join(files[:3])}")
    items = list_items(repo)
    code = [c for c in changed if is_code(c)]
    for i in items:
        if i.status in INACTIVE or i.type == "track":
            continue
        files = sorted(set(_path_hits(i.values("paths"), changed)) | set(_path_hits(body_paths(repo, i), code)))
        if files:
            add(_rel(repo, i.path), i.title, f"涉及 {', '.join(files[:3])}")
    broken = []
    for rel in changed:
        for ref in anchors_in(repo, rel, hunks.get(rel)):
            try:
                item: Item = find(items, ref)
            except LookupError:
                # 文档里常拿锚点举例；.aip/ 下文档的锚点由 aip_check 查，这里只报代码里断掉的
                if not rel.endswith(".md"):
                    broken.append(f"{rel} 里的锚点「{ref}」找不到对应条目")
                continue
            add(_rel(repo, item.path), item.title, f"{rel} 里写了它的锚点")
    return list(hits.values()), broken


def _git(repo: Path, args: list[str]) -> str:
    try:
        # 中文文件名默认会被转成 "\346\226..." 这种八进制写法，对不上仓库里的路径
        r = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=20, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout if r.returncode == 0 else ""


def staged_files(repo: Path) -> list[str]:
    return [l for l in _git(repo, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"]).splitlines() if l]


def staged_hunks(repo: Path, context: int = HUNK_CONTEXT) -> dict[str, str]:
    """暂存区里每个文件改动处前后 context 行的文本。"""
    out: dict[str, list[str]] = {}
    current = None
    in_header = False  # 文件头（diff --git 到第一个 @@）里的 +++ / --- 不是内容
    diff = _git(repo, ["diff", "--cached", f"-U{context}", "--no-color", "--no-ext-diff", "--diff-filter=ACMR"])
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            in_header, current = True, None
        elif in_header and line.startswith("+++ "):
            current = line[4:].removeprefix("b/")
            out.setdefault(current, [])
        elif line.startswith("@@"):
            in_header = False
        elif not in_header and current and line[:1] in (" ", "+", "-"):
            out[current].append(line[1:])
    return {k: "\n".join(v) for k, v in out.items()}


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
    hits, broken = relevant(repo, changed, staged_hunks(repo) if a.staged else None)
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
