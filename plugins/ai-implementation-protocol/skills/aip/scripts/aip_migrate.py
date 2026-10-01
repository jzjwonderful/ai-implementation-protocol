from __future__ import annotations

"""把 0.5.0 之前「一类一个大文件」的 .aip/ 迁成一条一个文件。

旧布局：knowledge.md（K-N）、decisions.md（ADR-N）、inbox.md（I-N）、OVERVIEW.md 手写看板、
knowledge_index.md。迁完：knowledge/、decisions/、inbox/、tracks/ 下一条一个文件，
OVERVIEW.md 删掉（看板由会话开始钩子按目录打印），knowledge_index.md 不再需要。
旧看板里标了做完的线不迁：做完的线不留文件。

- 默认只预览，打印会生成哪些文件、有哪些要人看的地方；加 --apply 才写。
- 旧编号（K-185、ADR-3、I-14）写进每条的 aliases，旧引用照样能用 aip_item.py show 查到；
  条目正文和 .aip/ 下其余说明文件里提到的旧编号换成完整标识（撞号的留着，列进要人看的地方）。
- 时间戳取条目标题第一次出现在 git 里的那次提交的时间（跟着文件改名往前找）；找不到用标题那一行
  的 git blame 时间，再没有用现在。一次提交带进来的多条会是同一秒，靠简述区分。
- 标题太长的，简述由 AI 起：--names-out 导出对照表，填好后 --names 读回；没填的按分句截。
- 旧看板里带状态标记（▶ ⏸ ⛔ [active] 等）的三级标题变成在建线；看板里其余手写内容
  收进一条「待整理」的旁路问题，不丢，由 AI 按 reference/migrate.md 分拣。
"""

import argparse
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from _aip_common import AIP_DIR, OLD_LAYOUT_FILES, force_utf8, project_living_path, read_text
from aip_item import STAMP_FORMAT, TYPES, Item, file_name, item_files, render, slug_is_cut, slugify, type_dir

DATE_IN = re.compile(r"(\d{4}-\d{2}-\d{2})")
FIELD = re.compile(r"^- ([^:：\n]+?)\s*[:：]\s*(.*)$")
FENCE = "```"
AUTO_BEGIN = "<!-- AIP:AUTO-DIGEST:BEGIN"

KNOWLEDGE_HEAD = re.compile(r"^(##) (K-\d+)\s*[:：]\s*(.*)$")
DECISION_HEAD = re.compile(r"^(##) (ADR-\d+)\s*[:：]\s*(.*)$")
INBOX_HEAD = re.compile(r"^(#{2,3}) (I-\d+)\s*[:：]\s*(.*)$")
# 知识条目里挪进文件头的字段：正文里不再留，免得两处各写各的
KNOWLEDGE_HEAD_FIELDS = {"分类": "category", "适用范围": "scope", "最后复核": "last_reviewed", "rule_id": "rule_id"}
INBOX_CLOSED = ("关闭", "已修", "已解决", "不做", "won't-fix", "已立项", "已完成", "已处理")
TRACK_MARKS = (("⛔", "blocked"), ("[blocked]", "blocked"), ("阻塞", "blocked"), ("⏸", "paused"),
               ("[paused]", "paused"), ("▶", "active"), ("[active]", "active"), ("[done]", "done"))
PLACEHOLDER = re.compile(r"^[（(]当前(无|没有)[^）)]*[）)]$")


@dataclass
class Block:
    old_id: str
    title: str
    line: int                 # 标题在原文件里的行号（从 1 起），用来查 git blame
    lines: list[str] = field(default_factory=list)


@dataclass
class Plan:
    items: list[Item] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    alias_to_id: dict[str, str] = field(default_factory=dict)   # 旧编号 → 完整标识（撞号时取第一条）
    twins: set[str] = field(default_factory=set)                # 撞号的旧编号
    anchors: dict[str, str] = field(default_factory=dict)       # 锚点里的 rule_id 或旧编号 → 知识条目标识
    unnamed: list[Item] = field(default_factory=list)           # 标题太长、简述还是自动截的


# ---------- 读旧文件 ----------

def blocks(text: str, head: re.Pattern) -> list[Block]:
    """按标题切条目；围栏代码块和 HTML 注释里的（模板示例）不算。条目到同级或更高级标题为止。"""
    out: list[Block] = []
    cur: Block | None = None
    level = 0
    in_fence = in_comment = False
    for n, line in enumerate(text.splitlines(), start=1):
        s = line.strip()
        if s.startswith(FENCE):
            in_fence = not in_fence
        if s.startswith("<!--") and "-->" not in s:
            in_comment = True
        elif in_comment and "-->" in s:
            in_comment = False
            continue
        m = head.match(line) if not (in_fence or in_comment) else None
        if m:
            cur = Block(m.group(2), m.group(3).strip(), n)
            level = len(m.group(1))
            out.append(cur)
            continue
        heading = re.match(r"^(#+) ", line)
        if cur and heading and len(heading.group(1)) <= level and not in_fence:
            cur = None
        if cur:
            cur.lines.append(line)
    return out


def fields(lines: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in lines:
        m = FIELD.match(line)
        if m and m.group(1).strip() not in out:
            out[m.group(1).strip()] = m.group(2).strip()
    return out


def blame_times(repo: Path, rel: str) -> dict[int, datetime]:
    """每一行进 git 的时间（作者时间）。不是 git 仓库或文件没提交过就是空。"""
    try:
        r = subprocess.run(["git", "blame", "--line-porcelain", "--", rel], cwd=repo, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return {}
    if r.returncode != 0:
        return {}
    out: dict[int, datetime] = {}
    line_no = 0
    when: datetime | None = None
    for line in r.stdout.splitlines():
        head = re.match(r"^[0-9a-f]{40} \d+ (\d+)", line)
        if head:
            line_no = int(head.group(1))
        elif line.startswith("author-time "):
            when = datetime.fromtimestamp(int(line.split()[1]))
        elif line.startswith("\t") and when:
            out[line_no] = when
    return out


def first_seen(repo: Path, rel: str, head: re.Pattern) -> dict[str, datetime]:
    """每个旧编号的标题第一次出现在 git 里的时间（作者时间），跟着文件改名往前找。

    git blame 给的是标题那一行最后一次改的时间，旁路问题关闭时加删除线就会变成关闭那天，
    所以要从历史里找「第一次加进来」。--follow 配 --reverse 会漏提交，只能倒序看、后看到的覆盖先看到的。
    """
    try:
        r = subprocess.run(["git", "log", "--follow", "--format=%x01%at", "-p", "--unified=0", "--", rel],
                           cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=120)
    except (OSError, subprocess.SubprocessError):
        return {}
    out: dict[str, datetime] = {}
    when: datetime | None = None
    for line in r.stdout.splitlines() if r.returncode == 0 else []:
        if line.startswith("\x01"):
            when = datetime.fromtimestamp(int(line[1:]))
        elif when and line.startswith("+") and not line.startswith("+++"):
            m = head.match(line[1:])
            if m:
                out[m.group(2)] = when
    return out


@dataclass
class EntryTimes:
    """一个旧文件里各条目进 git 的时间。"""
    first: dict[str, datetime]    # 旧编号 → 标题第一次进 git 的时间
    lines: dict[int, datetime]    # 行号 → git blame 时间，找不到第一次时的后备
    used: set[str] = field(default_factory=set)

    def stamp(self, block: Block) -> str:
        when = None
        # 撞号的两条只有先出现的那条能用「第一次」，另一条退回 blame
        if block.old_id and block.old_id not in self.used:
            when = self.first.get(block.old_id)
            self.used.add(block.old_id)
        return (when or self.lines.get(block.line) or datetime.now()).strftime(STAMP_FORMAT)


def entry_times(repo: Path, rel: str, head: re.Pattern | None) -> EntryTimes:
    return EntryTimes(first_seen(repo, rel, head) if head else {}, blame_times(repo, rel))


def _body(lines: list[str], drop: set[str] = frozenset(), rename: dict[str, str] | None = None) -> str:
    out = []
    for line in lines:
        m = FIELD.match(line)
        key = m.group(1).strip() if m else ""
        if key in drop:
            continue
        if rename and key in rename:
            line = f"- {rename[key]}: {m.group(2).strip()}"
        out.append(line)
    return "\n".join(out).strip()


# ---------- 各类条目怎么转 ----------

def _item(repo: Path, type_name: str, stamp: str, status: str, title: str, meta: dict[str, str], body: str) -> Item:
    slug = slugify(title)
    all_meta = {"title": title, "status": status, **meta}
    return Item(type_dir(repo, type_name) / file_name(stamp, type_name, status, slug),
                stamp, type_name, status, slug, all_meta, body)


def knowledge_items(repo: Path, plan: Plan) -> list[tuple[Item, str]]:
    """返回（条目, 被谁取代的旧编号）；取代关系等全部条目建完再对上。"""
    rel = f"{AIP_DIR}/knowledge.md"
    path = repo / rel
    if not path.exists():
        return []
    times = entry_times(repo, rel, KNOWLEDGE_HEAD)
    out = []
    for b in blocks(read_text(path), KNOWLEDGE_HEAD):
        f = fields(b.lines)
        raw = f.get("状态", "")
        word = (re.match(r"[A-Za-z]+", raw) or [""])[0].lower()
        meta = {v: f[k] for k, v in KNOWLEDGE_HEAD_FIELDS.items() if f.get(k)}
        meta["aliases"] = b.old_id
        extra = []
        if word not in TYPES["knowledge"].statuses:
            plan.notes.append(f"{b.old_id} 的状态「{raw}」认不出，先记成 draft，迁完请核对")
            word = "draft"
        if raw and raw.lower() != word:
            extra.append(f"- 状态说明（迁移前）: {raw}")
        if last := DATE_IN.search(meta.get("last_reviewed", "")):
            meta["last_reviewed"] = last.group(1)
        body = "\n".join(extra + [_body(b.lines, drop=set(KNOWLEDGE_HEAD_FIELDS) | {"状态"})]).strip()
        by = re.search(r"K-\d+", raw) if word == "superseded" else None
        out.append((_item(repo, "knowledge", times.stamp(b), word, b.title, meta, body), by.group(0) if by else ""))
    return out


def decision_items(repo: Path) -> list[tuple[Item, str]]:
    rel = f"{AIP_DIR}/decisions.md"
    path = repo / rel
    if not path.exists():
        return []
    times = entry_times(repo, rel, DECISION_HEAD)
    out = []
    for b in blocks(read_text(path), DECISION_HEAD):
        f = fields(b.lines)
        key = next((k for k in f if "状态" in k), "")
        raw = f.get(key, "")
        by = re.search(r"已被\s*(ADR-\d+)", raw)
        status = "superseded" if by else "accepted"
        body = _body(b.lines, rename={key: f"{key}（迁移前）"} if key else None)
        item = _item(repo, "decision", times.stamp(b), status, b.title,
                     {"aliases": b.old_id}, body)
        out.append((item, by.group(1) if by else ""))
    return out


def inbox_items(repo: Path) -> list[Item]:
    rel = f"{AIP_DIR}/inbox.md"
    path = repo / rel
    if not path.exists():
        return []
    times = entry_times(repo, rel, INBOX_HEAD)
    out = []
    for b in blocks(read_text(path), INBOX_HEAD):
        f = fields(b.lines)
        key = next((k for k in f if "状态" in k), "")
        raw = f.get(key, "")
        closed = b.title.startswith("~~") or any(w in raw for w in INBOX_CLOSED)
        title = b.title.strip("~ ")
        body = _body(b.lines, rename={key: f"{key}（迁移前）"} if key else None)
        out.append(_item(repo, "inbox", times.stamp(b),
                         "closed" if closed else "open", title, {"aliases": b.old_id}, body))
    return out


def _track_status(heading: str) -> str | None:
    return next((s for mark, s in TRACK_MARKS if mark in heading), None)


def _track_title(heading: str) -> str:
    t = heading
    for mark, _ in TRACK_MARKS:
        t = t.replace(mark, "")
    t = re.sub(r"\s+状态\s*[:：].*$", "", t)
    return re.sub(r"\s+", " ", t).strip()


def board_items(repo: Path) -> list[Item]:
    """旧看板手写部分：带状态标记的三级标题 → 在建线；其余非占位内容 → 一条待整理的旁路问题。"""
    rel = f"{AIP_DIR}/OVERVIEW.md"
    path = repo / rel
    if not path.exists():
        return []
    text = read_text(path)
    hand = text[:text.index(AUTO_BEGIN)] if AUTO_BEGIN in text else text
    times = entry_times(repo, rel, None)
    out: list[Item] = []
    leftover: list[str] = []
    cur: tuple[str, int, list[str]] | None = None

    def flush() -> None:
        if cur:
            heading, line, lines = cur
            if _track_status(heading) == "done":
                return  # 做完的线不留文件
            b = Block("", _track_title(heading), line, lines)
            out.append(_item(repo, "track", times.stamp(b), _track_status(heading),
                             b.title, {}, "\n".join(lines).strip()))

    for n, line in enumerate(hand.splitlines(), start=1):
        if line.startswith("### ") and _track_status(line):
            flush()
            cur = (line[4:].strip(), n, [])
        elif line.startswith(("## ", "### ", "# ")):
            flush()
            cur = None
            if line.startswith("### "):
                leftover.append(line)
            elif line.startswith("## "):
                leftover.append("#" + line)  # 降一级，放进条目正文
        elif cur:
            cur[2].append(line)
        elif not line.startswith(">"):
            leftover.append(line)
    flush()
    meaningful = [l for l in leftover if l.strip() and not l.startswith("#") and not PLACEHOLDER.match(l.strip())]
    if meaningful:
        body = ("迁移前手写看板里除在建线以外的内容，原样搬过来待分拣：还要做的拆成旁路问题或在建线，"
                "已经过时的删掉，都处理完把本条标 closed。\n\n" + "\n".join(leftover).strip())
        out.append(_item(repo, "inbox", datetime.now().strftime(STAMP_FORMAT), "open",
                         "迁移前看板里的其他内容待整理", {}, body))
    return out


# ---------- 汇总、落盘 ----------

def _dedupe(items: list[Item]) -> None:
    seen: set[str] = set()
    for i in items:
        base, n = i.slug, 2
        while i.id in seen:
            i.slug = f"{base}-{n}"
            n += 1
        i.path = i.path.with_name(file_name(i.stamp, i.type, i.status, i.slug))
        seen.add(i.id)


def _link_superseded(pairs: list[tuple[Item, str]], alias_to_id: dict[str, str], plan: Plan) -> None:
    for item, old in pairs:
        if item.status == "superseded" and not old:
            item.meta["superseded_by"] = "迁移前没写明被什么取代"
            plan.notes.append(f"{item.meta['aliases']} 标了 superseded 但没写被哪条取代：补上 superseded_by（条目标识或一句话）")
            continue
        if not old:
            continue
        if old in alias_to_id:
            item.meta["superseded_by"] = alias_to_id[old]
        else:
            plan.notes.append(f"{item.meta['aliases']} 写的是被 {old} 取代，但找不到 {old}：先改成 draft/accepted 或补上取代关系")
            item.status = "draft" if item.type == "knowledge" else "accepted"
            item.meta["status"] = item.status
            item.path = item.path.with_name(file_name(item.stamp, item.type, item.status, item.slug))


DOCS_SHOWN = 5   # 报告里逐个列出的说明文件数，多了只报总数
# 标题里的旧编号不换：换成完整标识标题会长得没法读，旧编号靠 aliases 照样查得到
KEEP_OLD_REFS = {"title", "status", "aliases", "rule_id", "superseded_by"}
# 「::」后面的是认不出的锚点，留给锚点报告，不当旧编号换
OLD_REF = re.compile(r"(?<![A-Za-z0-9_-])(?<!::)(?:K|ADR|I)-\d+(?![A-Za-z0-9_])")
ANCHOR = re.compile(r"\.aip/knowledge\.md::([A-Za-z0-9_-]+)")


def anchor_targets(items: list[Item]) -> dict[str, str]:
    """代码注释锚点 `.aip/knowledge.md::<rule_id 或旧编号>` → 条目标识。"""
    out: dict[str, str] = {}
    for i in items:
        if i.type != "knowledge":
            continue
        for key in [i.meta.get("rule_id", "")] + i.values("aliases"):
            if key:
                out.setdefault(key, i.id)
    return out


def rewrite_old_refs(text: str, plan: Plan) -> tuple[str, set[str], int]:
    """锚点换成 `.aip/knowledge/<标识>`，旧编号（K-12 / ADR-3 / I-7）换成完整标识。

    撞号的旧编号没法定是哪条，原样留着。返回（新文本, 留着的撞号编号, 换了几处）。
    """
    kept: set[str] = set()
    count = 0

    def anchor(m: re.Match) -> str:
        nonlocal count
        target = plan.anchors.get(m.group(1))
        if not target:
            return m.group(0)
        count += 1
        return f"{AIP_DIR}/knowledge/{target}"

    def old_ref(m: re.Match) -> str:
        nonlocal count
        old = m.group(0)
        if old in plan.twins:
            kept.add(old)
            return old
        if old not in plan.alias_to_id:
            return old
        count += 1
        return plan.alias_to_id[old]
    return OLD_REF.sub(old_ref, ANCHOR.sub(anchor, text)), kept, count


NAMES_HEAD = (f"# 标题太长、简述是自动截的条目。把第三列改成 8–24 字、说清这条是什么的短名字（不要截半句），"
              f"其余列别动；存好后迁移时加 --names <本文件>。没改的行按自动截的来。")


def write_names(path: Path, plan: Plan) -> None:
    rows = [f"{i.id}\t{i.title.replace(chr(9), ' ')}\t{i.slug}" for i in plan.unnamed]
    path.write_text("\n".join([NAMES_HEAD, "# 标识\t标题\t简述", *rows]) + "\n", encoding="utf-8")


def read_names(path: Path) -> dict[str, str]:
    """对照表 → {自动生成的标识: AI 起的简述}。"""
    out: dict[str, str] = {}
    for line in read_text(path).splitlines():
        cols = line.split("\t")
        if line.startswith("#") or len(cols) < 3:
            continue
        out[cols[0].strip()] = cols[2].strip()
    return out


def _apply_names(items: list[Item], names: dict[str, str], plan: Plan) -> None:
    by_id = {i.id: i for i in items}
    for key, name in names.items():
        item = by_id.get(key)
        if item is None:
            plan.notes.append(f"简述对照表里的 {key} 对不上任何条目（导出后旧文件又改过？），没用上：重新导出")
            continue
        if not name or slug_is_cut(name):
            plan.notes.append(f"简述对照表里给 {key} 起的「{name}」是空的或超过 24 字，没用上")
            continue
        item.slug = slugify(name)
        item.path = item.path.with_name(file_name(item.stamp, item.type, item.status, item.slug))


def build_plan(repo: Path, names: dict[str, str] | None = None) -> Plan:
    plan = Plan()
    kn = knowledge_items(repo, plan)
    dec = decision_items(repo)
    plan.items = [i for i, _ in kn] + [i for i, _ in dec] + inbox_items(repo) + board_items(repo)
    _dedupe(plan.items)
    auto = {i.id: i.slug for i in plan.items}
    if names:
        _apply_names(plan.items, names, plan)
        _dedupe(plan.items)
    plan.unnamed = [i for i in plan.items if slug_is_cut(i.title) and auto.get(i.id) == i.slug]
    for i in plan.items:
        for alias in i.values("aliases"):
            if alias in plan.alias_to_id:
                plan.twins.add(alias)
                plan.notes.append(f"旧编号 {alias} 有两条（撞号）：两条都保留了这个旧编号，按旧编号查会列出两条")
            plan.alias_to_id.setdefault(alias, i.id)
    _link_superseded(kn + dec, plan.alias_to_id, plan)
    plan.anchors = anchor_targets(plan.items)
    kept: set[str] = set()
    for i in plan.items:
        i.body, twins, _ = rewrite_old_refs(i.body, plan)
        kept |= twins
        for key in i.meta.keys() - KEEP_OLD_REFS:
            i.meta[key], twins, _ = rewrite_old_refs(i.meta[key], plan)
            kept |= twins
    if kept:
        plan.notes.append(f"正文里提到撞号的旧编号 {'、'.join(sorted(kept))}，没法定是哪条，原样留着：迁完请改成完整标识")
    return plan


def rewrite_anchors(repo: Path, plan: Plan, write: bool) -> tuple[int, dict[str, list[str]]]:
    """把锚点改写成 `.aip/knowledge/<时间戳_简述>`。返回（改了几处, {认不出的锚点: [文件]}）。"""
    targets = plan.anchors
    try:
        r = subprocess.run(["git", "grep", "-l", "-E", ANCHOR.pattern, "--", ".", f":(exclude){AIP_DIR}/**"],
                           cwd=repo, capture_output=True, text=True, encoding="utf-8", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return 0, {}
    done, unknown = 0, {}
    for rel in (r.stdout.splitlines() if r.returncode == 0 else []):
        path = repo / rel
        text = read_text(path)

        def sub(m: re.Match) -> str:
            nonlocal done
            key = m.group(1)
            if key not in targets:
                unknown.setdefault(key, []).append(rel)
                return m.group(0)
            done += 1
            return f"{AIP_DIR}/knowledge/{targets[key]}"
        new = ANCHOR.sub(sub, text)
        if write and new != text:
            path.write_text(new, encoding="utf-8", newline="")
    return done, unknown


def rewrite_docs(repo: Path, plan: Plan, write: bool) -> dict[str, int]:
    """.aip/ 下留下来的文件（reference.md、conventions.md、config.yaml、specs/ 等）里的锚点和旧编号换成完整标识。

    返回 {文件: 处数}。
    """
    root = repo / AIP_DIR
    skip_files = set(OLD_LAYOUT_FILES) | {"OVERVIEW.md"}
    skip_dirs = {t.folder for t in TYPES.values()}
    out: dict[str, int] = {}
    kept: set[str] = set()
    for path in sorted([*root.rglob("*.md"), root / "config.yaml"]):
        rel = path.relative_to(root)
        if not path.is_file() or rel.parts[0] in skip_dirs or str(rel) in skip_files:
            continue
        text = read_text(path)
        new, twins, count = rewrite_old_refs(text, plan)
        kept |= twins
        if count:
            out[f"{AIP_DIR}/{rel.as_posix()}"] = count
            if write:
                path.write_text(new, encoding="utf-8", newline="")
    if kept:
        plan.notes.append(f".aip/ 说明文件里提到撞号的旧编号 {'、'.join(sorted(kept))}，原样留着：迁完请改成完整标识")
    return out


def old_name_mentions(repo: Path) -> list[str]:
    """.aip/ 以外还在引用旧文件名的地方（代码注释锚点、说明文件、脚本）。"""
    pattern = r"\.aip/(knowledge|decisions|inbox|knowledge_index)\.md"
    try:
        r = subprocess.run(["git", "grep", "-l", "-E", pattern, "--", ".", f":(exclude){AIP_DIR}/**"],
                           cwd=repo, capture_output=True, text=True, encoding="utf-8", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return []
    return [l for l in r.stdout.splitlines() if l] if r.returncode == 0 else []


def aip_dirty(repo: Path) -> bool:
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", AIP_DIR], cwd=repo, capture_output=True,
                           text=True, encoding="utf-8", timeout=20)
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0 and bool(r.stdout.strip())


def apply(repo: Path, plan: Plan, engine: Path) -> None:
    import aip_init
    for i in plan.items:
        i.path.parent.mkdir(parents=True, exist_ok=True)
        i.path.write_text(render(i.meta, i.body), encoding="utf-8", newline="\n")
    for n in OLD_LAYOUT_FILES + ["OVERVIEW.md"]:
        p = project_living_path(repo, n)
        if p.exists():
            p.unlink()
    # 看板不再落盘：旧的手写看板在版本库里，连同版本库记录一起删
    subprocess.run(["git", "rm", "--cached", "-q", "--ignore-unmatch", f"{AIP_DIR}/OVERVIEW.md"],
                   cwd=repo, capture_output=True)
    aip_init.scaffold(repo, engine)


def report(repo: Path, plan: Plan, applied: bool, rewrite: bool, docs: dict[str, int]) -> None:
    print(("已迁移" if applied else "预览（没有写任何文件；确认后加 --apply）") + f"：共 {len(plan.items)} 条")
    for t in TYPES.values():
        mine = [i for i in plan.items if i.type == t.name]
        if not mine:
            continue
        counts = "、".join(f"{s} {sum(i.status == s for i in mine)}" for s in t.statuses if any(i.status == s for i in mine))
        print(f"  {t.folder}/：{len(mine)} 条（{counts}）")
        for i in mine[:3]:
            print(f"    {i.path.name}")
    if plan.unnamed:
        print(f"{len(plan.unnamed)} 条标题太长，简述是自动截的：--names-out <文件> 导出对照表，AI 起好名字后迁移加 --names <文件>")
    if plan.notes:
        print("要人看的地方：")
        for n in plan.notes:
            print(f"  - {n}")
    if docs:
        verb = "已改写" if applied else "会改写"
        shown = "、".join(f"{k}（{v} 处）" for k, v in list(docs.items())[:DOCS_SHOWN])
        more = f" 等 {len(docs)} 个文件" if len(docs) > DOCS_SHOWN else ""
        print(f".aip/ 说明文件里的旧编号和锚点{verb}成完整标识，共 {sum(docs.values())} 处：{shown}{more}")
    done, unknown = rewrite_anchors(repo, plan, write=applied and rewrite)
    if done or unknown:
        verb = "已改写" if applied and rewrite else "能自动改写"
        print(f"代码注释锚点 `.aip/knowledge.md::…`：{verb} {done} 处"
              + ("" if applied and rewrite else "（加 --rewrite-anchors 一起改）"))
        for key, files in unknown.items():
            print(f"  - 认不出 `{key}`（不是任何条目的 rule_id 或旧编号）：{'、'.join(dict.fromkeys(files))}")
    mentions = old_name_mentions(repo)
    if mentions:
        print("这些文件还在引用旧文件名（代码注释锚点、说明文件等），迁完改成新目录或条目标识：")
        for m in mentions:
            print(f"  - {m}")
    if applied:
        print("接下来：跑 aip_check.py 修掉报红的地方，按 reference/migrate.md 做收尾，然后一次提交。")


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="Migrate a pre-0.5.0 .aip/ to one-file-per-item.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--apply", action="store_true", help="真的写文件（默认只预览）")
    ap.add_argument("--rewrite-anchors", action="store_true",
                    help="连同 .aip/ 以外代码注释里的 `.aip/knowledge.md::<rule_id 或旧编号>` 一起改成新标识")
    ap.add_argument("--allow-dirty", action="store_true", help=".aip/ 有未提交改动也照样迁（回退时要小心）")
    ap.add_argument("--names-out", help="把标题太长、简述要另起的条目导出成对照表（不迁移）")
    ap.add_argument("--names", help="读回填好的简述对照表")
    ap.add_argument("--engine-root", default=str(Path(__file__).resolve().parents[1]))
    a = ap.parse_args()
    repo = Path(a.repo_root).resolve()
    if not any(project_living_path(repo, n).exists() for n in OLD_LAYOUT_FILES):
        print("没有旧格式的文件（knowledge.md / decisions.md / inbox.md），不用迁移。")
        return 0
    if item_files(repo):
        print("条目目录里已经有条目了：像是迁过一半。先把 .aip/ 恢复到迁移前（git checkout -- .aip），再重跑。")
        return 1
    if a.apply and aip_dirty(repo) and not a.allow_dirty:
        print(".aip/ 有未提交的改动：先提交或确认后加 --allow-dirty。迁移前干净，出问题才能一条命令退回去。")
        return 1
    plan = build_plan(repo, read_names(Path(a.names)) if a.names else None)
    if a.names_out:
        write_names(Path(a.names_out), plan)
        print(f"已导出 {len(plan.unnamed)} 条到 {a.names_out}：填第三列，再加 --names {a.names_out} 迁移")
        return 0
    if a.apply:
        apply(repo, plan, Path(a.engine_root).resolve())
    docs = rewrite_docs(repo, plan, write=a.apply)
    report(repo, plan, a.apply, a.rewrite_anchors, docs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
