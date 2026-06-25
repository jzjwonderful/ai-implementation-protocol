from __future__ import annotations

from pathlib import Path

BEGIN = "<!-- BEGIN AIP (managed) -->"
END = "<!-- END AIP (managed) -->"

BLOCK_BODY = (
    "## AI Implementation Protocol\n"
    "本仓库用 AIP 管理实现工作（机制见 `.aip/protocols/`）。需要时去 `.aip/` 找：\n"
    "- `OVERVIEW.md` 现状/在建（开始或接手任务前先读）\n"
    "- `knowledge.md`(+`knowledge_index.md`) 验证过的坑（遇问题先查）\n"
    "- `decisions.md` 为什么这么定 / `reference.md` 这工程是什么+该复用什么\n"
    "- `inbox.md` 旁路问题 / `conventions.md` 项目规约\n"
    "AIP 动作由 AI 按时机自主触发；语言一律大白话，禁止黑话。\n"
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
    path.write_text(new, encoding="utf-8")

def managed_block() -> str:
    return f"{BEGIN}\n{BLOCK_BODY}{END}\n"

def upsert_managed_block(path: Path) -> None:
    upsert_block(path, BLOCK_BODY, BEGIN, END)
