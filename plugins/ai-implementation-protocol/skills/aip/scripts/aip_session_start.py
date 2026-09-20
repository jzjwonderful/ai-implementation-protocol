from __future__ import annotations

"""Claude Code SessionStart 钩子入口：把 OVERVIEW 打进上下文。

钩子从 stdin 收到 JSON，其中 source 是 startup / resume / clear / compact / fork。
compact 表示上下文刚被压缩成摘要——这时 AI 的记忆最不可靠，所以除了打印看板，
还要明说"以看板为准、没写回的进展先补"。压缩前的钩子（PreCompact）输出到不了模型，
所以补救只能放在压缩之后这一刻。
"""

import argparse
import json
import sys
from pathlib import Path

from _aip_common import force_utf8, project_living_path, read_text


def read_source() -> str:
    try:
        return str(json.load(sys.stdin).get("source", ""))
    except (ValueError, OSError, AttributeError):
        return ""


def banner(source: str) -> str:
    if source == "compact":
        return ("=== AIP：上下文刚被压缩，摘要可能丢细节。下面的 OVERVIEW 是当前状态的权威来源；"
                "如果压缩前有进展还没写回看板，先补写再继续。===")
    return "=== AIP OVERVIEW ==="


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="Print .aip/OVERVIEW.md for a Claude Code SessionStart hook.")
    ap.add_argument("--repo-root", default=".")
    a = ap.parse_args()
    overview = project_living_path(Path(a.repo_root).resolve(), "OVERVIEW.md")
    if not overview.exists():
        print("AIP：项目尚未初始化（无 .aip/OVERVIEW.md）。需要时跑 aip init。")
        return 0
    print(banner(read_source()))
    print(read_text(overview))
    print("===================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
