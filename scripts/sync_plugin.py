from __future__ import annotations

"""把顶层规范源（scripts/docs/templates/schemas）同步进可分发 plugin 包。

plugin 包（plugins/ai-implementation-protocol/）需自带这些副本才能脱离克隆路径运行；
本脚本让顶层成为唯一真源，plugin 副本由此再生，消除手维护两份的漂移隐患。
保留 plugin 独有内容：.codex-plugin/、skills/、assets/、README.md。
"""

import argparse
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "ai-implementation-protocol"
SYNCED_DIRS = ["scripts", "docs", "templates", "schemas"]
SYNCED_FILES = ["VERSION"]
# superpowers/ 是开发期产物（spec/plan），不进可分发插件包。
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "superpowers")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync canonical top-level sources into the plugin package.")
    parser.add_argument("--check", action="store_true", help="只报告将同步什么，不写入。")
    parser.add_argument("--repo-root", default=None, help="仓库根目录（当前已用脚本位置推断，此参数为兼容保留，不影响行为）。")
    args = parser.parse_args()

    if not (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").exists():
        raise SystemExit(f"Plugin package not found: {PLUGIN_ROOT}")

    for name in SYNCED_DIRS:
        src = REPO_ROOT / name
        dst = PLUGIN_ROOT / name
        if not src.exists():
            print(f"skip (no source): {name}")
            continue
        if args.check:
            print(f"would sync: {name} -> plugins/ai-implementation-protocol/{name}")
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=IGNORE)
        print(f"synced: {name}")

    for name in SYNCED_FILES:
        src = REPO_ROOT / name
        if not src.exists():
            print(f"skip (no source): {name}")
            continue
        if args.check:
            print(f"would sync: {name} -> plugins/ai-implementation-protocol/{name}")
            continue
        shutil.copy2(src, PLUGIN_ROOT / name)
        print(f"synced: {name}")

    print("Plugin sync complete." if not args.check else "Check only; nothing written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
