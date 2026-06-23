from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from _aip_common import current_task_path, iso_now, read_json, write_json

SCRIPT_DIR = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Mark the active AIP feature done (gated by aip check).")
    parser.add_argument("--repo-root", required=True, help="Target project root.")
    parser.add_argument("--resolution", choices=["fixed", "wont_fix", "by_design"], default=None,
                        help="Bug 收尾结论（kind=bug 必填）。")
    args = parser.parse_args()

    target_repo = Path(args.repo_root).resolve()
    ct_path = current_task_path(target_repo)
    if not ct_path.exists():
        print("AIP 未初始化。请先运行 `$aip init`。")
        return 1

    current_task = read_json(ct_path)
    if current_task.get("kind", "feature") == "bug":
        resolution = args.resolution or current_task.get("resolution")
        if resolution not in ("fixed", "wont_fix", "by_design"):
            print("bug 收尾需指定 resolution：`$aip done --resolution fixed|wont_fix|by_design`。")
            return 1
        current_task["resolution"] = resolution

    prev_status = current_task.get("status", "in_progress")
    current_task["status"] = "done"
    current_task["last_updated"] = iso_now()
    write_json(ct_path, current_task)

    check = subprocess.call([sys.executable, str(SCRIPT_DIR / "aip_check.py"), "--repo-root", str(target_repo)])
    if check != 0:
        current_task["status"] = prev_status
        current_task["last_updated"] = iso_now()
        write_json(ct_path, current_task)
        print(f"完成闸门未通过；status 已回滚为 '{prev_status}'。修复上面的问题后重试 `$aip done`。")
        return 1

    print("Feature marked done; AIP check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
