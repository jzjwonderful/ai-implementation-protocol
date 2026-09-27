from __future__ import annotations

"""到期提醒：活文档里哪些内容该复核了。

只提醒、不挡提交——日子到了不是错误，放着不管才是。会话开始（SessionStart 钩子）
和 aip check 都会打印，让 AI 在用到这些条目、或当前任务收尾时顺手复核。
"""

import argparse
import re
import subprocess
from datetime import date
from pathlib import Path

from _aip_common import force_utf8, project_living_path, read_text
from aip_knowledge import parse_entries

KNOWLEDGE_STALE_DAYS = 90
FULL_REVIEW_DAYS = 30
# 知识条目的状态只用这几个词开头；后面可以跟括号补一句说明。
STATUS_WORDS = ("active", "draft", "fixed", "superseded")
LIST_LIMIT = 8

DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
REVIEW_KEY_RE = re.compile(r"^review_last_full:\s*[\"']?([^\"'#\s]*)", re.M)


def parse_day(value: str) -> date | None:
    m = DATE_RE.match(value.strip())
    if not m:
        return None
    try:
        return date.fromisoformat(m.group(1))
    except ValueError:
        return None


def status_word(value: str) -> str:
    """状态字段的第一个词（小写），比如「fixed（已修，2026-06-28）」→ fixed。"""
    m = re.match(r"[A-Za-z]+", value.strip())
    return m.group(0).lower() if m else ""


def last_full_review(repo: Path) -> tuple[bool, date | None]:
    """返回（config.yaml 里有没有这个键, 日期）。"""
    cfg = project_living_path(repo, "config.yaml")
    if not cfg.exists():
        return False, None
    m = REVIEW_KEY_RE.search(read_text(cfg))
    if not m:
        return False, None
    return True, parse_day(m.group(1))


def _ids(ids: list[str]) -> str:
    shown = "、".join(ids[:LIST_LIMIT])
    return shown + (f" 等 {len(ids)} 条" if len(ids) > LIST_LIMIT else "")


# ---------- 条目引用了哪些文件、哪些代码名字 ----------

BACKTICK = re.compile(r"`([^`\n]+)`")
ENTRY_HEAD = re.compile(r"^## (K-\d+):", re.M)
PATH_EXTS = (".py", ".cs", ".ts", ".tsx", ".js", ".vue", ".ps1", ".bat", ".sh", ".md", ".json",
             ".yml", ".yaml", ".toml", ".xaml", ".csproj", ".sln", ".go", ".rs", ".java", ".kt")
# 代码名字：点分标识符；只拿最后一段去搜。要求像代码（驼峰或带下划线）、不是全大写常量
# ——全大写多半是操作系统 / 框架的常量，本来就不在仓库里，查了只会误报。
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*(\(\))?$")
# 代码名字在代码里找，不在文档里找：文档里提到不代表代码里还有。
SYMBOL_PATHSPEC = [":(exclude)*.md", ":(exclude).aip/**", ":(exclude)docs/**"]
LONG_CEILING_DAYS = 365


def entry_blocks(text: str) -> dict[str, str]:
    heads = list(ENTRY_HEAD.finditer(text))
    return {m.group(1): text[m.start(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
            for i, m in enumerate(heads)}


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
    """一个条目里引用的（文件路径, 代码名字）。"""
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


def symbols_in_code(repo: Path, symbols: list[str], rev: str | None = None) -> set[str] | None:
    """这些名字里哪些在代码里出现（rev 给了就查那个提交时的代码）。"""
    if not symbols:
        return set()
    args = ["grep", "-I", "-F", "-w", "-o", "-h"]
    for s in symbols:
        args += ["-e", s]
    if rev:
        args.append(rev)
    out = _git(repo, args + ["--", ".", *SYMBOL_PATHSPEC])
    return None if out is None else {l.strip().rsplit(":", 1)[-1] for l in out.splitlines()}


def commit_at(repo: Path, day: date) -> str | None:
    out = _git(repo, ["rev-list", "-1", f"--before={day.isoformat()} 23:59:59", "HEAD"])
    return out.strip() or None if out else None


def files_at(repo: Path, rev: str) -> list[str] | None:
    out = _git(repo, ["ls-tree", "-r", "--name-only", rev])
    return None if out is None else [l for l in out.splitlines() if l]


def is_code(path: str) -> bool:
    """「代码改没改」只看代码：文档和 .aip/ 改了不代表条目说的机制变了。"""
    return not (path.endswith(".md") or path.startswith((".aip/", "docs/")))


def knowledge_findings(repo: Path, today: date) -> dict[str, list[str]]:
    """把 active 条目分成：代码改过、引用没了、按时间到期、一年兜底；外加 draft。

    「引用没了」只认最后复核那天仓库里还有、现在没了的文件和代码名字——
    外部接口名、环境变量、服务器路径这类本来就不在仓库里的，不会误报。
    """
    kn = project_living_path(repo, "knowledge.md")
    found = {"changed": [], "missing": [], "stale": [], "ceiling": [], "drafts": []}
    if not kn.exists():
        return found
    text = read_text(kn)
    blocks = entry_blocks(text)
    files = tracked_files(repo)
    active = []
    for e in parse_entries(text):
        word = status_word(e["fields"].get("状态", ""))
        if word == "draft":
            found["drafts"].append(e["id"])
        elif word == "active":
            active.append((e["id"], parse_day(e["fields"].get("最后复核", "")), blocks.get(e["id"], "")))
    if files is None:  # 不是 git 仓库或没装 git：只能按时间
        for kid, seen, _ in active:
            if seen is None or (today - seen).days > KNOWLEDGE_STALE_DAYS:
                found["stale"].append(kid)
        return found

    dated = [seen for _, seen, _ in active if seen]
    history = commits_since(repo, min(dated)) if dated else []
    all_symbols = sorted({s for _, _, b in active for s in refs(b)[1]})
    present_now = symbols_in_code(repo, all_symbols)
    then: dict[date, tuple[list[str], set[str]] | None] = {}
    for seen in set(dated):
        rev = commit_at(repo, seen)
        if not rev:
            then[seen] = None
            continue
        syms = sorted({s for _, d, b in active if d == seen for s in refs(b)[1]})
        then[seen] = (files_at(repo, rev) or [], symbols_in_code(repo, syms, rev) or set())

    for kid, seen, block in active:
        paths, symbols = refs(block)
        hits = {p: resolve_path(p, files) for p in paths}
        snapshot = then.get(seen) if seen else None
        if snapshot:
            files_then, syms_then = snapshot
            gone = [p for p, h in hits.items() if not h and resolve_path(p, files_then)]
            if present_now is not None:
                gone += [s for s in symbols if s in syms_then and s not in present_now]
            if gone:
                found["missing"].append(f"{kid}（{'、'.join(gone[:3])}{' 等' if len(gone) > 3 else ''}）")
        cited = sorted({f for h in hits.values() for f in h if is_code(f)})
        if seen is None:
            found["stale"].append(kid)
        elif cited:
            touched = sorted({f for d, names in (history or []) if d > seen for f in names if f in cited})
            if touched:
                found["changed"].append(f"{kid}（{touched[0]}{' 等' if len(touched) > 1 else ''}）")
            elif (today - seen).days > LONG_CEILING_DAYS:
                found["ceiling"].append(kid)
        elif (today - seen).days > KNOWLEDGE_STALE_DAYS:
            found["stale"].append(kid)
    return found


def reference_gone(repo: Path) -> list[str]:
    """reference.md 里引用的文件和代码名字：上次整份 review 时还有、现在没了的。"""
    ref = project_living_path(repo, "reference.md")
    _, last = last_full_review(repo)
    if not ref.exists() or last is None:
        return []
    files = tracked_files(repo)
    rev = commit_at(repo, last) if files is not None else None
    if not rev:
        return []
    paths, symbols = refs(read_text(ref))
    files_then = files_at(repo, rev) or []
    gone = [p for p in paths if not resolve_path(p, files) and resolve_path(p, files_then)]
    syms_then = symbols_in_code(repo, symbols, rev) or set()
    now = symbols_in_code(repo, symbols)
    if now is not None:
        gone += [s for s in symbols if s in syms_then and s not in now]
    return gone


def reminders(repo: Path, today: date | None = None) -> list[str]:
    today = today or date.today()
    out: list[str] = []
    fix = "对照现状重验：仍成立就更新「最后复核」；缺陷已修改 fixed；被新机制取代标 superseded(by K-N)。"

    f = knowledge_findings(repo, today)
    if f["changed"]:
        out.append(f"知识 {len(f['changed'])} 条引用的代码在最后复核之后改过：{_ids(f['changed'])}。{fix}")
    if f["missing"]:
        out.append(f"知识 {len(f['missing'])} 条引用的文件或代码名字在仓库里找不到了（可能改名、搬家或删了）：{_ids(f['missing'])}。{fix}")
    if f["stale"]:
        out.append(f"知识 {len(f['stale'])} 条超过 {KNOWLEDGE_STALE_DAYS} 天没复核（条目没写代码位置，只能按时间提醒）：{_ids(f['stale'])}。{fix}")
    if f["ceiling"]:
        out.append(f"知识 {len(f['ceiling'])} 条一年没复核（引用的代码没动过，按年兜底）：{_ids(f['ceiling'])}。{fix}")
    if f["drafts"]:
        out.append(f"知识 {len(f['drafts'])} 条还是 draft：{_ids(f['drafts'])}。补齐证据改 active，证伪就删。")
    gone = reference_gone(repo)
    if gone:
        out.append(f"reference.md 引用的 {_ids(gone)} 在上次整份 review 后没了（改名、搬家或删了）：改成现在的名字，或删掉这项。")

    has_key, last = last_full_review(repo)
    if not has_key or last is None:
        out.append(
            "config.yaml 没记上次整份 review 的日期（review_last_full）："
            "做一次整份 .aip/ review（aip 技能 reference/review-checklist.md），做完写上当天日期。"
        )
    elif (today - last).days > FULL_REVIEW_DAYS:
        out.append(
            f"距上次整份 .aip/ review 已 {(today - last).days} 天（review_last_full: {last.isoformat()}）："
            "按 aip 技能 reference/review-checklist.md 做一次，做完把日期改成当天。"
        )
    return out


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="List AIP living-doc items due for review (never fails).")
    ap.add_argument("--repo-root", required=True)
    a = ap.parse_args()
    items = reminders(Path(a.repo_root).resolve())
    for line in items:
        print(f"- {line}")
    if not items:
        print("没有到期要复核的内容。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
