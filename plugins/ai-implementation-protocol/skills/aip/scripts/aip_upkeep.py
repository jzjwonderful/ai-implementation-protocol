from __future__ import annotations

"""到期提醒：活文档里哪些内容该复核了。

只提醒、不挡提交——日子到了不是错误，放着不管才是。会话开始（SessionStart 钩子）
和 aip check 都会打印，让 AI 在用到这些条目、或当前任务收尾时顺手复核。
"""

import argparse
import re
from datetime import date
from pathlib import Path

from _aip_common import force_utf8, project_living_path, read_text
from aip_knowledge import parse_entries

KNOWLEDGE_STALE_DAYS = 90
FULL_REVIEW_DAYS = 30
# 知识条目的状态只用这几个词开头；后面可以跟括号补一句说明。
STATUS_WORDS = ("active", "draft", "fixed", "superseded")
LIST_LIMIT = 8

DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
REVIEW_KEY_RE = re.compile(r"^review_last_full:\s*[\"']?([^\"'#\s]*)", re.M)


def parse_day(value: str) -> date | None:
    m = DATE_RE.match(value.strip())
    if not m:
        return None
    try:
        return date.fromisoformat(m.group(1))
    except ValueError:
        return None


def status_word(value: str) -> str:
    """状态字段的第一个词（小写），比如「fixed（已修，2026-06-28）」→ fixed。"""
    m = re.match(r"[A-Za-z]+", value.strip())
    return m.group(0).lower() if m else ""


def last_full_review(repo: Path) -> tuple[bool, date | None]:
    """返回（config.yaml 里有没有这个键, 日期）。"""
    cfg = project_living_path(repo, "config.yaml")
    if not cfg.exists():
        return False, None
    m = REVIEW_KEY_RE.search(read_text(cfg))
    if not m:
        return False, None
    return True, parse_day(m.group(1))


def _ids(ids: list[str]) -> str:
    shown = "、".join(ids[:LIST_LIMIT])
    return shown + (f" 等 {len(ids)} 条" if len(ids) > LIST_LIMIT else "")


def reminders(repo: Path, today: date | None = None) -> list[str]:
    today = today or date.today()
    out: list[str] = []

    kn = project_living_path(repo, "knowledge.md")
    stale: list[str] = []
    drafts: list[str] = []
    if kn.exists():
        for e in parse_entries(read_text(kn)):
            word = status_word(e["fields"].get("状态", ""))
            if word == "draft":
                drafts.append(e["id"])
            elif word == "active":
                seen = parse_day(e["fields"].get("最后复核", ""))
                if seen is None or (today - seen).days > KNOWLEDGE_STALE_DAYS:
                    stale.append(e["id"])
    if stale:
        out.append(
            f"知识 {len(stale)} 条超过 {KNOWLEDGE_STALE_DAYS} 天没复核：{_ids(stale)}。"
            "对照现状重验：仍成立就更新「最后复核」；缺陷已修改 fixed；被新机制取代标 superseded(by K-N)。"
        )
    if drafts:
        out.append(f"知识 {len(drafts)} 条还是 draft：{_ids(drafts)}。补齐证据改 active，证伪就删。")

    has_key, last = last_full_review(repo)
    if not has_key or last is None:
        out.append(
            "config.yaml 没记上次整份 review 的日期（review_last_full）："
            "做一次整份 .aip/ review（aip 技能 reference/review-checklist.md），做完写上当天日期。"
        )
    elif (today - last).days > FULL_REVIEW_DAYS:
        out.append(
            f"距上次整份 .aip/ review 已 {(today - last).days} 天（review_last_full: {last.isoformat()}）："
            "按 aip 技能 reference/review-checklist.md 做一次，做完把日期改成当天。"
        )
    return out


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="List AIP living-doc items due for review (never fails).")
    ap.add_argument("--repo-root", required=True)
    a = ap.parse_args()
    items = reminders(Path(a.repo_root).resolve())
    for line in items:
        print(f"- {line}")
    if not items:
        print("没有到期要复核的内容。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
