from __future__ import annotations
import argparse
import json
from pathlib import Path
from _aip_common import (
    FORBIDDEN_SLOT_FILENAMES, PROJECT_LIVING_FILES, REQUIRED_KNOWLEDGE_FIELDS,
    SCAN_PRUNE_DIRS, aip_root, force_utf8, project_living_path, read_text,
)
from aip_knowledge import expected_index_text, parse_entries

def check_living_files(repo: Path) -> list[str]:
    return [f"缺失活文档: .aip/{n}" for n in PROJECT_LIVING_FILES
            if not project_living_path(repo, n).exists()]

def check_index_sync(repo: Path) -> list[str]:
    idx = project_living_path(repo, "knowledge_index.md")
    if not idx.exists():
        return ["缺失 knowledge_index.md（跑 aip knowledge 重建）"]
    if read_text(idx) != expected_index_text(repo):
        return ["knowledge_index.md 与 knowledge.md 不一致（跑 aip knowledge 重建）"]
    return []

def check_knowledge_fields(repo: Path) -> list[str]:
    kn = project_living_path(repo, "knowledge.md")
    if not kn.exists():
        return []
    out = []
    for e in parse_entries(read_text(kn)):
        for field in REQUIRED_KNOWLEDGE_FIELDS:
            if not e["fields"].get(field):
                out.append(f'知识条目 {e["id"]} 缺必填字段: {field}')
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

ENGINE_PKG = "plugins/ai-implementation-protocol"
ENGINE_MANIFESTS = [".claude-plugin/plugin.json", ".codex-plugin/plugin.json"]

def check_engine_versions(repo: Path) -> list[str]:
    # 只对 AIP 引擎自身仓库有意义：技能目录里的 VERSION 是唯一版本源，
    # 两份 plugin.json 的 version 必须与它一致（历史上这里漂过 0.2.0/0.2.1）。
    pkg = repo / ENGINE_PKG
    if not pkg.is_dir():
        return []
    ver_file = pkg / "skills" / "aip" / "VERSION"
    if not ver_file.is_file():
        return [f"引擎版本文件缺失: {ENGINE_PKG}/skills/aip/VERSION"]
    ver = read_text(ver_file).strip()
    out = []
    for manifest in ENGINE_MANIFESTS:
        path = pkg / manifest
        if not path.is_file():
            out.append(f"插件清单缺失: {ENGINE_PKG}/{manifest}")
            continue
        got = json.loads(read_text(path)).get("version")
        if got != ver:
            out.append(f"版本不一致: {manifest} 写的是 {got!r}，VERSION 是 {ver!r}")
    return out

def run_all(repo: Path) -> list[str]:
    return check_living_files(repo) + check_index_sync(repo) + check_knowledge_fields(repo) + check_no_orphan_slots(repo) + check_engine_versions(repo)

def main() -> int:
    force_utf8()
    p = argparse.ArgumentParser(description="AIP hygiene gate.")
    p.add_argument("--repo-root", required=True)
    viol = run_all(Path(p.parse_args().repo_root).resolve())
    if viol:
        print("aip check 未通过：")
        for v in viol: print(f"  - {v}")
        return 1
    print("aip check 通过"); return 0

if __name__ == "__main__":
    raise SystemExit(main())
