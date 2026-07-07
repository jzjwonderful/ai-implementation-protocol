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
        # 新模型不分发任何斜杠命令；即使源里残留 commands/ 也不带进安装目录。
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "commands"),
    )


def install_skills(source_plugin: Path, home: Path, force: bool) -> list[Path]:
    skills_root = source_plugin / "skills"
    if not skills_root.exists():
        raise SystemExit(f"Plugin skills dir not found: {skills_root}")

    installed: list[Path] = []
    for src in sorted(p for p in skills_root.iterdir() if (p / "SKILL.md").exists()):
        destination_skill_dir = home / ".claude" / "skills" / src.name
        if destination_skill_dir.exists():
            if not force:
                raise SystemExit(f"Skill destination exists: {destination_skill_dir}. Re-run with --force to replace it.")
            shutil.rmtree(destination_skill_dir)
        destination_skill_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / "SKILL.md", destination_skill_dir / "SKILL.md")
        installed.append(destination_skill_dir / "SKILL.md")
    return installed


def purge_obsolete_commands(home: Path) -> list[Path]:
    # 新模型只有技能、没有斜杠命令。清掉旧 per-command 模型在 ~/.claude/commands/aip
    # 留下的命令文件，避免升级后 Claude 里还冒出 check/resume/start 等旧命令。
    obsolete = home / ".claude" / "commands" / "aip"
    if obsolete.is_dir():
        shutil.rmtree(obsolete)
        return [obsolete]
    return []


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
    installed = install_skills(destination_plugin, home, args.force)
    purged = purge_obsolete_commands(home)

    # 安装后自检：关键文件真落盘了才算装好。
    missing = [p for p in [destination_plugin / ".claude-plugin" / "plugin.json",
                           destination_plugin / "scripts" / "aip_init.py"] if not p.exists()]
    if missing or not installed:
        raise SystemExit("Install incomplete: missing " + (", ".join(str(p) for p in missing) or "skills"))

    print(f"Installed Claude Code plugin: {destination_plugin}")
    for path in installed:
        print(f"Installed skill: {path}")
    for path in purged:
        print(f"Removed obsolete commands: {path}")
    print(f"Health check any time: python {destination_plugin / 'scripts' / 'aip_doctor.py'} --repo-root <your-project>")
    print("Restart Claude Code or open a new session for the skills to be picked up.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
