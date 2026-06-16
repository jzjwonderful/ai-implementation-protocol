from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PLUGIN_NAME = "ai-implementation-protocol"


def copy_plugin(source: Path, destination: Path, force: bool) -> None:
    if not (source / ".claude-plugin" / "plugin.json").exists():
        raise SystemExit(f"Plugin manifest not found: {source / '.claude-plugin' / 'plugin.json'}")

    if destination.exists():
        if not force:
            raise SystemExit(f"Destination exists: {destination}. Re-run with --force to replace it.")
        shutil.rmtree(destination)

    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )


def install_skill(source_plugin: Path, home: Path, force: bool) -> Path:
    source_skill = source_plugin / "skills" / "aip" / "SKILL.md"
    destination_skill_dir = home / ".claude" / "skills" / "aip"
    destination_skill = destination_skill_dir / "SKILL.md"

    if not source_skill.exists():
        raise SystemExit(f"AIP skill not found: {source_skill}")

    if destination_skill_dir.exists():
        if not force:
            raise SystemExit(f"Skill destination exists: {destination_skill_dir}. Re-run with --force to replace it.")
        shutil.rmtree(destination_skill_dir)

    destination_skill_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_skill, destination_skill)
    return destination_skill


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the AIP plugin for Claude Code.")
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="AIP repository root. Defaults to the parent of this script directory.",
    )
    parser.add_argument(
        "--home",
        default=Path.home(),
        type=Path,
        help="Home directory that contains .claude/skills/ and plugins/. Defaults to the current user home.",
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing installed plugin directory or skill.")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    home = args.home.resolve()
    source_plugin = repo_root / "plugins" / PLUGIN_NAME
    destination_plugin = home / "plugins" / PLUGIN_NAME

    copy_plugin(source_plugin, destination_plugin, args.force)
    destination_skill = install_skill(destination_plugin, home, args.force)

    print(f"Installed Claude Code plugin: {destination_plugin}")
    print(f"Installed AIP skill: {destination_skill}")
    print("Restart Claude Code or open a new session for the skill to be picked up.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
