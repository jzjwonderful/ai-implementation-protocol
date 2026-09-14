from __future__ import annotations

"""把 AIP 装进 Claude Code：整份技能目录（SKILL.md + scripts/ + templates/ + reference/）拷到
~/.claude/skills/<skill>/。脚本随技能走，技能里写的相对路径装到哪都成立。

安装即覆盖：装过就先清掉旧目录再拷（和 Codex 安装器一致）。
"""

import argparse
import shutil
from pathlib import Path


PLUGIN_NAME = "ai-implementation-protocol"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")


def install_skills(source_skills: Path, home: Path) -> list[Path]:
    if not source_skills.is_dir():
        raise SystemExit(f"Plugin skills dir not found: {source_skills}")
    installed: list[Path] = []
    for src in sorted(p for p in source_skills.iterdir() if (p / "SKILL.md").exists()):
        dst = home / ".claude" / "skills" / src.name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=IGNORE)
        installed.append(dst)
    return installed


def purge_obsolete(home: Path) -> list[Path]:
    # 旧 per-command 模型留在 ~/.claude/commands/aip 的命令文件：清掉，免得旧命令还冒出来。
    purged: list[Path] = []
    obsolete = home / ".claude" / "commands" / "aip"
    if obsolete.is_dir():
        shutil.rmtree(obsolete)
        purged.append(obsolete)
    return purged


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the AIP skills for Claude Code.")
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
        help="Home directory that contains .claude/skills/. Defaults to the current user home.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    home = args.home.resolve()
    source_skills = repo_root / "plugins" / PLUGIN_NAME / "skills"

    installed = install_skills(source_skills, home)
    purged = purge_obsolete(home)

    # 安装后自检：关键文件真落盘了才算装好。
    aip_dir = home / ".claude" / "skills" / "aip"
    missing = [p for p in [aip_dir / "SKILL.md",
                           aip_dir / "VERSION",
                           aip_dir / "scripts" / "aip_init.py",
                           aip_dir / "templates" / "overview-template.md"] if not p.exists()]
    if missing or not installed:
        raise SystemExit("Install incomplete: missing " + (", ".join(str(p) for p in missing) or "skills"))

    for path in installed:
        print(f"Installed skill: {path}")
    for path in purged:
        print(f"Removed obsolete commands: {path}")
    legacy = home / "plugins" / PLUGIN_NAME
    if legacy.is_dir():
        print(f"Note: {legacy} is no longer used by Claude Code (Codex still installs there); "
              "remove it if you only use Claude Code.")
    print(f"Health check any time: python {aip_dir / 'scripts' / 'aip_doctor.py'} --repo-root <your-project>")
    print("Restart Claude Code or open a new session for the skills to be picked up.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
