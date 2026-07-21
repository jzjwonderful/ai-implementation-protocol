from __future__ import annotations

"""一键安装 AIP 到本机已支持的全部 AI 运行时。

当前支持：Claude Code、Codex、Grok。各端分装脚本仍可单独用：
  install_claude_plugin.py / install_codex_plugin.py / install_grok_plugin.py

本脚本只拷一次引擎包到 ~/plugins/，再按目标写各端 skills，避免连跑三端时
第二次因「目标已存在」失败。
"""

import argparse
import shutil
import sys
from pathlib import Path

import install_claude_plugin as claude
import install_codex_plugin as codex
import install_grok_plugin as grok

PLUGIN_NAME = "ai-implementation-protocol"
# 有新运行时就加进这里；--targets 的合法名也来自这张表。
SUPPORTED = ("claude", "codex", "grok")


def copy_engine(source: Path, destination: Path, force: bool) -> None:
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
    if destination.exists():
        if not force:
            raise SystemExit(
                f"Destination exists: {destination}. Re-run with --force to replace it."
            )
        shutil.rmtree(destination)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "commands"),
    )


def parse_targets(raw: str) -> list[str]:
    text = (raw or "all").strip().lower()
    if text in ("all", "*"):
        return list(SUPPORTED)
    parts = [p.strip() for p in text.replace(" ", ",").split(",") if p.strip()]
    bad = [p for p in parts if p not in SUPPORTED]
    if bad:
        raise SystemExit(
            f"Unknown target(s): {', '.join(bad)}. Supported: {', '.join(SUPPORTED)}, or all"
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
    force: bool,
    user_plugin: bool,
) -> list[str]:
    """装一端，返回给人看的落点说明行。"""
    lines: list[str] = []
    if name == "claude":
        installed = claude.install_skills(destination_plugin, home, force)
        purged = claude.purge_obsolete_commands(home)
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
        installed = grok.install_skills(destination_plugin, home, force)
        lines.append(f"[grok] skills → {home / '.grok' / 'skills'}")
        for p in installed:
            lines.append(f"  skill: {p}")
        if user_plugin:
            path = grok.install_user_plugin(destination_plugin, home, force)
            lines.append(f"  user plugin: {path}")
    else:
        raise SystemExit(f"Internal error: unhandled target {name!r}")
    return lines


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
        "--force",
        action="store_true",
        help="Replace existing engine package and skill directories.",
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
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    home = args.home.resolve()
    targets = parse_targets(args.targets)
    source_plugin = repo_root / "plugins" / PLUGIN_NAME
    destination_plugin = home / "plugins" / PLUGIN_NAME

    if not source_plugin.is_dir():
        raise SystemExit(f"Plugin package not found: {source_plugin}")

    copy_engine(source_plugin, destination_plugin, args.force)

    all_lines: list[str] = [f"Engine package: {destination_plugin}"]
    for name in targets:
        all_lines.extend(
            install_one(name, destination_plugin, home, args.force, args.user_plugin)
        )

    # 自检：引擎脚本在，且每个目标至少有 aip skill
    missing: list[Path] = []
    if not (destination_plugin / "scripts" / "aip_init.py").exists():
        missing.append(destination_plugin / "scripts" / "aip_init.py")
    skill_roots = {
        "claude": home / ".claude" / "skills",
        "codex": home / ".agents" / "skills",
        "grok": home / ".grok" / "skills",
    }
    for name in targets:
        for skill in ("aip", "root-cause"):
            p = skill_roots[name] / skill / "SKILL.md"
            if not p.exists():
                missing.append(p)
    if missing:
        raise SystemExit("Install incomplete: missing " + ", ".join(str(p) for p in missing))

    for line in all_lines:
        print(line)
    print(f"Installed for: {', '.join(targets)}")
    print(
        f"Health check: python {destination_plugin / 'scripts' / 'aip_doctor.py'} --repo-root <your-project>"
    )
    print("Restart Claude Code / Codex / Grok (or open a new session) to pick up skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
