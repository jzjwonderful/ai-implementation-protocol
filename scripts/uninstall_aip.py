from __future__ import annotations

"""把 AIP 从本机彻底卸载（Claude Code / Codex / Grok 三套落点都清）。

清理范围（缺啥跳啥，幂等）：
- 引擎包         ~/plugins/ai-implementation-protocol/
- Claude 技能    ~/.claude/skills/{aip,root-cause,aip-brainstorm}/
- Claude 旧命令  ~/.claude/commands/aip/        （旧 per-command 模型残留）
- Codex 技能     ~/.agents/skills/{aip,root-cause,aip-brainstorm}/
- Codex home 技能 $CODEX_HOME/skills/{aip,root-cause,aip-brainstorm}/（默认 ~/.codex/skills）
- Codex 旧命令   ~/.agents/commands/aip/
- Codex 市场条目 ~/.agents/plugins/marketplace.json 里的 ai-implementation-protocol
- Grok 技能      ~/.grok/skills/{aip,root-cause}/
- Grok 用户插件  ~/.grok/plugins/ai-implementation-protocol/

装进各业务仓库 .git/hooks/pre-commit 的 AIP 检查是逐仓库的、无法在这里枚举，
需到对应仓库手动删（删该文件或其中的 AIP gate 行）。
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

PLUGIN_NAME = "ai-implementation-protocol"

from _aip_common import SKILL_NAMES  # noqa: E402  唯一真源，新增技能只改 _aip_common


def _utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass


def rm(path: Path, removed: list[str]) -> None:
    if path.is_dir():
        shutil.rmtree(path); removed.append(str(path))
    elif path.exists():
        path.unlink(); removed.append(str(path))


def prune_marketplace(path: Path, removed: list[str]) -> None:
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        return
    kept = [p for p in plugins if p.get("name") != PLUGIN_NAME]
    if len(kept) != len(plugins):
        data["plugins"] = kept
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        removed.append(f"{path}（移除 {PLUGIN_NAME} 条目）")


def default_codex_home(home: Path) -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return home / ".codex"


def main() -> int:
    _utf8()
    ap = argparse.ArgumentParser(description="Uninstall AIP from this machine (Claude Code + Codex + Grok).")
    ap.add_argument("--home", default=Path.home(), type=Path, help="用户主目录。默认当前用户。")
    ap.add_argument("--codex-home", default=None, type=Path,
                    help="Codex home；默认取 CODEX_HOME，未设置则为 <home>/.codex。")
    args = ap.parse_args()
    home = args.home.resolve()
    codex_home = args.codex_home.expanduser().resolve() if args.codex_home else default_codex_home(home)
    removed: list[str] = []

    rm(home / "plugins" / PLUGIN_NAME, removed)
    for s in SKILL_NAMES:
        rm(home / ".claude" / "skills" / s, removed)
    rm(home / ".claude" / "commands" / "aip", removed)
    for s in SKILL_NAMES:
        rm(home / ".agents" / "skills" / s, removed)
    for s in SKILL_NAMES:
        rm(codex_home / "skills" / s, removed)
    rm(home / ".agents" / "commands" / "aip", removed)
    prune_marketplace(home / ".agents" / "plugins" / "marketplace.json", removed)
    for s in SKILL_NAMES:
        rm(home / ".grok" / "skills" / s, removed)
    rm(home / ".grok" / "plugins" / PLUGIN_NAME, removed)

    if removed:
        print("已移除：")
        for r in removed:
            print(f"  - {r}")
    else:
        print("没发现 AIP 安装痕迹（可能已卸载干净）。")
    print("提醒：装进各业务仓库 .git/hooks/pre-commit 的 AIP 检查需到对应仓库手动删。")
    print("重启 Claude Code / Codex / Grok 后命令与技能列表才刷新。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
