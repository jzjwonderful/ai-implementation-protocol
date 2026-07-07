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
PLUGIN_DIR_NAME = Path("plugins") / "ai-implementation-protocol"
PLUGIN_ROOT = REPO_ROOT / PLUGIN_DIR_NAME
SYNCED_DIRS = ["scripts", "docs", "templates", "schemas"]
SYNCED_FILES = ["VERSION"]
# superpowers/ 是开发期产物（spec/plan），不进可分发插件包。
IGNORE_NAMES = {"__pycache__", ".DS_Store", "superpowers"}
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "superpowers")


def _synced_files(base: Path) -> set[Path]:
    """列出参与同步比对的文件（相对路径），套用与拷贝相同的忽略规则。"""
    if not base.is_dir():
        return set()
    out: set[Path] = set()
    for f in base.rglob("*"):
        if not f.is_file() or f.suffix == ".pyc":
            continue
        rel = f.relative_to(base)
        if any(p in IGNORE_NAMES for p in rel.parts):
            continue
        out.add(rel)
    return out


def drift(repo_root: Path | None = None) -> list[str]:
    """真实比对源与插件副本，返回不一致清单（空 = 逐字节一致）。

    这是唯一一份比对实现：aip_check.check_dual_copy 与 --check 都走这里。
    """
    root = repo_root or REPO_ROOT
    plugin = root / PLUGIN_DIR_NAME
    out: list[str] = []
    for name in SYNCED_DIRS:
        src, dst = root / name, plugin / name
        if not src.is_dir():
            continue
        src_files, dst_files = _synced_files(src), _synced_files(dst)
        for rel in sorted(src_files - dst_files, key=str):
            out.append(f"副本缺失: {name}/{rel.as_posix()}")
        for rel in sorted(dst_files - src_files, key=str):
            out.append(f"副本多余（源侧已删）: {name}/{rel.as_posix()}")
        for rel in sorted(src_files & dst_files, key=str):
            if (src / rel).read_bytes() != (dst / rel).read_bytes():
                out.append(f"副本漂移: {name}/{rel.as_posix()}")
    for name in SYNCED_FILES:
        src, dst = root / name, plugin / name
        if not src.is_file():
            continue
        if not dst.is_file():
            out.append(f"副本缺失: {name}")
        elif src.read_bytes() != dst.read_bytes():
            out.append(f"副本漂移: {name}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync canonical top-level sources into the plugin package.")
    parser.add_argument("--check", action="store_true", help="真实比对源与副本，不写入；有不一致退出码 1。")
    parser.add_argument("--repo-root", default=None, help="仓库根目录（当前已用脚本位置推断，此参数为兼容保留，不影响行为）。")
    args = parser.parse_args()

    if not (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").exists():
        raise SystemExit(f"Plugin package not found: {PLUGIN_ROOT}")

    if args.check:
        problems = drift()
        if problems:
            print("副本与源不一致（跑 python scripts/sync_plugin.py 重新生成）：")
            for p in problems:
                print(f"  - {p}")
            return 1
        print("副本与源一致，无需同步。")
        return 0

    for name in SYNCED_DIRS:
        src = REPO_ROOT / name
        dst = PLUGIN_ROOT / name
        if not src.exists():
            print(f"skip (no source): {name}")
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
        shutil.copy2(src, PLUGIN_ROOT / name)
        print(f"synced: {name}")

    print("Plugin sync complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
