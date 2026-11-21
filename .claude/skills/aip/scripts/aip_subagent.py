from __future__ import annotations

"""Claude Code SubagentStart 钩子入口：开子代理时把 AIP 的现状和两条规矩交给它。

子代理是另一份干净的上下文：它看不到主代理读过的在建线和条目，于是会把主代理踩过的坑再踩一遍，
或者自己往 `.aip/` 里写东西。这枚钩子在子代理第一轮之前把在建线、主题目录和两条规矩注入进去
（走 additionalContext，字段必须嵌在 hookSpecificOutput 里，放顶层会被静默忽略）。

只注入、不改任何文件；出错不出声（子代理照常开，只是少了这段）。
"""

import json
import os
import sys
from pathlib import Path

from aip_lookup import index_lines
from aip_item import TYPES, list_items

RULES = ("AIP 规矩（子代理照这个来）：1) 只有主代理写 `.aip/`，你发现了什么就汇报，不要新建或改条目；"
         "2) 动手前读 `.aip/conventions.md`，改代码前跑 `aip_lookup.py relevant <要改的文件>` 看相关的主题和条目。")


def context_for(repo: Path) -> str:
    parts = [RULES]
    tracks = [t for t in list_items(repo, "track") if t.status in TYPES["track"].statuses]
    if tracks:
        parts.append("当前在建线（.aip/tracks/，别重新规划，按它的下一步来）：\n"
                     + "\n".join(f"### {t.path.name}\n{t.body.strip()}" for t in tracks))
    topics = index_lines(repo)
    if topics:
        parts.append("主题资料（.aip/reference/，按「什么时候读」挑跟你这件事有关的读）：\n" + "\n".join(topics))
    return "\n\n".join(parts)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        data = {}
    repo = Path(data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if not (repo / ".aip" / "config.yaml").exists():
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SubagentStart",
                                             "additionalContext": context_for(repo)}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(0)
