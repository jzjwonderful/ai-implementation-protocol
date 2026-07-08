from __future__ import annotations
import argparse
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

PLUGIN_ROOT = "plugins/ai-implementation-protocol"

def check_dual_copy(repo: Path) -> list[str]:
    # 镜像比对只对 AIP 引擎自身仓库有意义。消费方项目没有这个插件包，
    # 否则项目自带的 scripts/、templates/ 会被逐个误判成"副本缺失"。
    # 比对实现只有一份，在 sync_plugin.drift（覆盖全部同步目录 + VERSION）。
    if not (repo / PLUGIN_ROOT).is_dir():
        return []
    import sync_plugin
    return [f"plugins {v}（跑 sync_plugin.py）" for v in sync_plugin.drift(repo)]

def run_all(repo: Path) -> list[str]:
    return check_living_files(repo) + check_index_sync(repo) + check_knowledge_fields(repo) + check_no_orphan_slots(repo) + check_dual_copy(repo)

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
