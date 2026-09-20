from __future__ import annotations

"""把 AIP 装进 Claude Code：整份技能目录（SKILL.md + scripts/ + templates/ + reference/）拷到
`<落点>/.claude/skills/<skill>/`。脚本随技能走，技能里写的相对路径装到哪都成立。

两种落点：
- 默认「个人级」：落在用户主目录，本机所有项目都能用。
- `--project <仓库>`「项目级」：落在那个仓库里，随仓库走，别人 clone 下来就有。
  项目级技能会进版本库，本脚本装完会把该说的提醒印出来（钩子重指、要不要提交）。

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


def install_into_project(repo_root: Path, project: Path) -> int:
    """项目级安装：技能落 <project>/.claude/skills/，随仓库走。"""
    project = project.resolve()
    if not project.is_dir():
        raise SystemExit(f"Project not found: {project}")
    installed = install_skills(repo_root / "plugins" / PLUGIN_NAME / "skills", project)
    aip_dir = project / ".claude" / "skills" / "aip"
    _verify(aip_dir, installed)
    for path in installed:
        print(f"Installed skill: {path}")
    print(f"Health check any time: python {aip_dir / 'scripts' / 'aip_doctor.py'} --repo-root {project}")
    for line in project_notes(project, aip_dir):
        print(line)
    print("Open a new Claude Code session in that project for the skills to be picked up.")
    return 0


def _verify(aip_dir: Path, installed: list[Path]) -> None:
    """安装后自检：关键文件真落盘了才算装好。"""
    missing = [p for p in [aip_dir / "SKILL.md",
                           aip_dir / "VERSION",
                           aip_dir / "scripts" / "aip_init.py",
                           aip_dir / "templates" / "overview-template.md"] if not p.exists()]
    if missing or not installed:
        raise SystemExit("Install incomplete: missing " + (", ".join(str(p) for p in missing) or "skills"))


def project_notes(project: Path, aip_dir: Path) -> list[str]:
    """项目级安装装完要交代的事：钩子指哪、这些文件会不会进版本库。"""
    notes = [
        "",
        "项目级安装。接下来：",
        f"  1. 让本仓库的钩子指向这份副本（老仓库的钩子可能还指着已经搬走的路径）："
        f"\n     python {aip_dir / 'scripts' / 'install_hooks.py'} --repo-root {project}"
        f" --engine-root {aip_dir} --session-start --force",
        "  2. 在这个仓库开新会话，用 /aip init（已初始化过的仓库跑一次也是幂等的）。",
    ]
    gitignore = project / ".gitignore"
    tracked_hint = "  3. 技能目录会进版本库（随仓库分发给所有人）。不想进就加进 .gitignore。"
    if gitignore.is_file():
        text = gitignore.read_text(encoding="utf-8", errors="ignore")
        if ".claude/skills" in text:
            tracked_hint = "  3. 注意：本仓库 .gitignore 里排除了 .claude/skills，这份副本不会随仓库分发。"
    notes.append(tracked_hint)
    return notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install the AIP skills for Claude Code.")
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="AIP repository root. Defaults to the parent of this script directory.",
    )
    parser.add_argument(
        "--home",
        default=None,
        type=Path,
        help="Home directory that contains .claude/skills/. Defaults to the current user home.",
    )
    parser.add_argument(
        "--project",
        default=None,
        type=Path,
        help="Install into this project instead of the user home: <project>/.claude/skills/. "
             "The skills then travel with that repository.",
    )
    args = parser.parse_args(argv)

    if args.project is not None and args.home is not None:
        raise SystemExit("--project 和 --home 只能给一个：前者装进项目，后者装进主目录。")

    repo_root = args.repo_root.resolve()
    if args.project is not None:
        return install_into_project(repo_root, args.project)

    home = (args.home or Path.home()).resolve()
    installed = install_skills(repo_root / "plugins" / PLUGIN_NAME / "skills", home)
    purged = purge_obsolete(home)

    aip_dir = home / ".claude" / "skills" / "aip"
    _verify(aip_dir, installed)

    for path in installed:
        print(f"Installed skill: {path}")
    for path in purged:
        print(f"Removed obsolete commands: {path}")
    print(f"Health check any time: python {aip_dir / 'scripts' / 'aip_doctor.py'} --repo-root <your-project>")

    legacy = home / "plugins" / PLUGIN_NAME
    if legacy.is_dir():
        print(f"Note: {legacy} is no longer used by Claude Code (Codex still installs there); "
              "remove it if you only use Claude Code.")
    print("Restart Claude Code or open a new session for the skills to be picked up.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
