from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE_ROOT = SCRIPT_DIR.parent


def run_script(script_name: str, args: list[str]) -> int:
    cmd = [sys.executable, str(SCRIPT_DIR / script_name), *args]
    return subprocess.call(cmd)


def add_repo_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", default=".", help="Target repository root. Defaults to the current directory.")


def main() -> int:
    parser = argparse.ArgumentParser(description="AIP command router.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize AIP in a target repository.")
    add_repo_root(init_parser)
    init_parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT), help="AIP template root.")

    start_parser = subparsers.add_parser("start", help="Create a new AIP feature work package.")
    add_repo_root(start_parser)
    start_parser.add_argument("feature_id", nargs="?", help="Feature directory id.")
    start_parser.add_argument("--feature-id", dest="feature_id_flag", help="Feature directory id.")
    start_parser.add_argument("--title", default="", help="Optional human-readable title.")
    start_parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT), help="AIP template root.")

    bug_parser = subparsers.add_parser("bug", help="Create a new AIP bug work package (light track).")
    add_repo_root(bug_parser)
    bug_parser.add_argument("bug_id", nargs="?", help="Bug directory id.")
    bug_parser.add_argument("--bug-id", dest="bug_id_flag", help="Bug directory id.")
    bug_parser.add_argument("--title", default="", help="Optional human-readable title.")
    bug_parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT), help="AIP template root.")

    resume_parser = subparsers.add_parser("resume", help="Print the current AIP resume summary.")
    add_repo_root(resume_parser)

    check_parser = subparsers.add_parser("check", help="Validate AIP handoff completeness.")
    add_repo_root(check_parser)

    knowledge_parser = subparsers.add_parser("knowledge", help="Rebuild the knowledge index from knowledge.md.")
    add_repo_root(knowledge_parser)

    done_parser = subparsers.add_parser("done", help="Mark the active feature done (runs aip check; rolls back on fail).")
    add_repo_root(done_parser)
    done_parser.add_argument("--resolution", choices=["fixed", "wont_fix", "by_design"], default=None,
                             help="Bug 收尾结论（kind=bug 必填）。")

    args = parser.parse_args()

    if args.command == "init":
        return run_script("aip_init.py", ["--repo-root", args.repo_root, "--template-root", args.template_root])

    if args.command == "start":
        feature_id = args.feature_id_flag or args.feature_id
        if not feature_id:
            parser.error("start requires FEATURE_ID or --feature-id FEATURE_ID")
        script_args = [
            "--repo-root",
            args.repo_root,
            "--feature-id",
            feature_id,
            "--template-root",
            args.template_root,
        ]
        if args.title:
            script_args.extend(["--title", args.title])
        return run_script("aip_start_feature.py", script_args)

    if args.command == "bug":
        bug_id = args.bug_id_flag or args.bug_id
        if not bug_id:
            parser.error("bug requires BUG_ID or --bug-id BUG_ID")
        script_args = ["--repo-root", args.repo_root, "--bug-id", bug_id, "--template-root", args.template_root]
        if args.title:
            script_args.extend(["--title", args.title])
        return run_script("aip_start_bug.py", script_args)

    if args.command == "resume":
        return run_script("aip_resume.py", ["--repo-root", args.repo_root])

    if args.command == "check":
        return run_script("aip_check.py", ["--repo-root", args.repo_root])

    if args.command == "knowledge":
        return run_script("aip_knowledge.py", ["--repo-root", args.repo_root])

    if args.command == "done":
        done_args = ["--repo-root", args.repo_root]
        if args.resolution:
            done_args.extend(["--resolution", args.resolution])
        return run_script("aip_done.py", done_args)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
