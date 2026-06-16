from __future__ import annotations

"""把 AIP 作为 Claude Code 技能安装。

与 Codex 装法平行：复用同一套工具无关的 CLI/协议/模板，只换外壳与落点。
默认装到目标仓库的项目级 `.claude/skills/aip/SKILL.md`（最小侵入、易回退）；
`--user` 则装到 `~/.claude/skills/aip/SKILL.md`（所有项目可用）。
技能内回填引擎根路径（本 AIP 仓库），技能据此调 `scripts/aip.py`。
"""

import argparse
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
SKILL_TEMPLATE = ENGINE_ROOT / "templates" / "claude-skill-SKILL.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Install AIP as a Claude Code skill.")
    parser.add_argument("--repo-root", default=".", type=Path, help="目标项目根（项目级安装）。默认当前目录。")
    parser.add_argument("--engine-root", default=ENGINE_ROOT, type=Path, help="AIP 引擎根（含 scripts/）。默认本仓库。")
    parser.add_argument("--user", action="store_true", help="装到用户级 ~/.claude/skills/ 而非项目级。")
    parser.add_argument("--home", default=Path.home(), type=Path, help="用户主目录（--user 时用）。")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的技能。")
    args = parser.parse_args()

    if not SKILL_TEMPLATE.exists():
        raise SystemExit(f"Skill template not found: {SKILL_TEMPLATE}")

    engine_root = args.engine_root.resolve()
    content = SKILL_TEMPLATE.read_text(encoding="utf-8").replace("{{ENGINE_ROOT}}", engine_root.as_posix())

    if args.user:
        skill_dir = args.home.resolve() / ".claude" / "skills" / "aip"
    else:
        skill_dir = args.repo_root.resolve() / ".claude" / "skills" / "aip"
    skill_file = skill_dir / "SKILL.md"

    if skill_file.exists() and not args.force:
        raise SystemExit(f"Skill exists: {skill_file}. Re-run with --force to replace it.")

    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(content, encoding="utf-8", newline="\n")

    print(f"Installed AIP Claude Code skill: {skill_file}")
    print(f"Engine root: {engine_root}")
    print("Next: in the target repo run `aip init` via the skill (or: "
          f'python "{engine_root.as_posix()}/scripts/aip.py" init --repo-root .).')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
