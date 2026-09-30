from __future__ import annotations

"""生成看板 `.aip/OVERVIEW.md`：在建线、待处理的旁路问题、知识概况、近期决策、参照。

看板完全由条目文件派生，不进仓库（init 把它写进 .aip/.gitignore）：
进了仓库，并行分支每次合并都会在这里冲突。要改看板就改 `tracks/` 下的文件。
每一节都封顶，条目再多看板也不会越长越大——全量用 `aip_item.py list` 看。
"""

import argparse
import re
from pathlib import Path

from _aip_common import force_utf8, project_living_path, read_text, write_text
from aip_item import Item, TYPES, list_items

INBOX_LIMIT = 10
RECENT_LIMIT = 5
TRACK_MARK = {"active": "▶", "blocked": "⛔", "paused": "⏸"}

TABLE_RULE = re.compile(r"^\|[\s:|-]+\|?$")


def reference_sections(text: str) -> list[str]:
    """reference.md 每个二级节有几条：表格数据行、列表项、三级标题各算一条。

    模板用表格写术语和可复用实现，只数三级标题会让摘要永远是空的。
    表头、分隔行、占位（「<例：…>」「<暂无>」这类尖括号开头的）都不算。
    """
    sections: list[list] = []
    in_fence = False
    prev_table = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        s = line.strip()
        is_table = s.startswith("|")
        header = is_table and not prev_table
        prev_table = is_table
        if line.startswith("## "):
            sections.append([line[3:].strip(), 0])
            continue
        if not sections or s.lstrip("-|# ").startswith("<") or header or TABLE_RULE.match(s):
            continue
        if is_table or line.startswith("### ") or line.startswith("- "):
            sections[-1][1] += 1
    return [f"{name}（{n}）" for name, n in sections if n > 0]


def _line(i: Item) -> str:
    return f"- {i.title} — `{i.id}`"


def _tracks(items: list[Item]) -> str:
    live = [t for t in items if t.status in TRACK_MARK]
    live.sort(key=lambda t: list(TRACK_MARK).index(t.status))
    if not live:
        return "（当前没有在建线）\n"
    return "\n".join(f"### {TRACK_MARK[t.status]} {t.title}  [{t.status}]\n`{t.path.parent.name}/{t.path.name}`\n\n"
                     f"{t.body.strip()}\n" for t in live)


def _capped(items: list[Item], limit: int, more: str) -> str:
    if not items:
        return "（无）\n"
    lines = [_line(i) for i in items[:limit]]
    if len(items) > limit:
        lines.append(f"- ……还有 {len(items) - limit} 条，全部：{more}")
    return "\n".join(lines) + "\n"


def _recent_knowledge(items: list[Item]) -> list[Item]:
    def touched(i: Item) -> str:
        return max(i.created.isoformat(), i.meta.get("last_reviewed", ""))
    live = [i for i in items if i.status in ("active", "draft")]
    return sorted(live, key=touched, reverse=True)


def build_overview(repo: Path) -> str:
    by_type = {t: list_items(repo, t) for t in TYPES}
    knowledge = by_type["knowledge"]
    counts = " / ".join(f"{s} {sum(i.status == s for i in knowledge)}" for s in TYPES["knowledge"].statuses)
    inbox = [i for i in by_type["inbox"] if i.status == "open"]
    inbox.sort(key=lambda i: i.stamp, reverse=True)
    decisions = [d for d in by_type["decision"] if d.status == "accepted"]
    decisions.sort(key=lambda d: d.stamp, reverse=True)
    ref = project_living_path(repo, "reference.md")
    ref_lines = "\n".join(f"- {h}" for h in reference_sections(read_text(ref) if ref.exists() else "")) or "- （空）"
    return (
        "# 总览（自动生成，勿手改）\n\n"
        "> 由 aip 技能的 `aip_overview.py` 从 `.aip/` 下的条目生成，不进仓库。"
        "要改在建线就改 `.aip/tracks/` 下的文件，改状态用 `aip_item.py status`。\n\n"
        f"## 在建\n{_tracks(by_type['track'])}\n"
        f"## 待处理的旁路问题（{len(inbox)} 条）\n"
        f"{_capped(inbox, INBOX_LIMIT, 'aip_item.py list --type inbox --status open')}\n"
        f"## 知识（{counts}）\n最近新增或复核的：\n"
        f"{_capped(_recent_knowledge(knowledge), RECENT_LIMIT, 'aip_item.py list --type knowledge')}\n"
        f"## 近期决策\n{_capped(decisions, RECENT_LIMIT, 'aip_item.py list --type decision --status accepted')}\n"
        f"## 参照（`.aip/reference.md`，括号里是条数）\n{ref_lines}\n"
    )


def rebuild_overview(repo: Path) -> Path:
    p = project_living_path(repo, "OVERVIEW.md")
    write_text(p, build_overview(repo))
    return p


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="Rebuild .aip/OVERVIEW.md from the item files.")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--print", dest="do_print", action="store_true", help="重建后把看板输出到 stdout")
    a = ap.parse_args()
    p = rebuild_overview(Path(a.repo_root).resolve())
    print(read_text(p) if a.do_print else f"看板已重建: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
