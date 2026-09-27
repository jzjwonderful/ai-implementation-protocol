"""安装器共用：装完在 aip 技能目录写 SOURCE.json，让装好的技能以后能自己查更新、自己更新（/aip update）。

格式和读写都在引擎的 aip_update.py，这里只负责把引擎脚本目录加进导入路径再转调。
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_NAME = "ai-implementation-protocol"
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "plugins" / PLUGIN_NAME / "skills" / "aip" / "scripts"))

import aip_update  # noqa: E402


def record(installed: list[Path], scope: str, target: Path | None = None, source_repo: Path = REPO_ROOT) -> None:
    """installed 里凡是 aip 技能目录，都写一份来源记录。写不出来不影响安装。"""
    for d in installed:
        if d.name == "SKILL.md":  # 有的安装器返回 SKILL.md 路径而不是技能目录
            d = d.parent
        if d.name == "aip":
            try:
                aip_update.write_install_source(d, source_repo, scope, target)
            except OSError as e:
                print(f"（没写成来源记录 {d / aip_update.SOURCE_FILE}：{e}；以后 /aip update 查不了这份）")
