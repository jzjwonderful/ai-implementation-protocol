from __future__ import annotations

"""Claude Code SessionStart 钩子入口：打印看板，外加检出状态、更新和到期提醒。

看板直接从目录读：在建线全文、待处理旁路问题的文件名。不另存文件——存下来的看板
没人刷新就会过期。知识、决策不列，用到时按文件名查。

钩子从 stdin 收到 JSON，其中 source 是 startup / resume / clear / compact / fork。
compact 表示上下文刚被压缩成摘要——这时 AI 的记忆最不可靠，所以除了打印看板，
还要明说"以看板为准、没写回的进展先补"。压缩前的钩子（PreCompact）输出到不了模型，
所以补救只能放在压缩之后这一刻。
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from _aip_common import AIP_DIR, OLD_LAYOUT_FILES, force_utf8, project_living_path, py_cmd, read_text, remove_old_board
from aip_item import TYPES, list_items
from aip_update import update_notice
from aip_upkeep import reminders


INBOX_LIMIT = 10


def board(repo: Path) -> str:
    # 旧版本留下的 _done_ 文件不算在建（aip_check 会让删掉）
    tracks = [t for t in list_items(repo, "track") if t.status in TYPES["track"].statuses]
    lines = ["## 在建线（.aip/tracks/）"]
    lines += [f"### {t.path.name}\n{t.body.strip()}" for t in tracks] or ["（没有）"]
    inbox = [i for i in reversed(list_items(repo, "inbox")) if i.status == "open"]
    lines.append(f"## 待处理的旁路问题（.aip/inbox/ 下 {len(inbox)} 条 open，新的在前）")
    lines += [f"- {i.path.name}" for i in inbox[:INBOX_LIMIT]] or ["（没有）"]
    if len(inbox) > INBOX_LIMIT:
        lines.append(f"- ……还有 {len(inbox) - INBOX_LIMIT} 条：aip_item.py list --type inbox --status open")
    lines.append("知识、决策按文件名查：ls .aip/knowledge | grep 关键词，或 aip_item.py list --grep 关键词")
    return "\n".join(lines)


def read_source() -> str:
    try:
        return str(json.load(sys.stdin).get("source", ""))
    except (ValueError, OSError, AttributeError):
        return ""


def banner(source: str) -> str:
    if source == "compact":
        return ("=== AIP：上下文刚被压缩，摘要可能丢细节。下面的在建线是当前状态的权威来源；"
                "如果压缩前有进展还没写回在建线文件，先补写再继续。===")
    return "=== AIP 看板 ==="


def _git(repo: Path, args: list[str]) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=10, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def checkout_notes(repo: Path) -> list[str]:
    """写 .aip/ 之前该知道的检出状态。只看本机已有的远端记录，不联网。

    在落后远端的检出里写条目、写完又不提交，是真实项目里条目丢失的原因。
    """
    notes = []
    upstream = _git(repo, ["rev-parse", "--abbrev-ref", "@{upstream}"])
    behind = _git(repo, ["rev-list", "--count", "HEAD..@{upstream}"]) if upstream else None
    if behind and behind.isdigit() and int(behind) > 0:
        notes.append(f"当前检出落后 {upstream} {behind} 个提交（按本机上次拉取的记录）：写 .aip/ 前先同步")
    # 逐个文件列：不加的话整个没进版本库的目录只算一行
    dirty = _git(repo, ["status", "--porcelain", "--untracked-files=all", "--", AIP_DIR])
    if dirty:
        n = len(dirty.splitlines())
        notes.append(f".aip/ 下有 {n} 个文件的改动没提交：先确认是不是上次会话留下的，该提交就提交")
    return notes


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="Print the AIP board for a Claude Code SessionStart hook.")
    ap.add_argument("--repo-root", default=".")
    a = ap.parse_args()
    repo = Path(a.repo_root).resolve()
    if not project_living_path(repo, "config.yaml").exists():
        print("AIP：项目尚未初始化（无 .aip/config.yaml）。需要时跑 aip init。")
        return 0
    source = read_source()
    if any(project_living_path(repo, n).exists() for n in OLD_LAYOUT_FILES):
        old = project_living_path(repo, "OVERVIEW.md")
        print("=== AIP：这个仓库的 .aip/ 还是旧格式，先跟用户说一声，同意后按 aip 技能的 /aip migrate 迁移 ===")
        if old.exists():
            print(read_text(old))
        return 0
    remove_old_board(repo)
    print(banner(source))
    print(board(repo))
    # 钩子命令已经挑出一个 3.9 以上的解释器；告诉 AI，本会话跑 AIP 脚本都用它，不用再猜 python3 还是 python
    print(f"跑 AIP 脚本用这个解释器（会话开始钩子探测到的）：{py_cmd()}")
    print("===================")
    # 压缩后正在干活，不拿检出状态、更新和复核提醒打断；新会话 / 恢复会话才提。
    if source == "compact":
        return 0
    notes = checkout_notes(repo)
    if notes:
        print("=== AIP 检出状态 ===")
        for line in notes:
            print(f"- {line}")
    notice = update_notice(repo)  # 查不了就是 None，不出声
    if notice:
        print(f"=== AIP 有更新 ===\n- {notice}")
    try:
        due = reminders(repo)
    except Exception:  # 提醒出错不能挡住会话开始
        due = []
    if due:
        print("=== AIP 到期提醒：用到这些条目时顺手复核，或在当前任务收尾时处理；要延后就跟用户说一声 ===")
        for line in due:
            print(f"- {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
