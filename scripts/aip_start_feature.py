from __future__ import annotations

import argparse
from pathlib import Path

from _aip_common import current_task_path, feature_dir, iso_now, write_json, write_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new AIP feature work package.")
    parser.add_argument("--repo-root", required=True, help="Target project root.")
    parser.add_argument("--feature-id", required=True, help="Feature directory id.")
    parser.add_argument("--title", default="", help="Optional human-readable title.")
    parser.add_argument(
        "--template-root",
        default=Path(__file__).resolve().parents[1],
        help="AIP repository root. Defaults to this script's repository.",
    )
    args = parser.parse_args()

    target_repo = Path(args.repo_root).resolve()
    template_root = Path(args.template_root).resolve()
    out_dir = feature_dir(target_repo, args.feature_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    template_map = {
        "spec.md": "feature-spec-template.md",
        "plan.md": "feature-plan-template.md",
        "handoff.md": "handoff-template.md",
        "verification.md": "verification-template.md",
        "task_board.yaml": "task-board-template.yaml",
        "file_scope.yaml": "file-scope-template.yaml",
    }
    for out_name, tpl_name in template_map.items():
        content = (template_root / "templates" / tpl_name).read_text(encoding="utf-8")
        write_text(out_dir / out_name, content)

    session_log = f"# Session Log\n\n- {iso_now()} feature created: {args.feature_id}\n"
    write_text(out_dir / "session_log.md", session_log)
    write_text(out_dir / "decisions.md", "# Decisions\n\n")

    current_task = {
        "feature_id": args.feature_id,
        "status": "planned",
        "current_phase": "spec",
        "current_task": args.title or f"Write spec for {args.feature_id}",
        "next_action": "Review and complete spec.md before implementation.",
        "last_updated": iso_now(),
        "owner": "ai",
        "blocking": [],
        "must_read": [
            "project_docs/protocols/ai-implementation-protocol.md",
            f"project_docs/features/{args.feature_id}/spec.md",
            f"project_docs/features/{args.feature_id}/handoff.md"
        ]
    }
    write_json(current_task_path(target_repo), current_task)

    print(f"Feature initialized: {args.feature_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
