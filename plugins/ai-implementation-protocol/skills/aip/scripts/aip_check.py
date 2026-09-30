from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path
from _aip_common import (
    FORBIDDEN_SLOT_FILENAMES, GENERATED_FILES, OLD_LAYOUT_FILES, PROJECT_FILES,
    SCAN_PRUNE_DIRS, aip_root, force_utf8, project_living_path,
)
from aip_item import SUPERSEDABLE, TYPES, Item, item_files, parse_name, read_item, type_dir
from aip_upkeep import parse_day, reminders

STAMP_PREFIX = re.compile(r"^\d{8}-\d{6}_")
MIGRATE_HINT = "跑 aip 技能的 scripts/aip_migrate.py 迁移（做法见 reference/migrate.md）"

def check_project_files(repo: Path) -> list[str]:
    out = [f"缺失文档: .aip/{n}" for n in PROJECT_FILES if not project_living_path(repo, n).exists()]
    out += [f"缺失条目目录: .aip/{t.folder}/" for t in TYPES.values() if not type_dir(repo, t.name).is_dir()]
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

def check_generated_untracked(repo: Path) -> list[str]:
    try:
        r = subprocess.run(["git", "ls-files", "--", *(f"{aip_root(repo).name}/{n}" for n in GENERATED_FILES)],
                           cwd=repo, capture_output=True, text=True, encoding="utf-8", timeout=20)
    except (OSError, subprocess.SubprocessError):
        return []
    if r.returncode != 0:
        return []
    return [f"现场生成的 {p} 进了仓库（并行分支合并会冲突）：git rm --cached {p}"
            for p in r.stdout.splitlines() if p]

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

def run_all(repo: Path) -> list[str]:
    old = check_old_layout(repo)
    if old:  # 旧格式下其余检查全是噪音，先迁移
        return old + check_engine_versions(repo)
    return (check_project_files(repo) + check_item_names(repo) + check_items(repo)
            + check_generated_untracked(repo) + check_no_orphan_slots(repo) + check_engine_versions(repo))

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
