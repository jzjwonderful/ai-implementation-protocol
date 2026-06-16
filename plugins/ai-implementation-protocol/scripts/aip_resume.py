from __future__ import annotations

import argparse
from pathlib import Path

from _aip_common import current_task_path, feature_dir, read_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Print an AIP resume summary.")
    parser.add_argument("--repo-root", required=True, help="Target project root.")
    args = parser.parse_args()

    target_repo = Path(args.repo_root).resolve()
    ct_path = current_task_path(target_repo)
    if not ct_path.exists():
        print("AIP 未初始化（缺 .aip/_runtime/current_task.json）。请先运行 `$aip init`。")
        return 1
    current_task = read_json(ct_path)
    fid = current_task.get("feature_id", "")

    print(f"当前功能: {fid or '(none)'}")
    print(f"状态: {current_task.get('status', '')}")
    print(f"阶段: {current_task.get('current_phase', '')}")
    print(f"当前任务: {current_task.get('current_task', '')}")
    print(f"下一步: {current_task.get('next_action', '')}")

    blockers = current_task.get("blocking", [])
    print("阻塞:")
    if blockers:
        for item in blockers:
            print(f"- {item}")
    else:
        print("- 无")

    print("必须先阅读:")
    for idx, item in enumerate(current_task.get("must_read", []), start=1):
        print(f"{idx}. {item}")

    if fid:
        fd = feature_dir(target_repo, fid)
        print(f"功能目录: {fd}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
