from __future__ import annotations

from pathlib import Path

BEGIN = "<!-- BEGIN AIP (managed) -->"
END = "<!-- END AIP (managed) -->"
# 只是写进托管块的版本戳，给人/doctor 看装的是第几版；不参与"要不要升级"的判断。
# upsert 每次都把标记区整块重写，块内容一变就必刷新——不靠版本号比对，
# 省得"改了内容却忘 bump 版本号"导致该升级的没升级。
MANAGED_VERSION = "3"

BLOCK_BODY = (
    f"<!-- AIP managed version: {MANAGED_VERSION} -->\n"
    "## AI Implementation Protocol\n"
    "**会话开始时必须先调用 `aip` 技能，再做任何其他事（包括回答问题）。**\n"
    "调完技能后读 `.aip/OVERVIEW.md`（自动生成的看板：在建线、待处理问题、知识概况）；没有这个文件就用技能里的 `aip_overview.py` 生成。\n"
    "条目一条一个文件，文件名是 `时间戳_类型_状态_简述.md`：`.aip/knowledge/` 验证过的坑和根因、`decisions/` 架构决策、"
    "`inbox/` 旁路问题、`tracks/` 在建线。先按文件名或 `aip_item.py list` 找相关的，再打开读，不要通读整个目录；"
    "新建、改状态走 `aip_item.py`，引用别的条目写完整的「时间戳_简述」。\n"
    "其余按需查：`reference.md` 核心概念+复用件 / `conventions.md` 规约。\n"
    "编码任务开始前先读懂项目验证机制，并建立“plan/需求 → 实现位置 → 行为证据”的验收矩阵；完成前逐项核对。\n"
    "不能只凭 build/lint 通过宣布功能完成，也不得通过删除、跳过或削弱测试绕过约束；未闭环时必须说明未验证项和风险。\n"
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
