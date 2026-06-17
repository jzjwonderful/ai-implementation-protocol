from __future__ import annotations

import argparse
from pathlib import Path

from _aip_common import AIP_DIR, current_task_path, feature_dir, iso_now, write_json, write_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new AIP bug work package (light track).")
    parser.add_argument("--repo-root", required=True, help="Target project root.")
    parser.add_argument("--bug-id", required=True, help="Bug directory id.")
    parser.add_argument("--title", default="", help="Optional human-readable title.")
    parser.add_argument(
        "--template-root",
        default=Path(__file__).resolve().parents[1],
        help="AIP repository root. Defaults to this script's repository.",
    )
    args = parser.parse_args()

    target_repo = Path(args.repo_root).resolve()
    template_root = Path(args.template_root).resolve()
    out_dir = feature_dir(target_repo, args.bug_id)
    if out_dir.exists():
        print(f"Refusing to overwrite existing work package: {out_dir}")
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)

    template_map = {
        "report.md": "bug-report-template.md",
        "handoff.md": "handoff-template.md",
        "verification.md": "bug-verification-template.md",
        "file_scope.yaml": "file-scope-template.yaml",
    }
    for out_name, tpl_name in template_map.items():
        content = (template_root / "templates" / tpl_name).read_text(encoding="utf-8")
        write_text(out_dir / out_name, content)

    write_text(out_dir / "session_log.md", f"# Session Log\n\n- {iso_now()} bug created: {args.bug_id}\n")
    write_text(out_dir / "decisions.md", "# Decisions\n\n")

    current_task = {
        "kind": "bug",
        "feature_id": args.bug_id,
        "status": "planned",
        "current_phase": "investigate",
        "current_task": args.title or f"Investigate bug {args.bug_id}",
        "resolution": None,
        "next_action": "Run root-cause investigation; fill report.md before any fix.",
        "last_updated": iso_now(),
        "owner": "ai",
        "blocking": [],
        "must_read": [
            f"{AIP_DIR}/protocols/ai-implementation-protocol.md",
            f"{AIP_DIR}/STATUS.md",
            f"{AIP_DIR}/knowledge_index.md",
            f"{AIP_DIR}/features/{args.bug_id}/report.md",
            f"{AIP_DIR}/features/{args.bug_id}/handoff.md",
        ],
    }
    write_json(current_task_path(target_repo), current_task)

    print(f"Bug package initialized: {args.bug_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
