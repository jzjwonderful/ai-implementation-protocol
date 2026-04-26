from __future__ import annotations

import argparse
from pathlib import Path

from _aip_common import REQUIRED_FEATURE_FILES, current_task_path, feature_dir, read_json, read_text


def count_in_progress(task_board_text: str) -> int:
    count = 0
    for line in task_board_text.splitlines():
        if line.strip().startswith("status:") and "in_progress" in line:
            count += 1
    return count


def contains_required_handoff_sections(handoff_text: str) -> list[str]:
    required = [
        "## Current Phase",
        "## Current Task",
        "## Completed Work",
        "## Remaining Work",
        "## Blockers",
        "## Next Action",
        "## Files Touched",
        "## Verification Status",
    ]
    return [item for item in required if item not in handoff_text]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AIP handoff completeness.")
    parser.add_argument("--repo-root", required=True, help="Target project root.")
    args = parser.parse_args()

    target_repo = Path(args.repo_root).resolve()
    errors: list[str] = []

    task_path = current_task_path(target_repo)
    if not task_path.exists():
        errors.append(f"Missing runtime pointer: {task_path}")
    else:
        current_task = read_json(task_path)
        fid = current_task.get("feature_id", "")
        if not fid:
            errors.append("current_task.json has empty feature_id")
            fid = ""
        if fid:
            fd = feature_dir(target_repo, fid)
            if not fd.exists():
                errors.append(f"Missing feature directory: {fd}")
            else:
                for name in REQUIRED_FEATURE_FILES:
                    if not (fd / name).exists():
                        errors.append(f"Missing feature file: {fd / name}")

                handoff = fd / "handoff.md"
                if handoff.exists():
                    missing_sections = contains_required_handoff_sections(read_text(handoff))
                    for section in missing_sections:
                        errors.append(f"handoff.md missing section: {section}")

                task_board = fd / "task_board.yaml"
                if task_board.exists():
                    in_progress_count = count_in_progress(read_text(task_board))
                    if in_progress_count > 1:
                        errors.append("task_board.yaml has more than one in_progress task")

                if current_task.get("status") == "done" and not (fd / "verification.md").exists():
                    errors.append("feature marked done but verification.md is missing")

    if errors:
        print("AIP check failed:")
        for item in errors:
            print(f"- {item}")
        return 1

    print("AIP check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
