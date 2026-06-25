from __future__ import annotations
import argparse
from pathlib import Path
from _aip_common import PROJECT_LIVING_FILES, project_living_path, read_text
from aip_knowledge import expected_index_text

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

def run_all(repo: Path) -> list[str]:
    return check_living_files(repo) + check_index_sync(repo)

def main() -> int:
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
