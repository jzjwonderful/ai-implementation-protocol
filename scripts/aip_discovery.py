from __future__ import annotations

from pathlib import Path

BEGIN = "<!-- BEGIN AIP (managed) -->"
END = "<!-- END AIP (managed) -->"

BLOCK_BODY = (
    "## AI Implementation Protocol\n"
    "**会话开始时必须先调用 `aip` 技能，再做任何其他事（包括回答问题）。**\n"
    "调完技能后读 `.aip/OVERVIEW.md`（当前在建线）；遇问题先查 `.aip/knowledge.md`。\n"
    "其余按需查：`decisions.md` 架构决策 / `reference.md` 核心概念+复用件 / `inbox.md` 旁路问题 / `conventions.md` 规约。\n"
    "语言一律大白话，禁止黑话。\n"
)


def upsert_block(path: Path, body: str, begin: str, end: str) -> None:
    """幂等写入标记块：无文件则建；有标记则只替换标记区；否则末尾追加。"""
    block = f"{begin}\n{body}{end}\n"
    if not path.exists():
        path.write_text(block, encoding="utf-8", newline="\n"); return
    text = path.read_text(encoding="utf-8")
    if begin in text and end in text:
        new = text[: text.index(begin)] + block.rstrip("\n") + text[text.index(end) + len(end):]
    else:
        sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
        new = text + sep + block
    path.write_text(new, encoding="utf-8", newline="\n")

def managed_block() -> str:
    return f"{BEGIN}\n{BLOCK_BODY}{END}\n"

def upsert_managed_block(path: Path) -> None:
    upsert_block(path, BLOCK_BODY, BEGIN, END)
