from __future__ import annotations

"""到期提醒：活文档里哪些内容该复核了。

只提醒、不挡提交——日子到了不是错误，放着不管才是。会话开始（SessionStart 钩子）
和 aip check 都会打印，让 AI 在用到这些条目、或当前任务收尾时顺手复核。

一次全列出来没人看得完（真实项目一次能列出一百多项），所以按轻重排好、只列前几项，
其余给总数；完整清单用 `--all` 看。每个条目只归到最要紧的那一类，不重复出现。
"""

import argparse
import os
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from _aip_common import force_utf8, project_living_path, py_cmd, read_text
from aip_discovery import BEGIN as GUIDE_BEGIN, END as GUIDE_END
from aip_item import ENGINE_ROOT, Item, list_items

KNOWLEDGE_STALE_DAYS = 90
FULL_REVIEW_DAYS = 30
LONG_CEILING_DAYS = 365
# 会话开始只列这么多项，其余给总数
REMINDER_LIMIT = 5
LIST_LIMIT = 3
# 在建线是往前看的看板，不是流水账；超过这么多行就提醒压缩
TRACK_LINE_LIMIT = 12

DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
REVIEW_KEY_RE = re.compile(r"^review_last_full:\s*[\"']?([^\"'#\s]*)", re.M)
AIP_VERSION_RE = re.compile(r"^aip_version:\s*[\"']?([^\"'#\s]*)", re.M)
# 升级说明里每个要调整既有仓库的版本是一个二级标题，如「## 0.7.0」
UPGRADE_DOC = ENGINE_ROOT / "reference" / "upgrade.md"
UPGRADE_HEAD_RE = re.compile(r"^## (\d+(?:\.\d+)*)\b", re.M)


def parse_day(value: str) -> date | None:
    m = DATE_RE.match(value.strip())
    if not m:
        return None
    try:
        return date.fromisoformat(m.group(1))
    except ValueError:
        return None


def last_full_review(repo: Path) -> tuple[bool, date | None]:
    """返回（config.yaml 里有没有这个键, 日期）。"""
    cfg = project_living_path(repo, "config.yaml")
    if not cfg.exists():
        return False, None
    m = REVIEW_KEY_RE.search(read_text(cfg))
    if not m:
        return False, None
    return True, parse_day(m.group(1))


def _names(names: list[str]) -> str:
    shown = "、".join(f"`{n}`" for n in names[:LIST_LIMIT])
    return shown + (" 等" if len(names) > LIST_LIMIT else "")


# ---------- 条目引用了哪些文件、哪些代码名字 ----------

BACKTICK = re.compile(r"`([^`\n]+)`")
PATH_EXTS = (".py", ".cs", ".ts", ".tsx", ".js", ".vue", ".ps1", ".bat", ".sh", ".md", ".json",
             ".yml", ".yaml", ".toml", ".xaml", ".csproj", ".sln", ".go", ".rs", ".java", ".kt")
# 代码名字：点分标识符；只拿最后一段去搜。要求像代码（驼峰或带下划线）、不是全大写常量
# ——全大写多半是操作系统 / 框架的常量，本来就不在仓库里，查了只会误报。
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*(\(\))?$")
# 代码名字在代码里找，不在文档里找：文档里提到不代表代码里还有。
SYMBOL_PATHSPEC = [":(exclude)*.md", ":(exclude).aip/**", ":(exclude)docs/**"]


def _clean_path(token: str) -> str | None:
    t = token.strip()
    if any(c in t for c in " <>*%~$") or t.startswith(("http", "-", "/")):
        return None
    t = re.split(r"::|:\d", t)[0].rstrip("/").replace("\\", "/")
    name = t.rsplit("/", 1)[-1]
    if not name or name.startswith(".") and name.count(".") == 1 and "/" not in t:
        return None  # 裸扩展名，比如 `.ps1`
    if "/" not in t and not t.endswith(PATH_EXTS):
        return None
    return t


def _is_symbol(token: str) -> str | None:
    t = token.strip()
    if not IDENT.match(t):
        return None
    last = t.removesuffix("()").split(".")[-1]
    if len(last) < 4 or last.isupper() or last.lower() in {"true", "false", "none", "null"}:
        return None
    camel = re.search(r"[a-z][A-Z]", last) or (last[0].isupper() and re.search(r"[a-z]", last))
    if not (camel or "_" in last.strip("_")):
        return None
    return last


def refs(block: str) -> tuple[list[str], list[str]]:
    """一段文字里引用的（文件路径, 代码名字）。"""
    paths, symbols = [], []
    for tok in BACKTICK.findall(block):
        p = _clean_path(tok)
        if p:
            paths.append(p)
            continue
        s = _is_symbol(tok)
        if s:
            symbols.append(s)
    return list(dict.fromkeys(paths)), list(dict.fromkeys(symbols))


# ---------- 用 git 看：文件在不在、改没改、名字还有没有 ----------

def _git(repo: Path, args: list[str]) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=20, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode in (0, 1) else None


def tracked_files(repo: Path) -> list[str] | None:
    out = _git(repo, ["ls-files"])
    return None if out is None else [l for l in out.splitlines() if l]


def resolve_path(p: str, files: list[str]) -> list[str]:
    """条目里写的路径 → 仓库里对应的文件（允许写部分路径，如 `routers/admin.py`；目录算它下面全部）。"""
    exact = [f for f in files if f == p or f.startswith(p + "/")]
    if exact:
        return exact
    return [f for f in files if f.endswith("/" + p) or ("/" + p + "/") in ("/" + f)]


def commits_since(repo: Path, since: date) -> list[tuple[date, set[str]]] | None:
    out = _git(repo, ["log", f"--since={since.isoformat()}", "--format=%x00%cs", "--name-only", "--relative"])
    if out is None:
        return None
    commits = []
    for chunk in out.split("\x00")[1:]:
        lines = [l for l in chunk.splitlines() if l.strip()]
        if lines:
            d = parse_day(lines[0])
            if d:
                commits.append((d, set(lines[1:])))
    return commits


WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# 压缩过的前端产物、锁文件动辄几 MB，里面的名字不是条目要说的代码
MAX_SCAN_BYTES = 2_000_000


def symbols_in_code(repo: Path, symbols: list[str], rev: str | None = None) -> set[str] | None:
    """这些名字里哪些在代码里出现（rev 给了就查那个提交时的代码）。

    查现在的代码时自己把代码文件读一遍、切出标识符取交集：几百个名字一起交给
    `git grep -F -w` 在真实项目里要近 4 秒，自己读只要零点几秒。
    """
    if not symbols:
        return set()
    if rev is None:
        files = tracked_files(repo)
        if files is None:
            return None
        wanted, found = set(symbols), set()
        for rel in files:
            path = repo / rel
            if not is_code(rel) or not path.is_file() or path.stat().st_size > MAX_SCAN_BYTES:
                continue
            try:
                found |= wanted.intersection(WORD.findall(path.read_text(encoding="utf-8", errors="ignore")))
            except OSError:
                continue
        return found
    args = ["grep", "-I", "-F", "-w", "-o", "-h"]
    for s in symbols:
        args += ["-e", s]
    out = _git(repo, args + [rev, "--", ".", *SYMBOL_PATHSPEC])
    return None if out is None else {l.strip().rsplit(":", 1)[-1] for l in out.splitlines()}


def revs_for_days(repo: Path, days: set[date]) -> dict[date, str]:
    """每个日期当天结束时 HEAD 历史上最新的提交（和 `rev-list -1 --before=<那天 23:59:59>` 一样），一次 git 调用算完。"""
    if not days:
        return {}
    out = _git(repo, ["log", "--format=%H %cs", "HEAD"])
    commits = [(parse_day(l.split()[1]), l.split()[0]) for l in (out or "").splitlines() if len(l.split()) == 2]
    found: dict[date, str] = {}
    for day in days:
        rev = next((h for d, h in commits if d and d <= day), None)
        if rev:
            found[day] = rev
    return found


def files_at(repo: Path, rev: str) -> list[str] | None:
    out = _git(repo, ["ls-tree", "-r", "--name-only", rev])
    return None if out is None else [l for l in out.splitlines() if l]


def is_code(path: str) -> bool:
    """「代码改没改」只看代码：文档和 .aip/ 改了不代表条目说的机制变了。"""
    return not (path.endswith(".md") or path.startswith((".aip/", "docs/")))


def gone_since(repo: Path, asks: dict[str, tuple[date, list[str], list[str]]],
               files_now: list[str], symbols_now: set[str] | None) -> dict[str, list[str]]:
    """每一问（复核日期, 文件路径, 代码名字）里：那天仓库里还有、现在没了的。

    只拿「现在找不到」的去翻历史：外部接口名、环境变量这些从来不在仓库里的不会误报。
    同一个历史版本只搜一次——真实项目里逐条去搜曾占掉 6 秒。
    """
    missing: dict[str, tuple[date, list[str], list[str]]] = {}
    for key, (day, paths, symbols) in asks.items():
        mp = [p for p in paths if not resolve_path(p, files_now)]
        ms = [s for s in symbols if symbols_now is not None and s not in symbols_now]
        if mp or ms:
            missing[key] = (day, mp, ms)
    revs = revs_for_days(repo, {day for day, _, _ in missing.values()})
    by_rev: dict[str, tuple[bool, set[str]]] = {}
    for day, mp, ms in missing.values():
        if day in revs:
            need_files, syms = by_rev.get(revs[day], (False, set()))
            by_rev[revs[day]] = (need_files or bool(mp), syms | set(ms))
    then = {rev: ((files_at(repo, rev) or []) if need_files else [], symbols_in_code(repo, sorted(syms), rev) or set())
            for rev, (need_files, syms) in by_rev.items()}
    out: dict[str, list[str]] = {}
    for key, (day, mp, ms) in missing.items():
        if day not in revs:
            continue
        files_then, syms_then = then[revs[day]]
        gone = [p for p in mp if resolve_path(p, files_then)] + [s for s in ms if s in syms_then]
        if gone:
            out[key] = gone
    return out


# ---------- 该处理的事，按轻重排 ----------

@dataclass(frozen=True)
class Due:
    priority: int   # 越小越先处理
    kind: str       # 汇总时的分类名
    text: str


def knowledge_dues(repo: Path, today: date) -> list[Due]:
    """知识条目：每条只归到最要紧的一类——引用没了 > 代码改过 > 按时间到期；外加 draft。"""
    items = list_items(repo, "knowledge")
    out: list[Due] = []
    active: list[tuple[Item, date | None]] = []
    for i in items:
        if i.status == "draft":
            out.append(Due(4, "draft", f"{i.id}：还是 draft。补齐证据改 active，证伪就删"))
        elif i.status == "active":
            active.append((i, parse_day(i.meta.get("last_reviewed", ""))))
    fix = "对照现状重验：仍成立就 `aip_item.py reviewed`，缺陷已修改 fixed，被取代改 superseded"
    files = tracked_files(repo)
    if files is None:  # 不是 git 仓库或没装 git：只能按时间
        for i, seen in active:
            if seen is None or (today - seen).days > KNOWLEDGE_STALE_DAYS:
                out.append(Due(5, "到期", f"{i.id}：超过 {KNOWLEDGE_STALE_DAYS} 天没复核。{fix}"))
        return out

    dated = [seen for _, seen in active if seen]
    history = commits_since(repo, min(dated)) if dated else []
    cited_refs = {i.id: refs(i.meta.get("title", "") + "\n" + i.body) for i, _ in active}
    all_symbols = sorted({s for _, syms in cited_refs.values() for s in syms})
    symbols_now = symbols_in_code(repo, all_symbols)
    gone = gone_since(repo, {i.id: (seen, *cited_refs[i.id]) for i, seen in active if seen},
                      files, symbols_now)
    for i, seen in active:
        paths, _ = cited_refs[i.id]
        if seen is None:
            out.append(Due(5, "到期", f"{i.id}：最后复核不是日期，按到期处理。{fix}"))
        elif i.id in gone:
            out.append(Due(1, "引用没了", f"{i.id}：引用的 {_names(gone[i.id])} 在仓库里找不到了（改名、搬家或删了）。{fix}"))
        elif cited := sorted({f for p in paths for f in resolve_path(p, files) if is_code(f)}):
            touched = sorted({f for d, names in (history or []) if d > seen for f in names if f in cited})
            if touched:
                out.append(Due(2, "代码改过", f"{i.id}：引用的 {_names(touched)} 在 {seen} 复核之后改过。{fix}"))
            elif (today - seen).days > LONG_CEILING_DAYS:
                out.append(Due(6, "一年没复核", f"{i.id}：引用的代码一年没动过，按年兜底复核。{fix}"))
        elif (today - seen).days > KNOWLEDGE_STALE_DAYS:
            out.append(Due(5, "到期", f"{i.id}：{(today - seen).days} 天没复核（没写代码位置，只能按时间提醒）。{fix}"))
    return out


def reference_dues(repo: Path) -> list[Due]:
    """reference.md 里引用的文件和代码名字：上次整份 review 时还有、现在没了的。"""
    ref = project_living_path(repo, "reference.md")
    _, last = last_full_review(repo)
    files = tracked_files(repo) if ref.exists() and last else None
    if files is None:
        return []
    paths, symbols = refs(read_text(ref))
    gone = gone_since(repo, {"reference": (last, paths, symbols)}, files,
                      symbols_in_code(repo, symbols)).get("reference")
    if not gone:
        return []
    return [Due(2, "reference", f"reference.md 引用的 {_names(gone)} 在上次整份 review 后没了：改成现在的名字，或删掉这项")]


def full_review_dues(repo: Path, today: date) -> list[Due]:
    has_key, last = last_full_review(repo)
    if not has_key or last is None:
        return [Due(3, "整份 review", "config.yaml 没记上次整份 review 的日期（review_last_full）：做一次整份 .aip/ review"
                    "（aip 技能 reference/review-checklist.md），做完写上当天日期")]
    if (today - last).days > FULL_REVIEW_DAYS:
        return [Due(3, "整份 review", f"距上次整份 .aip/ review 已 {(today - last).days} 天（review_last_full: {last.isoformat()}）："
                    "按 aip 技能 reference/review-checklist.md 做一次，做完把日期改成当天")]
    return []


GUIDE_FILES = ("CLAUDE.md", "AGENTS.md")
AIP_SCRIPT_PATH = re.compile(r"[^\s`'\"()（）]*/(?:aip_[a-z_]+|install_hooks)\.py")


def guide_dues(repo: Path) -> list[Due]:
    """说明文件托管块以外写的 AIP 脚本路径，磁盘上已经没有了（引擎搬过家，手写的命令跑不起来）。"""
    out = []
    for name in GUIDE_FILES:
        path = repo / name
        if not path.exists():
            continue
        text = read_text(path)
        if GUIDE_BEGIN in text and GUIDE_END in text:
            text = text[:text.index(GUIDE_BEGIN)] + text[text.index(GUIDE_END):]
        dead = []
        for raw in dict.fromkeys(AIP_SCRIPT_PATH.findall(text)):
            if "<" in raw:
                continue  # `<skill>/scripts/...` 这类占位写法
            p = raw.replace("$CLAUDE_PROJECT_DIR", str(repo))
            p = Path(os.path.expanduser(p))
            if not (p if p.is_absolute() else repo / p).exists():
                dead.append(raw)
        if dead:
            out.append(Due(0, "说明文件", f"{name} 里写的 AIP 脚本 {_names(dead)} 已经不存在（引擎搬过家）："
                           "改成技能目录里的脚本，或删掉这段手写规矩、只留 AIP 托管块"))
    return out


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", text))


def pending_upgrades(repo: Path) -> list[str]:
    """升级说明里比这个仓库 .aip/ 整理时的版本（config.yaml 的 aip_version）新的那些版本。

    没写 aip_version 的是 0.7.0 之前建的仓库，所有调整都要做。
    """
    cfg = project_living_path(repo, "config.yaml")
    if not cfg.exists() or not UPGRADE_DOC.exists():
        return []
    m = AIP_VERSION_RE.search(read_text(cfg))
    done = _version(m.group(1)) if m else ()
    return [v for v in UPGRADE_HEAD_RE.findall(read_text(UPGRADE_DOC)) if _version(v) > done]


def upgrade_dues(repo: Path) -> list[Due]:
    pending = pending_upgrades(repo)
    if not pending:
        return []
    return [Due(0, "升级整理", f"AIP 升级后这个仓库的 .aip/ 还没按新模板整理（{'、'.join(pending)} 的调整没做）："
                "先跟用户说一声，再按 aip 技能 reference/upgrade.md 做，做完把 config.yaml 的 aip_version "
                f"改成 {max(pending, key=_version)}")]


def track_dues(repo: Path) -> list[Due]:
    out = []
    for t in list_items(repo, "track"):
        lines = [l for l in t.body.splitlines() if l.strip()]
        if len(lines) > TRACK_LINE_LIMIT:
            out.append(Due(4, "在建线太长", f"{t.id}：在建线写了 {len(lines)} 行（上限 {TRACK_LINE_LIMIT}）。"
                           "只留目标、卡在哪、下一步、先读；过程和结论进 git 提交或知识条目"))
    return out


def collect(repo: Path, today: date | None = None) -> list[Due]:
    today = today or date.today()
    dues = (upgrade_dues(repo) + guide_dues(repo) + knowledge_dues(repo, today) + reference_dues(repo)
            + full_review_dues(repo, today) + track_dues(repo))
    return sorted(dues, key=lambda d: d.priority)


def reminders(repo: Path, today: date | None = None, limit: int | None = REMINDER_LIMIT) -> list[str]:
    """要提醒的内容。超过 limit 项时第一行是汇总，后面只列最该先处理的 limit 项；limit=None 全列。"""
    dues = collect(repo, today)
    if limit is None or len(dues) <= limit:
        return [d.text for d in dues]
    counts = Counter(d.kind for d in dues)
    head = (f"共 {len(dues)} 项要处理（" + "、".join(f"{k} {n}" for k, n in counts.items())
            + f"），下面是最该先处理的 {limit} 项；完整清单：{py_cmd()} <aip 技能目录>/scripts/aip_upkeep.py --repo-root . --all")
    return [head] + [d.text for d in dues[:limit]]


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="List AIP living-doc items due for review (never fails).")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--all", action="store_true", help="全部列出，不只列最该先处理的几项")
    a = ap.parse_args()
    items = reminders(Path(a.repo_root).resolve(), limit=None if a.all else REMINDER_LIMIT)
    for line in items:
        print(f"- {line}")
    if not items:
        print("没有到期要复核的内容。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
