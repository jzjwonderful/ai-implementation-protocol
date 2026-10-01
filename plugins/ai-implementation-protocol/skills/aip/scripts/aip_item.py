from __future__ import annotations

"""条目：知识、决策、旁路问题、在建线，一条一个文件。

文件名 `<时间戳>_<类型>_<状态>_<简述>.md`，比如
`20260928-153012_knowledge_active_gbrain健康分是扣分制.md`。时间戳是创建时间，精确到秒；
同一秒建的两条靠简述区分。

- 条目的标识是「时间戳_简述」。状态会变、标识不变，所以引用别的条目一律写完整标识，
  不只写时间戳（光看时间戳谁也不知道指的是什么），也不带状态（一改状态引用就断）。
- 状态在文件名和文件头里各写一份：文件名方便按状态筛和排序，打开文件也能直接看到。
  改状态走本脚本，两处一起改；aip_check 查两处是否一致。
- 并行分支各自新增条目是不同的文件，合并时不会冲突——这是不再按顺序发号的原因。
- 在建线做完就删文件，不留 done：线只写往前看的内容，做完没有可留的，过程在 git 里。
  收线放进这条线最后一个 MR：合入了线就没了，没合入主干上它还在，不用再单独提 MR 改状态。
"""

import argparse
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from _aip_common import aip_root, force_utf8, read_text, write_text

ENGINE_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ItemType:
    name: str
    folder: str
    statuses: tuple[str, ...]
    remove_on: tuple[str, ...] = ()     # 改成这些状态就是删掉文件
    required: tuple[str, ...] = ()      # 文件头必填（title、status 所有类型都要）
    body_required: tuple[str, ...] = ()  # 正文里必须写了内容的小节


TYPES: dict[str, ItemType] = {
    t.name: t for t in (
        ItemType("knowledge", "knowledge", ("active", "draft", "fixed", "superseded"),
                 required=("category", "scope", "last_reviewed"), body_required=("症状", "根因")),
        ItemType("decision", "decisions", ("accepted", "superseded")),
        ItemType("inbox", "inbox", ("open", "closed")),
        ItemType("track", "tracks", ("active", "blocked", "paused"), remove_on=("done",)),
    )
}
# 被取代的条目必须写明被谁取代
SUPERSEDABLE = ("knowledge", "decision")
DEFAULT_STATUS = {"knowledge": "draft", "decision": "accepted", "inbox": "open", "track": "active"}
# 多值字段用逗号分隔：related 写别的条目的标识，aliases 是迁移前的旧编号
HEAD_ORDER = ("title", "status", "category", "scope", "last_reviewed", "superseded_by",
              "rule_id", "aliases", "related")

STAMP_FORMAT = "%Y%m%d-%H%M%S"
NAME_RE = re.compile(r"^(\d{8}-\d{6})_([a-z]+)_([a-z]+)_(.+)\.md$")
SLUG_LIMIT = 24
# 按分句截出来的太短（只剩「注意」这种）就不如硬截
SLUG_CLAUSE_MIN = 8
# 分句的标点：兜底截断时优先在这里断，保住完整的分句
SLUG_CLAUSE = re.compile(r"[，,；;：:。！!？?]|——|—| - ")
# 括号里多是补充说明（日期、编号），不进简述
SLUG_PAREN = re.compile(r"（[^（）]*）|\([^()]*\)|【[^【】]*】|\[[^\[\]]*\]")
# Windows 文件名不认的字符、会破坏文件名结构的下划线、反引号、引号和标点都去掉
SLUG_DROP = re.compile(r"[\\/:：*?\"<>|`'“”‘’「」『』《》,，。.、;；!！?？#%&=+~^$@—–…·{}]")
FRONT = "---"


@dataclass
class Item:
    path: Path
    stamp: str
    type: str
    status: str
    slug: str
    meta: dict[str, str] = field(default_factory=dict)
    body: str = ""

    @property
    def id(self) -> str:
        return f"{self.stamp}_{self.slug}"

    @property
    def title(self) -> str:
        return self.meta.get("title") or self.slug

    @property
    def created(self) -> date:
        return datetime.strptime(self.stamp, STAMP_FORMAT).date()

    def values(self, key: str) -> list[str]:
        return [v.strip() for v in self.meta.get(key, "").split(",") if v.strip()]


# ---------- 文件名与文件头 ----------

def parse_name(name: str) -> tuple[str, str, str, str] | None:
    """文件名 → (时间戳, 类型, 状态, 简述)；不合格式返回 None。"""
    m = NAME_RE.match(name)
    if not m:
        return None
    try:
        datetime.strptime(m.group(1), STAMP_FORMAT)
    except ValueError:
        return None
    return m.group(1), m.group(2), m.group(3), m.group(4)


def file_name(stamp: str, type_name: str, status: str, slug: str) -> str:
    return f"{stamp}_{type_name}_{status}_{slug}.md"


def _clean(text: str) -> str:
    """去掉括号说明和文件名里不能有的字符。

    中文和英文之间的空格直接去掉（「MCP 工具」→「MCP工具」），两个英文词之间用连字符。
    """
    s = SLUG_DROP.sub("", SLUG_PAREN.sub("", text))
    s = re.sub(r"(?<=[A-Za-z0-9])[\s_-]+(?=[A-Za-z0-9])", "-", s)
    s = re.sub(r"[\s_]+", "", s)
    return re.sub(r"-{2,}", "-", s).strip("-")


def slug_is_cut(title: str, limit: int = SLUG_LIMIT) -> bool:
    """标题太长、直接当简述得截断：这时应该由写条目的人（AI）另起一个短名字。"""
    return len(_clean(title)) > limit


def _clause_cut(title: str, limit: int) -> str:
    """从头取尽量多的完整分句；取不出够长的就返回空。"""
    taken: list[str] = []
    best = ""
    for part in SLUG_CLAUSE.split(SLUG_PAREN.sub("", title)):
        taken.append(part)
        cand = _clean(" ".join(taken))
        if len(cand) > limit:
            break
        best = cand
    return best if len(best) >= SLUG_CLAUSE_MIN else ""


def _hard_cut(s: str, limit: int) -> str:
    """硬截，但不把英文单词切成半截。"""
    cut = s[:limit]
    if s[limit].isascii() and s[limit].isalnum() and cut[-1].isascii() and cut[-1].isalnum():
        cut = re.sub(r"[A-Za-z0-9]+$", "", cut)
    return cut.strip("-")


def slugify(title: str, limit: int = SLUG_LIMIT) -> str:
    """标题 → 文件名里的中文简述。

    简述最好由写条目的人起（说清这条是什么的短名字），这里是没起时的兜底：
    放得下就整句用；放不下先在分句标点处断开，保住完整的分句；还不行才硬截。
    """
    s = _clean(title)
    if len(s) > limit:
        s = _clause_cut(title, limit) or _hard_cut(s, limit)
    return s or "untitled"


def split_front(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONT:
        return {}, text
    meta: dict[str, str] = {}
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONT:
            return meta, "\n".join(lines[i + 1:]).lstrip("\n")
        key, sep, value = line.partition(":")
        if sep and key.strip():
            meta[key.strip()] = value.strip()
    return {}, text  # 没有收尾的 ---，整篇当正文


def render(meta: dict[str, str], body: str) -> str:
    keys = [k for k in HEAD_ORDER if meta.get(k)] + [k for k in meta if k not in HEAD_ORDER and meta[k]]
    head = "\n".join(f"{k}: {meta[k]}" for k in keys)
    return f"{FRONT}\n{head}\n{FRONT}\n\n{body.strip()}\n"


def read_item(path: Path) -> Item | None:
    parsed = parse_name(path.name)
    if not parsed:
        return None
    meta, body = split_front(read_text(path))
    stamp, type_name, status, slug = parsed
    return Item(path, stamp, type_name, status, slug, meta, body)


def save(item: Item) -> None:
    write_text(item.path, render(item.meta, item.body))


# ---------- 查找 ----------

def type_dir(repo: Path, type_name: str) -> Path:
    return aip_root(repo) / TYPES[type_name].folder


def item_files(repo: Path, type_name: str | None = None) -> list[Path]:
    names = [type_name] if type_name else list(TYPES)
    out: list[Path] = []
    for n in names:
        d = type_dir(repo, n)
        if d.is_dir():
            out.extend(sorted(p for p in d.iterdir() if p.is_file() and p.suffix == ".md"))
    return out


def list_items(repo: Path, type_name: str | None = None) -> list[Item]:
    items = [read_item(p) for p in item_files(repo, type_name)]
    return [i for i in items if i is not None]


def matches(item: Item, ref: str) -> bool:
    ref = ref.strip().strip("`")
    return ref in (item.id, item.path.name, item.path.stem) or ref in item.values("aliases")


def find(items: list[Item], ref: str) -> Item:
    """按完整标识、文件名或旧编号找条目。只写时间戳不算数。"""
    hits = [i for i in items if matches(i, ref)]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise LookupError(f"找不到条目「{ref}」（引用要写完整的「时间戳_简述」，或迁移前的旧编号）")
    raise LookupError(f"「{ref}」对应多条：" + "、".join(i.path.name for i in hits))


# ---------- 新建与修改 ----------

def load_body_template(type_name: str, engine: Path = ENGINE_ROOT) -> str:
    tpl = engine / "templates" / f"item-{type_name}.md"
    return read_text(tpl) if tpl.exists() else ""


def new_item(repo: Path, type_name: str, title: str, status: str | None = None, slug: str | None = None,
             meta: dict[str, str] | None = None, body: str | None = None, stamp: str | None = None,
             engine: Path = ENGINE_ROOT) -> Item:
    if type_name not in TYPES:
        raise ValueError(f"类型只能是 {' / '.join(TYPES)}")
    status = status or DEFAULT_STATUS[type_name]
    if status not in TYPES[type_name].statuses:
        raise ValueError(f"{type_name} 的状态只能是 {' / '.join(TYPES[type_name].statuses)}")
    stamp = stamp or datetime.now().strftime(STAMP_FORMAT)
    if slug and slug_is_cut(slug):
        raise ValueError(f"简述「{slug}」超过 {SLUG_LIMIT} 字：起一个更短的名字")
    slug = slugify(slug or title)
    all_meta = {"title": title, "status": status, **(meta or {})}
    if type_name == "knowledge":
        all_meta.setdefault("last_reviewed", date.today().isoformat())
    item = Item(type_dir(repo, type_name) / file_name(stamp, type_name, status, slug),
                stamp, type_name, status, slug, all_meta,
                body if body is not None else load_body_template(type_name, engine))
    if any(i.id == item.id for i in list_items(repo)):
        raise FileExistsError(f"已有条目 {item.id}：换个简述")
    save(item)
    return item


def set_status(repo: Path, ref: str, status: str, by: str | None = None) -> Item:
    """改状态；改成该类的 remove_on 状态（线做完）就删掉文件，返回的条目路径已不存在。"""
    items = list_items(repo)
    item = find(items, ref)
    kind = TYPES[item.type]
    if status in kind.remove_on:
        item.path.unlink()
        return item
    if status not in kind.statuses:
        raise ValueError(f"{item.type} 的状态只能是 {' / '.join(kind.statuses + kind.remove_on)}")
    if status == "superseded":
        if not by:
            raise ValueError("标 superseded 要用 --by 写明被哪一条取代（条目标识，或被某个机制取代时写一句话）")
        try:
            item.meta["superseded_by"] = find(items, by).id
        except LookupError:
            if re.match(r"^\d{8}-\d{6}", by.strip()):
                raise  # 看着像条目标识却找不到，多半是写错了
            item.meta["superseded_by"] = by.strip()
    old = item.path
    item.status = status
    item.meta["status"] = status
    item.path = old.with_name(file_name(item.stamp, item.type, status, item.slug))
    save(item)
    if old != item.path:
        old.unlink()
    return item


def search(items: list[Item], keyword: str) -> list[Item]:
    """按关键词筛：查标题、简述、分类、适用范围（分类和适用范围不在文件名里，光看文件名查不到）。"""
    k = keyword.lower()
    return [i for i in items
            if any(k in v.lower() for v in (i.title, i.slug, i.meta.get("category", ""), i.meta.get("scope", "")))]


def mark_reviewed(repo: Path, ref: str, day: date | None = None) -> Item:
    item = find(list_items(repo), ref)
    if item.type != "knowledge":
        raise ValueError("只有知识条目有「最后复核」")
    item.meta["last_reviewed"] = (day or date.today()).isoformat()
    save(item)
    return item


# ---------- 命令行 ----------

def _print_list(items: list[Item]) -> None:
    for i in items:
        extra = f"  复核 {i.meta.get('last_reviewed', '?')}" if i.type == "knowledge" else ""
        print(f"{i.id}  [{i.type}/{i.status}]  {i.title}{extra}")
    if not items:
        print("（没有符合条件的条目）")


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="新建、改状态、查找 .aip/ 下的条目（知识 / 决策 / 旁路问题 / 在建线）。")
    ap.add_argument("--repo-root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="新建条目，打印文件路径；正文按模板生成，之后直接编辑文件补内容")
    p.add_argument("--type", required=True, choices=list(TYPES))
    p.add_argument("--title", required=True, help="一句话标题（完整的，写进文件头）")
    p.add_argument("--slug", help=f"文件名里的简述：8–{SLUG_LIMIT} 字、说清这条是什么的短名字；"
                                  f"标题超过 {SLUG_LIMIT} 字时必填")
    p.add_argument("--status")
    p.add_argument("--category", help="知识条目的分类")
    p.add_argument("--scope", help="知识条目的适用范围")

    p = sub.add_parser("status", help="改状态（文件名和文件头一起改）；在建线改 done 就是删掉文件")
    p.add_argument("ref", help="完整的「时间戳_简述」、文件名或旧编号")
    p.add_argument("status")
    p.add_argument("--by", help="标 superseded 时写被哪一条取代")

    p = sub.add_parser("reviewed", help="知识条目重验过：最后复核改成今天")
    p.add_argument("ref")

    p = sub.add_parser("list", help="列条目")
    p.add_argument("--type", choices=list(TYPES))
    p.add_argument("--status", action="append", help="只列这些状态，可写多次")
    p.add_argument("--grep", help="关键词：在标题、简述、分类、适用范围里找，不分大小写")

    p = sub.add_parser("show", help="打印一条的路径和内容")
    p.add_argument("ref")

    a = ap.parse_args()
    repo = Path(a.repo_root).resolve()
    try:
        if a.cmd == "new":
            if not a.slug and slug_is_cut(a.title):
                print(f"aip item：标题超过 {SLUG_LIMIT} 字，用 --slug 起一个 8–{SLUG_LIMIT} 字、说清这条是什么的"
                      f"短名字（不要截半句）。自动截出来是「{slugify(a.title)}」，可以参考")
                return 1
            if a.type == "knowledge" and not (a.category and a.scope):
                print("aip item：知识条目要写 --category（分类）和 --scope（适用范围），不写 aip_check 过不去")
                return 1
            meta = {k: v for k, v in (("category", a.category), ("scope", a.scope)) if v}
            print(new_item(repo, a.type, a.title, a.status, a.slug, meta).path)
        elif a.cmd == "status":
            item = set_status(repo, a.ref, a.status, a.by)
            print(item.path if item.path.exists() else f"已删除 {item.path}（线做完了，过程在 git 里）")
        elif a.cmd == "reviewed":
            print(mark_reviewed(repo, a.ref).path)
        elif a.cmd == "list":
            items = [i for i in list_items(repo, a.type) if not a.status or i.status in a.status]
            if a.grep:
                items = search(items, a.grep)
            _print_list(items)
        elif a.cmd == "show":
            item = find(list_items(repo), a.ref)
            print(item.path)
            print(read_text(item.path))
    except (LookupError, ValueError, FileExistsError) as e:
        print(f"aip item：{e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
