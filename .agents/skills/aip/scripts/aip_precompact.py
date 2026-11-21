from __future__ import annotations

"""Claude Code PreCompact 钩子入口：压缩之前说清摘要里必须留下什么。

这个钩子在上下文被压缩**之前**跑，它的标准输出会被当成「写这份摘要的指示」（上限 1 万字符）。
AIP 最怕的就是压缩把在建线的进展、正在跑的验证和用户的明确要求丢掉——压缩之后的 SessionStart
钩子只能重新打印在建线文件，文件里没写回的那部分就真丢了。所以这里在压缩前把在建线全文和
几条「必须保留」的要求交给写摘要的那一轮。

只输出指示，不改任何文件、不挡压缩：钩子退 0，出错也不出声（摘要照常写，只是少了指示）。
"""

import argparse
import sys
from pathlib import Path

from _aip_common import force_utf8, project_living_path
from aip_item import TYPES, list_items

# PreCompact 钩子的输出上限（Claude Code 超了会截断）；留点余量给截断提示
OUTPUT_LIMIT = 10000
MARK = "\n…（在建线太长，这里截断了；完整内容在 .aip/tracks/ 下）"

KEEP = """写这份摘要时，下面几样必须原样留下，缺一样就等于这次会话白干：
1. 在建线的目标、卡在哪、下一步（下面附了原文），以及**还没写回在建线文件**的进展——摘要里要点明哪些进展还只存在于上下文里。
2. 这次实际跑过的验证命令（原样的命令行）和它们的结果；失败的要留原始报错，别概括成"有报错"。
3. 这次碰过的文件清单和每处改动的意图；没做完的改动要说清停在哪一步。
4. 用户明确提出的要求、否决和拍过的方向（原话优先，别改写）。
5. 已经查过的 `.aip/` 条目标识和结论（免得压缩后又从头查一遍）。
摘要之外不用保留寒暄、工具调用过程和已经读完归档的大段文件内容。"""


def tracks_text(repo: Path) -> str:
    tracks = [t for t in list_items(repo, "track") if t.status in TYPES["track"].statuses]
    if not tracks:
        return "（.aip/tracks/ 下没有在建线）"
    return "\n".join(f"### {t.path.name}\n{t.body.strip()}" for t in tracks)


def instructions(repo: Path, limit: int = OUTPUT_LIMIT) -> str:
    text = f"{KEEP}\n\n当前在建线（.aip/tracks/ 原文，摘要里按它的说法保留状态）：\n{tracks_text(repo)}"
    if len(text) > limit:
        text = text[: limit - len(MARK)] + MARK
    return text


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="Print compaction instructions for a Claude Code PreCompact hook.")
    ap.add_argument("--repo-root", default=".")
    a = ap.parse_args()
    if not sys.stdin.isatty():
        try:
            sys.stdin.read()  # 钩子的输入读掉就行（trigger / custom_instructions 由 Claude Code 自己用）
        except OSError:
            pass
    repo = Path(a.repo_root).resolve()
    if not project_living_path(repo, "config.yaml").exists():
        return 0  # 没装 AIP 的仓库不插话
    print(instructions(repo))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:  # 压缩不能因为这个钩子失败
        raise SystemExit(0)
