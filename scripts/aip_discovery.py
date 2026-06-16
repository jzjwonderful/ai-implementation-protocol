from __future__ import annotations

from pathlib import Path

BEGIN = "<!-- BEGIN AIP (managed) -->"
END = "<!-- END AIP (managed) -->"

BLOCK_BODY = (
    "## AI Implementation Protocol\n"
    "本仓库用 AIP 管理实现工作。后续 AI 会话请先读：\n"
    "- `.aip/STATUS.md` 现状真理源\n"
    "- `.aip/_runtime/current_task.json` 当前任务指针 + must_read\n"
    "- `.aip/knowledge_index.md` 已沉淀真因索引（遇问题先查）\n"
    "命令：`$aip resume` 续作 / `$aip check` 校验 / 详见 `.aip/protocols/`。\n"
)


def managed_block() -> str:
    return f"{BEGIN}\n{BLOCK_BODY}{END}\n"


def upsert_managed_block(path: Path) -> None:
    """幂等写入托管块：不存在则建；有标记则只替换标记区；否则末尾追加。保持文件原换行。"""
    block = managed_block()
    if not path.exists():
        path.write_text(block, encoding="utf-8", newline="\n")
        return
    text = path.read_text(encoding="utf-8")
    if BEGIN in text and END in text:
        pre = text[: text.index(BEGIN)]
        post = text[text.index(END) + len(END):]
        new = pre + block.rstrip("\n") + post
    else:
        sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
        new = text + sep + block
    path.write_text(new, encoding="utf-8")
