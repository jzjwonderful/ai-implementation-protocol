from __future__ import annotations

import argparse
import json
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
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )


def install_skill(source_plugin: Path, home: Path, force: bool) -> Path:
    source_skill = source_plugin / "skills" / "aip" / "SKILL.md"
    destination_skill_dir = home / ".agents" / "skills" / "aip"
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
    parser.add_argument("--force", action="store_true", help="Replace an existing installed plugin directory.")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    home = args.home.resolve()
    source_plugin = repo_root / "plugins" / PLUGIN_NAME
    destination_plugin = home / "plugins" / PLUGIN_NAME
    marketplace_path = home / ".agents" / "plugins" / "marketplace.json"

    copy_plugin(source_plugin, destination_plugin, args.force)
    destination_skill = install_skill(destination_plugin, home, args.force)

    marketplace = load_marketplace(marketplace_path)
    upsert_marketplace_entry(marketplace, f"./plugins/{PLUGIN_NAME}")
    write_json(marketplace_path, marketplace)

    print(f"Installed Codex plugin: {destination_plugin}")
    print(f"Installed AIP skill: {destination_skill}")
    print(f"Updated marketplace: {marketplace_path}")
    print("Restart Codex or refresh plugins if the plugin list is already open.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
