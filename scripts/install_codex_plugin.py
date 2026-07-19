from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any


PLUGIN_NAME = "ai-implementation-protocol"
PLUGIN_CATEGORY = "Productivity"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def copy_plugin(source: Path, destination: Path, force: bool) -> None:
    if not (source / ".codex-plugin" / "plugin.json").exists():
        raise SystemExit(f"Plugin manifest not found: {source / '.codex-plugin' / 'plugin.json'}")

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


def purge_obsolete_commands(home: Path) -> list[Path]:
    # 清掉旧 per-command 模型在 ~/.agents/commands/aip 留下的命令文件。
    obsolete = home / ".agents" / "commands" / "aip"
    if obsolete.is_dir():
        shutil.rmtree(obsolete)
        return [obsolete]
    return []


def default_codex_home(home: Path) -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return home / ".codex"


def codex_skill_roots(home: Path, codex_home: Path, skill_scope: str) -> list[Path]:
    roots: list[Path] = []
    if skill_scope in {"agents", "both"}:
        roots.append(home / ".agents" / "skills")
    if skill_scope in {"codex-home", "both"}:
        roots.append(codex_home / "skills")

    seen: set[str] = set()
    unique: list[Path] = []
    for root in roots:
        resolved = root.expanduser().resolve()
        key = str(resolved).casefold()
        if key not in seen:
            seen.add(key)
            unique.append(resolved)
    return unique


def install_skills(source_plugin: Path, skill_roots: list[Path], force: bool) -> list[Path]:
    skills_root = source_plugin / "skills"
    if not skills_root.exists():
        raise SystemExit(f"Plugin skills dir not found: {skills_root}")

    sources = sorted(p for p in skills_root.iterdir() if (p / "SKILL.md").exists())
    planned = [(skill_root, src, skill_root / src.name) for skill_root in skill_roots for src in sources]
    conflicts = [destination for _, _, destination in planned if destination.exists()]
    if conflicts and not force:
        raise SystemExit("Skill destination exists: " + ", ".join(str(p) for p in conflicts)
                         + ". Re-run with --force to replace it.")

    installed: list[Path] = []
    for _, src, destination_skill_dir in planned:
        if destination_skill_dir.exists():
            shutil.rmtree(destination_skill_dir)
        destination_skill_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / "SKILL.md", destination_skill_dir / "SKILL.md")
        installed.append(destination_skill_dir / "SKILL.md")
    return installed


def load_marketplace(path: Path) -> dict[str, Any]:
    if path.exists():
        return read_json(path)
    return {
        "name": "local",
        "interface": {"displayName": "Local Plugins"},
        "plugins": [],
    }


def upsert_marketplace_entry(marketplace: dict[str, Any], plugin_path: str) -> None:
    marketplace.setdefault("name", "local")
    marketplace.setdefault("interface", {"displayName": "Local Plugins"})
    plugins = marketplace.setdefault("plugins", [])

    entry = {
        "name": PLUGIN_NAME,
        "source": {
            "source": "local",
            "path": plugin_path,
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": PLUGIN_CATEGORY,
    }

    for idx, existing in enumerate(plugins):
        if existing.get("name") == PLUGIN_NAME:
            plugins[idx] = entry
            return

    plugins.append(entry)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the AIP Codex plugin into the current user's local plugin directory.")
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
        help="Home directory that contains .agents/plugins/marketplace.json and plugins/. Defaults to the current user home.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=True,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--skill-scope",
        choices=["agents", "codex-home", "both"],
        default="both",
        help="Where to install Codex skills: both=~/.agents/skills and $CODEX_HOME/skills or ~/.codex/skills (default), "
             "agents=~/.agents/skills only, codex-home=$CODEX_HOME/skills or ~/.codex/skills only.",
    )
    parser.add_argument(
        "--codex-home",
        default=None,
        type=Path,
        help="Codex home used when --skill-scope includes codex-home. Defaults to CODEX_HOME or <home>/.codex.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    home = args.home.resolve()
    codex_home = args.codex_home.expanduser().resolve() if args.codex_home else default_codex_home(home)
    skill_roots = codex_skill_roots(home, codex_home, args.skill_scope)
    source_plugin = repo_root / "plugins" / PLUGIN_NAME
    destination_plugin = home / "plugins" / PLUGIN_NAME
    marketplace_path = home / ".agents" / "plugins" / "marketplace.json"

    copy_plugin(source_plugin, destination_plugin, args.force)
    installed = install_skills(destination_plugin, skill_roots, args.force)
    purged = purge_obsolete_commands(home)

    marketplace = load_marketplace(marketplace_path)
    upsert_marketplace_entry(marketplace, f"./plugins/{PLUGIN_NAME}")
    write_json(marketplace_path, marketplace)

    # 安装后自检：关键文件真落盘了才算装好。
    missing = [p for p in [destination_plugin / ".codex-plugin" / "plugin.json",
                           destination_plugin / "scripts" / "aip_init.py",
                           marketplace_path] if not p.exists()]
    if missing or not installed:
        raise SystemExit("Install incomplete: missing " + (", ".join(str(p) for p in missing) or "skills"))

    print(f"Installed Codex plugin: {destination_plugin}")
    for path in installed:
        print(f"Installed skill: {path}")
    for path in purged:
        print(f"Removed obsolete commands: {path}")
    print(f"Updated marketplace: {marketplace_path}")
    print(f"Health check any time: python {destination_plugin / 'scripts' / 'aip_doctor.py'} --repo-root <your-project>")
    print("Restart Codex or refresh plugins if the plugin list is already open.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
