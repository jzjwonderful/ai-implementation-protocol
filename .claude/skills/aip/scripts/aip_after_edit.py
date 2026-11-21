from __future__ import annotations

"""Claude Code PostToolUse 钩子入口（Edit / Write 之后）：把刚改的文件相关的条目摆出来。

「改代码前跑 aip_lookup.py relevant」原来全靠 AI 自觉，唯一的兜底是提交前钩子——那时候代码
已经写完了。这枚钩子在每次 Edit / Write 之后自动跑一次反查，结果走 additionalContext 进模型，
赶在下一轮动作之前。一个会话里同一个文件只提一次（按会话 id + 文件记在临时目录），不然连改
十次就刷十遍同样的内容。

输出必须是 Claude Code 认的 JSON，字段嵌在 hookSpecificOutput 里（放到顶层会被静默忽略）。
查不出东西就什么都不输出；出错也不出声，绝不挡住工具调用。
"""

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

from aip_lookup import pick, relevant

# 同一个会话里同一个文件只提一次：标记文件放临时目录，不往用户仓库里写东西
STATE_DIR = "aip-relevant"


def _seen(session: str, repo: Path, rel: str) -> bool:
    """这个会话里这个仓库的这个文件提过了吗（顺手记上）。临时目录不可写就当没提过。"""
    key = hashlib.sha1(f"{session}\0{repo.as_posix()}\0{rel}".encode("utf-8")).hexdigest()[:16]
    d = Path(tempfile.gettempdir()) / f"{STATE_DIR}-{hashlib.sha1(session.encode()).hexdigest()[:12]}"
    try:
        d.mkdir(parents=True, exist_ok=True)
        mark = d / key
        if mark.exists():
            return True
        mark.write_text("", encoding="utf-8")
    except OSError:
        return False
    return False


def context_for(repo: Path, rel: str) -> str:
    hits, broken = relevant(repo, [rel])
    if not hits and not broken:
        return ""
    lines = [f"AIP：刚改的 {rel} 相关的主题和条目（确认没踩到再继续；完整清单：aip_lookup.py relevant {rel} --all）："]
    lines += [h.line() for h in pick(hits)]
    if len(hits) > len(pick(hits)):
        lines.append(f"- ……还有 {len(hits) - len(pick(hits))} 条相关的（按轻重排在后面）")
    lines += [f"- 锚点断了：{b}" for b in broken]
    return "\n".join(lines)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    tool_input = data.get("tool_input") or {}
    path = str(tool_input.get("file_path") or "")
    repo = Path(data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()
    if not path or not (repo / ".aip" / "config.yaml").exists():
        return 0
    try:
        rel = Path(path).resolve().relative_to(repo).as_posix()
    except ValueError:
        return 0  # 改的是仓库外的文件
    if rel.startswith(".aip/") or _seen(str(data.get("session_id") or ""), repo, rel):
        return 0
    text = context_for(repo, rel)
    if text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}},
                         ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:  # 钩子不能挡住工具调用
        raise SystemExit(0)
