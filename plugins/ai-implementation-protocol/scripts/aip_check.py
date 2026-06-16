from __future__ import annotations

import argparse
from pathlib import Path

from _aip_common import (
    PROJECT_LIVING_FILES,
    REQUIRED_FEATURE_FILES,
    aip_root,
    current_task_path,
    feature_dir,
    project_living_path,
    read_json,
    read_text,
)


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


def unclassified_findings(findings_text: str) -> int:
    """统计未分类的侧发现条目。真实条目状态行含 '待分类' 且不含 '|'（'|' 是模板里的菜单行）。"""
    count = 0
    for line in findings_text.splitlines():
        s = line.strip()
        if s.startswith("- 发现") and "待分类" in s and "|" not in s:
            count += 1
    return count


def gate_problems(verification_text: str) -> list[str]:
    """验收完成时，机器闸门必须有真实证据：有 Machine Gates 段、无 fail 行。"""
    problems: list[str] = []
    if "## Machine Gates" not in verification_text:
        problems.append("verification.md missing '## Machine Gates' section")
    if "| fail |" in verification_text:
        problems.append("verification.md has a gate with result 'fail'")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AIP handoff completeness and real-evidence gates.")
    parser.add_argument("--repo-root", required=True, help="Target project root.")
    args = parser.parse_args()

    target_repo = Path(args.repo_root).resolve()
    errors: list[str] = []

    # 项目级活文档（始终校验存在；init 应已生成）。
    if not aip_root(target_repo).exists():
        errors.append(f"Missing AIP directory: {aip_root(target_repo)} (run `aip init`)")
    else:
        for name in PROJECT_LIVING_FILES:
            if not project_living_path(target_repo, name).exists():
                errors.append(f"Missing project living doc: {project_living_path(target_repo, name)}")

        # 侧发现闸门：findings.md 不得留未分类条目。
        findings = project_living_path(target_repo, "findings.md")
        if findings.exists():
            n = unclassified_findings(read_text(findings))
            if n:
                errors.append(f"findings.md has {n} unclassified (待分类) side-finding(s) — classify before completion")

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

                verification = fd / "verification.md"
                if current_task.get("status") == "done":
                    if not verification.exists():
                        errors.append("feature marked done but verification.md is missing")
                    else:
                        errors.extend(gate_problems(read_text(verification)))

    if errors:
        print("AIP check failed:")
        for item in errors:
            print(f"- {item}")
        return 1

    print("AIP check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
