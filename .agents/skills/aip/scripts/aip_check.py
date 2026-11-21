from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from _aip_common import (
    FORBIDDEN_SLOT_FILENAMES, OLD_LAYOUT_FILES, OLD_REFERENCE_FILE, PROJECT_FILES, SCAN_PRUNE_DIRS, TOPIC_DIR,
    WIDER_CHECK_VERSION, aip_root, aip_version, force_utf8, project_living_path, py_cmd, read_text, split_layout,
)
from aip_item import SUPERSEDABLE, TYPES, Item, item_files, parse_name, read_item, type_dir
from aip_lookup import ANCHOR, READ_WHEN_LIMIT, list_topics, topic_dir
from aip_size import MUST_READ_FILE, over_limits, project_skill_files, size_check_paths
from aip_upkeep import parse_day, reminders

STAMP_PREFIX = re.compile(r"^\d{8}-\d{6}_")
MIGRATE_HINT = "跑 aip 技能的 scripts/aip_migrate.py 迁移（做法见 reference/migrate.md）"

# 0.8.0 起才有的目录：没整理过的仓库不要求（整理前一查就红，提交都过不去）
SPLIT_ONLY_DIRS = {"reuse"}

def check_project_files(repo: Path) -> list[str]:
    split = split_layout(repo)
    out = [f"缺失文档: .aip/{n}" for n in PROJECT_FILES if not project_living_path(repo, n).exists()]
    out += [f"缺失条目目录: .aip/{t.folder}/" for t in TYPES.values()
            if not type_dir(repo, t.name).is_dir() and (split or t.name not in SPLIT_ONLY_DIRS)]
    if split and not topic_dir(repo).is_dir():
        out.append(f"缺失主题目录: .aip/{TOPIC_DIR}/")
    if split and project_living_path(repo, OLD_REFERENCE_FILE).exists():
        out.append(f".aip/{OLD_REFERENCE_FILE} 应该已经拆成 .aip/{TOPIC_DIR}/ 下的主题文件"
                   "（可复用实现改成 reuse 条目）：拆完删掉它，做法见 aip 技能 reference/upgrade.md 的 0.8.0")
    return out

def check_old_layout(repo: Path) -> list[str]:
    return [f"还是旧格式（.aip/{n}）：{MIGRATE_HINT}" for n in OLD_LAYOUT_FILES
            if project_living_path(repo, n).exists()]

def check_item_names(repo: Path) -> list[str]:
    out = []
    for t in TYPES.values():
        for path in item_files(repo, t.name):
            parsed = parse_name(path.name)
            rel = path.relative_to(repo).as_posix()
            if not parsed:
                out.append(f"文件名不合格式（要 时间戳_类型_状态_简述.md，时间戳如 20260928-153012）: {rel}")
            elif parsed[1] != t.name:
                out.append(f"文件名里的类型「{parsed[1]}」和所在目录 {t.folder}/ 不符: {rel}")
            elif parsed[2] in t.remove_on:
                out.append(f"做完的在建线不留文件，删掉（过程在 git 里）: {rel}")
            elif parsed[2] not in t.statuses:
                out.append(f"状态「{parsed[2]}」不对，{t.name} 只能是 {' / '.join(t.statuses)}: {rel}")
    return out

def _body_has(body: str, section: str) -> bool:
    # 小节写成「- 症状: 内容」或「## 症状」下面有内容都算；模板里的 <占位> 不算
    for m in re.finditer(rf"^(?:- {section}\s*[:：](.*)|#+\s*{section}\s*$)", body, re.M):
        if m.group(1) is None or (m.group(1).strip() and not m.group(1).strip().startswith("<")):
            return True
    return False

def _valid_items(repo: Path) -> list[Item]:
    items = [read_item(p) for p in item_files(repo)]
    return [i for i in items if i and i.type in TYPES and i.status in TYPES[i.type].statuses]

def check_items(repo: Path) -> list[str]:
    items = _valid_items(repo)
    ids = {i.id for i in items}
    out = []
    seen: dict[str, str] = {}
    for i in items:
        rel = i.path.relative_to(repo).as_posix()
        if i.id in seen:
            out.append(f"标识重复 {i.id}：{seen[i.id]} 和 {rel}（合并时两边改了同一条的状态？留一个）")
        seen[i.id] = rel
        kind = TYPES[i.type]
        for key in ("title", "status") + kind.required:
            if not i.meta.get(key):
                out.append(f"{rel} 文件头缺 {key}")
        if i.meta.get("status") and i.meta["status"] != i.status:
            out.append(f"{rel} 文件名里的状态是 {i.status}，文件头写的是 {i.meta['status']}（改状态要用 aip_item.py status）")
        if i.type == "knowledge" and i.meta.get("last_reviewed") and parse_day(i.meta["last_reviewed"]) is None:
            out.append(f"{rel} 的 last_reviewed「{i.meta['last_reviewed']}」不是 YYYY-MM-DD 日期")
        for section in kind.body_required:
            if not _body_has(i.body, section):
                out.append(f"{rel} 正文没写「{section}」")
        if i.type in SUPERSEDABLE and i.status == "superseded" and not i.meta.get("superseded_by"):
            out.append(f"{rel} 标了 superseded，文件头缺 superseded_by（被哪一条取代）")
        # related 只能写条目；superseded_by 也可以是一句话（被某个机制取代），像条目标识的才要对得上
        refs = i.values("related") + [s for s in [i.meta.get("superseded_by", "")] if STAMP_PREFIX.match(s)]
        for ref in refs:
            if ref not in ids:
                out.append(f"{rel} 引用了不存在的条目「{ref}」（要写完整的「时间戳_简述」）")
    return out

def check_no_orphan_slots(repo: Path) -> list[str]:
    # 迁移守卫只扫 .aip/——旧机制的残留都落在这里。项目自带的同名文件
    # （如根目录 STATUS.md、src/report.md）不归 AIP 管，扫全仓会大量误报。
    out = []
    root = aip_root(repo)
    if not root.is_dir():
        return out
    for path in root.rglob("*"):
        if not path.is_file() or any(p in SCAN_PRUNE_DIRS for p in path.parts):
            continue
        if path.name in FORBIDDEN_SLOT_FILENAMES:
            out.append(f"发现旧机制残留/未迁移文件: {path.relative_to(repo)}")
    return out

def check_sizes(repo: Path) -> list[str]:
    return over_limits(repo)

def check_topics(repo: Path) -> list[str]:
    # 没写什么时候读，AI 判断不了相关不相关，只能全读一遍，拆分就白做了
    if not split_layout(repo):
        return []
    out = []
    for t in list_topics(repo):
        rel = t.path.relative_to(repo).as_posix()
        for key in ("title", "read_when"):
            if not t.meta.get(key):
                out.append(f"{rel} 文件头缺 {key}（read_when 写什么时候该读，比如「改安装器或环境变量时」）")
        if len(t.read_when) > READ_WHEN_LIMIT:
            out.append(f"{rel} 的 read_when 有 {len(t.read_when)} 字（上限 {READ_WHEN_LIMIT}）：一句话说清什么时候读")
    return out

# ---------- 引用：拆分以后「见某文件某节」最容易断 ----------
AIP_PATH_REF = re.compile(r"\.aip/[^\s`'\"<>()（）\[\]「」，。；、*]+?\.md")
# 「conventions.md「铁律」」「.aip/reference/环境变量.md 的「代理」」这种写法
SECTION_REF = re.compile(r"((?:\.aip/)?(?:[^\s`'\"<>()（）\[\]「」/，。；、]+/)?[^\s`'\"<>()（）\[\]「」/，。；、]+\.md)`?\s*(?:的|里的|中的)?「([^」]+)」")

# 「本文「某节」」：拆分后最容易悄悄失效的文件内指针。「本文的「X」」常只是个说法（「和本文的「邀请加入」
# 是两回事」），带「的」时要后面跟着「一节」「小节」这类字才算指针。
SELF_REF = re.compile(r"本文(?:\s*「([^」]+)」|\s*(?:的|里的|中的)「([^」]+)」\s*(?:这|那)?一?(?:小节|章节|节|章))")

def link_sources(repo: Path) -> tuple[list[Path], list[Path]]:
    """查引用的文件，分两类返回：(AI 照着走的, 记录类文档)。

    照着走的：每次读的、按需读的、还在用的条目；0.8.1 起加项目自己的技能。里面的引用全查。
    记录类：0.8.1 起加的 .aip/ 下条目以外的文档（如 specs/）、size_check_paths 列的文档。规格和设计记录里
    「当时改了 .aip/reference.md」这种历史写法很常见，只提到一个路径不算错；只查条目锚点和「某文件「某节」」
    这类让人跳过去读的指针。
    不查的：决策和作废的条目是历史记录；旁路问题本来就在记「哪里还指着旧东西」，提到旧路径不算错。
    """
    root = aip_root(repo)
    if not root.is_dir():
        return [], []
    follow = [project_living_path(repo, MUST_READ_FILE)] + [t.path for t in list_topics(repo)]
    follow += [repo / n for n in ("CLAUDE.md", "AGENTS.md")]
    for i in _valid_items(repo):
        if i.type not in ("decision", "inbox") and i.status not in ("superseded", "fixed"):
            follow.append(i.path)
    records: list[Path] = []
    if aip_version(repo) >= WIDER_CHECK_VERSION:
        follow += project_skill_files(repo, "**/*.md")
        folders = {t.folder for t in TYPES.values()}
        records += [p for p in root.rglob("*.md") if p.relative_to(root).parts[0] not in folders]
        for pattern in size_check_paths(repo):
            records += [p for p in repo.glob(pattern) if p.suffix == ".md"]
    follow_set = {p for p in follow if p.is_file()}
    return sorted(follow_set), sorted({p for p in records if p.is_file()} - follow_set)

def _headings(path: Path) -> list[str]:
    return [l.lstrip("#").strip() for l in read_text(path).splitlines() if l.startswith("#")]

def check_links(repo: Path) -> list[str]:
    if not split_layout(repo):
        return []
    root = aip_root(repo)
    ids = {i.id for i in _valid_items(repo)} | {i.path.stem for i in _valid_items(repo)}
    out = []
    follow, records = link_sources(repo)
    for src in follow + records:
        rel = src.relative_to(repo).as_posix()
        text = read_text(src)
        for m in ANCHOR.finditer(text):
            ref = m.group(2).removesuffix(".md")
            if ref not in ids:
                out.append(f"{rel} 引用的条目「{m.group(0)}」不存在（要写完整的「时间戳_简述」）")
        for ref in dict.fromkeys(AIP_PATH_REF.findall(text)) if src in follow else ():
            if ANCHOR.match(ref):
                continue
            if not (repo / ref).is_file():
                out.append(f"{rel} 引用的 {ref} 不存在")
        own = _headings(src)
        for heading in (a or b for a, b in SELF_REF.findall(text)):
            if not any(heading in h for h in own):
                out.append(f"{rel} 里写的「本文「{heading}」」找不到这一节（拆分或改标题后没跟着改）")
        for name, heading in SECTION_REF.findall(text):
            target = repo / name if name.startswith(".aip/") else root / name
            if not target.is_file():
                if name.removeprefix(".aip/") == OLD_REFERENCE_FILE:
                    out.append(f"{rel} 引用了 {OLD_REFERENCE_FILE}「{heading}」，它已拆成 .aip/{TOPIC_DIR}/ 下的主题文件：改成对应的主题文件")
                elif name.startswith(".aip/"):
                    out.append(f"{rel} 引用的 {name} 不存在")
                continue  # 不在 .aip/ 下的文件（项目自己的 README 之类）不归这里管
            if not any(heading in h for h in _headings(target)):
                out.append(f"{rel} 引用的 {name}「{heading}」找不到这一节（标题改了或挪走了）")
    return list(dict.fromkeys(out))

ENGINE_PKG = "plugins/ai-implementation-protocol"
ENGINE_MANIFESTS = [".claude-plugin/plugin.json", ".codex-plugin/plugin.json",
                    ".grok-plugin/plugin.json"]

def check_engine_versions(repo: Path) -> list[str]:
    # 只对 AIP 引擎自身仓库有意义：技能目录里的 VERSION 是唯一版本源，
    # 各端 plugin.json 的 version 必须与它一致（历史上这里漂过 0.2.0/0.2.1）。
    pkg = repo / ENGINE_PKG
    if not pkg.is_dir():
        return []
    ver_file = pkg / "skills" / "aip" / "VERSION"
    if not ver_file.is_file():
        return [f"引擎版本文件缺失: {ENGINE_PKG}/skills/aip/VERSION"]
    ver = ver_file.read_text(encoding="utf-8").strip()
    out = []
    for manifest in ENGINE_MANIFESTS:
        path = pkg / manifest
        if not path.is_file():
            out.append(f"插件清单缺失: {ENGINE_PKG}/{manifest}")
            continue
        got = json.loads(path.read_text(encoding="utf-8")).get("version")
        if got != ver:
            out.append(f"版本不一致: {manifest} 写的是 {got!r}，VERSION 是 {ver!r}")
    return out

# 引擎仓库自己也按项目级装了一份（拷贝，不用链接：Windows 上 git 链接要额外设置）。
# 改了引擎源忘了重装，本仓库会话里用的就是旧引擎，所以逐个文件比内容。
# SOURCE.json 是安装记录、缓存是运行产物，不算。
# 装进本仓库的引擎副本。Codex 文档里仓库技能在 .agents/skills（从当前目录找到仓库根）；
# .codex/skills 是早先的写法，某些版本还认，仓库里还有就一起保持同步。
ENGINE_COPIES = [".claude/skills/aip", ".agents/skills/aip", ".codex/skills/aip"]
COPY_SKIP_NAMES = {"SOURCE.json"}

def _skill_files(root: Path) -> dict[str, Path]:
    return {p.relative_to(root).as_posix(): p for p in root.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc" and p.name not in COPY_SKIP_NAMES}

def check_engine_copies(repo: Path) -> list[str]:
    src = repo / ENGINE_PKG / "skills" / "aip"
    if not src.is_dir():
        return []
    want = _skill_files(src)
    out = []
    for rel in ENGINE_COPIES:
        copy = repo / rel
        if not copy.is_dir():
            continue
        have = _skill_files(copy)
        diff = sorted(k for k in want.keys() | have.keys()
                      if k not in want or k not in have or want[k].read_bytes() != have[k].read_bytes())
        if diff:
            out.append(f"本仓库装的 {rel} 和引擎源不一致（{len(diff)} 个文件，如 {diff[0]}）："
                       f"改完引擎要重装：{py_cmd()} scripts/install_all.py --project .")
    return out

def run_all(repo: Path) -> list[str]:
    old = check_old_layout(repo)
    if old:  # 旧格式下其余检查全是噪音，先迁移
        return old + check_engine_versions(repo)
    return (check_project_files(repo) + check_item_names(repo) + check_items(repo)
            + check_topics(repo) + check_sizes(repo) + check_links(repo)
            + check_no_orphan_slots(repo) + check_engine_versions(repo) + check_engine_copies(repo)
            )

def main() -> int:
    force_utf8()
    p = argparse.ArgumentParser(description="AIP hygiene gate.")
    p.add_argument("--repo-root", required=True)
    p.add_argument("--no-reminders", action="store_true",
                   help="不算到期提醒（pre-commit 用：提醒不挡提交，算它要跑 git，白白拖慢每次提交）")
    a = p.parse_args()
    repo = Path(a.repo_root).resolve()
    viol = run_all(repo)
    if viol:
        print("aip check 未通过：")
        for v in viol: print(f"  - {v}")
    else:
        print("aip check 通过")
    if not a.no_reminders and not check_old_layout(repo) and aip_root(repo).is_dir():
        due = reminders(repo)
        if due:
            print("到期提醒（不挡提交）：")
            for d in due: print(f"  - {d}")
    return 1 if viol else 0

if __name__ == "__main__":
    raise SystemExit(main())
