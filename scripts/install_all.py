from __future__ import annotations

"""一键安装 AIP 到本机已支持的全部 AI 运行时。

当前支持：Claude Code、Codex、Grok。各端分装脚本仍可单独用：
  install_claude_plugin.py / install_codex_plugin.py / install_grok_plugin.py

本脚本只拷一次引擎包到 ~/plugins/，再按目标写各端 skills，避免连跑三端时
第二次因「目标已存在」失败。

`--project <仓库>` 改成项目级安装：技能落进那个仓库（Claude 走 .claude/skills/，
Codex 走 .codex/skills/），随仓库走，不碰 ~/plugins 也不写市场条目。
Grok 没有约定俗成的项目级技能目录，所以项目级安装不含 Grok。
"""

import argparse
import shutil
import sys
from pathlib import Path

import install_claude_plugin as claude
import install_codex_plugin as codex
import install_grok_plugin as grok

PLUGIN_NAME = "ai-implementation-protocol"

# 技能清单的唯一真源在引擎里（aip 技能的 scripts/_aip_common.py）。
sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / PLUGIN_NAME / "skills" / "aip" / "scripts"))
from _aip_common import SKILL_NAMES  # noqa: E402

# 有新运行时就加进这里；--targets 的合法名也来自这张表。
SUPPORTED = ("claude", "codex", "grok")
# 有项目级技能目录约定的运行时。Grok 没有，所以 --project 不支持它。
PROJECT_SUPPORTED = ("claude", "codex")


def copy_engine(source: Path, destination: Path) -> None:
    manifests = [
        source / ".claude-plugin" / "plugin.json",
        source / ".codex-plugin" / "plugin.json",
        source / ".grok-plugin" / "plugin.json",
    ]
    if not any(m.exists() for m in manifests):
        raise SystemExit(
            f"Plugin package incomplete under {source}: need at least one of "
            ".claude-plugin / .codex-plugin / .grok-plugin plugin.json"
        )
    # 安装即覆盖：重跑一键脚本直接替换旧引擎包，不设开关。
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "commands"),
    )


def parse_targets(raw: str, supported: tuple[str, ...] = SUPPORTED) -> list[str]:
    text = (raw or "all").strip().lower()
    if text in ("all", "*"):
        return list(supported)
    parts = [p.strip() for p in text.replace(" ", ",").split(",") if p.strip()]
    bad = [p for p in parts if p not in supported]
    if bad:
        raise SystemExit(
            f"Unknown target(s): {', '.join(bad)}. Supported: {', '.join(supported)}, or all"
        )
    # 去重且保序
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    if not out:
        raise SystemExit("No install targets selected.")
    return out


def install_one(
    name: str,
    destination_plugin: Path,
    home: Path,
    user_plugin: bool,
) -> list[str]:
    """装一端，返回给人看的落点说明行。一键脚本一律覆盖安装。"""
    lines: list[str] = []
    if name == "claude":
        # claude 安装器一律覆盖安装，入参是插件包里的 skills 目录。
        installed = claude.install_skills(destination_plugin / "skills", home)
        purged = claude.purge_obsolete(home)
        lines.append(f"[claude] skills → {home / '.claude' / 'skills'}")
        for p in installed:
            lines.append(f"  skill: {p}")
        for p in purged:
            lines.append(f"  removed obsolete: {p}")
    elif name == "codex":
        codex_home = codex.default_codex_home(home)
        skill_roots = codex.codex_skill_roots(home, codex_home, "both")
        installed = codex.install_skills(destination_plugin, skill_roots)
        purged = codex.purge_obsolete_commands(home)
        marketplace_path = home / ".agents" / "plugins" / "marketplace.json"
        marketplace = codex.load_marketplace(marketplace_path)
        codex.upsert_marketplace_entry(marketplace, f"./plugins/{PLUGIN_NAME}")
        codex.write_json(marketplace_path, marketplace)
        lines.append(f"[codex] skills → {home / '.agents' / 'skills'}")
        for p in installed:
            lines.append(f"  skill: {p}")
        for p in purged:
            lines.append(f"  removed obsolete: {p}")
        lines.append(f"  marketplace: {marketplace_path}")
    elif name == "grok":
        installed = grok.install_skills(destination_plugin, home)
        lines.append(f"[grok] skills → {home / '.grok' / 'skills'}")
        for p in installed:
            lines.append(f"  skill: {p}")
        if user_plugin:
            path = grok.install_user_plugin(destination_plugin, home)
            lines.append(f"  user plugin: {path}")
    else:
        raise SystemExit(f"Internal error: unhandled target {name!r}")
    return lines


def install_into_project(repo_root: Path, project: Path, raw_targets: str) -> int:
    """项目级安装：把技能装进指定仓库，交给各端分装器自己处理落点差异。"""
    project = project.resolve()
    if not project.is_dir():
        raise SystemExit(f"Project not found: {project}")
    targets = parse_targets(raw_targets, PROJECT_SUPPORTED)
    for name in targets:
        print(f"=== {name} ===")
        if name == "claude":
            rc = claude.install_into_project(repo_root, project)
        else:
            rc = codex.install_into_project(repo_root, project)
        if rc != 0:
            return rc
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Install AIP for all supported AI runtimes in one shot "
            f"({', '.join(SUPPORTED)})."
        )
    )
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
        help="Home directory for plugins/ and runtime skill dirs. Defaults to the current user home.",
    )
    parser.add_argument(
        "--targets",
        default="all",
        help=f"Comma-separated subset of {{{','.join(SUPPORTED)}}} or 'all' (default).",
    )
    parser.add_argument(
        "--user-plugin",
        action="store_true",
        help="When installing grok, also copy package under ~/.grok/plugins/.",
    )
    parser.add_argument(
        "--project",
        default=None,
        type=Path,
        help="Install into this project instead of the user home "
             f"({' + '.join(PROJECT_SUPPORTED)} only; the skills travel with that repository).",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    if args.project is not None:
        return install_into_project(repo_root, args.project, args.targets)
    home = args.home.resolve()
    targets = parse_targets(args.targets)
    source_plugin = repo_root / "plugins" / PLUGIN_NAME
    destination_plugin = home / "plugins" / PLUGIN_NAME

    if not source_plugin.is_dir():
        raise SystemExit(f"Plugin package not found: {source_plugin}")

    copy_engine(source_plugin, destination_plugin)

    all_lines: list[str] = [f"Engine package: {destination_plugin}"]
    for name in targets:
        all_lines.extend(
            install_one(name, destination_plugin, home, args.user_plugin)
        )

    # 自检：引擎脚本在，且每个目标至少有 aip skill
    missing: list[Path] = []
    engine_init = destination_plugin / "skills" / "aip" / "scripts" / "aip_init.py"
    if not engine_init.exists():
        missing.append(engine_init)
    skill_roots = {
        "claude": home / ".claude" / "skills",
        "codex": home / ".agents" / "skills",
        "grok": home / ".grok" / "skills",
    }
    for name in targets:
        for skill in SKILL_NAMES:
            p = skill_roots[name] / skill / "SKILL.md"
            if not p.exists():
                missing.append(p)
    if missing:
        raise SystemExit("Install incomplete: missing " + ", ".join(str(p) for p in missing))

    for line in all_lines:
        print(line)
    print(f"Installed for: {', '.join(targets)}")
    print(
        f"Health check: python {destination_plugin / 'skills' / 'aip' / 'scripts' / 'aip_doctor.py'} --repo-root <your-project>"
    )
    print("Restart Claude Code / Codex / Grok (or open a new session) to pick up skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
