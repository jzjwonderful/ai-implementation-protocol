from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PLUGIN_NAME = "ai-implementation-protocol"


def copy_plugin(source: Path, destination: Path, force: bool) -> None:
    if not (source / ".grok-plugin" / "plugin.json").exists():
        raise SystemExit(f"Plugin manifest not found: {source / '.grok-plugin' / 'plugin.json'}")

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
        destination_skill_dir = home / ".grok" / "skills" / src.name
        if destination_skill_dir.exists():
            if not force:
                raise SystemExit(
                    f"Skill destination exists: {destination_skill_dir}. Re-run with --force to replace it."
                )
            shutil.rmtree(destination_skill_dir)
        destination_skill_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / "SKILL.md", destination_skill_dir / "SKILL.md")
        installed.append(destination_skill_dir / "SKILL.md")
    return installed


def install_user_plugin(source_plugin: Path, home: Path, force: bool) -> Path:
    """可选：把插件包装进 ~/.grok/plugins/，便于 `grok plugin list` 发现。

    默认不装：用户 skill（~/.grok/skills/）始终会被加载，足够日常使用。
    需要以 Grok plugin 形态管理时再加 --user-plugin。
    """
    destination = home / ".grok" / "plugins" / PLUGIN_NAME
    if destination.exists():
        if not force:
            raise SystemExit(
                f"Grok plugin destination exists: {destination}. Re-run with --force to replace it."
            )
        shutil.rmtree(destination)
    shutil.copytree(
        source_plugin,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "commands"),
    )
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the AIP plugin for Grok.")
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
        help="Home directory that contains .grok/skills/ and plugins/. Defaults to the current user home.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing installed plugin directory or skill.",
    )
    parser.add_argument(
        "--user-plugin",
        action="store_true",
        help="Also copy the package under ~/.grok/plugins/ (Grok plugin discovery). Skills still go to ~/.grok/skills/.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    home = args.home.resolve()
    source_plugin = repo_root / "plugins" / PLUGIN_NAME
    destination_plugin = home / "plugins" / PLUGIN_NAME

    copy_plugin(source_plugin, destination_plugin, args.force)
    installed = install_skills(destination_plugin, home, args.force)
    grok_plugin: Path | None = None
    if args.user_plugin:
        grok_plugin = install_user_plugin(destination_plugin, home, args.force)

    # 安装后自检：关键文件真落盘了才算装好。
    missing = [
        p
        for p in [
            destination_plugin / ".grok-plugin" / "plugin.json",
            destination_plugin / "scripts" / "aip_init.py",
        ]
        if not p.exists()
    ]
    if missing or not installed:
        raise SystemExit("Install incomplete: missing " + (", ".join(str(p) for p in missing) or "skills"))

    print(f"Installed Grok engine package: {destination_plugin}")
    for path in installed:
        print(f"Installed skill: {path}")
    if grok_plugin is not None:
        print(f"Installed Grok user plugin: {grok_plugin}")
        print("If the plugin is listed but inactive, run: grok plugin enable ai-implementation-protocol")
    print(
        f"Health check any time: python {destination_plugin / 'scripts' / 'aip_doctor.py'} --repo-root <your-project>"
    )
    print("Restart Grok or open a new session for the skills to be picked up.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
