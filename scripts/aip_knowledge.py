from __future__ import annotations

import argparse
import re
from pathlib import Path

from _aip_common import project_living_path, read_text, write_text

INDEX_HEADER = (
    "# 知识索引（自动生成，勿手改；运行 `aip knowledge` 重建）\n"
    "# 格式: ID | 分类 | 状态 | 标题 | 最后复核\n"
)

ENTRY_RE = re.compile(r"^## (K-\d+):\s*(.*)$")
FIELD_RE = re.compile(r"^- (\S+?):\s*(.*)$")


def parse_categories(text: str) -> list[str]:
    """读取顶部 '## 类目' 区声明的合法类目集。"""
    cats: list[str] = []
    capturing = False
    for line in text.splitlines():
        s = line.strip()
        if s == "## 类目":
            capturing = True
            continue
        if capturing and s.startswith("## "):
            break
        if capturing and s and not s.startswith("#"):
            cats.extend(t for t in re.split(r"[|,，\s]+", s) if t)
    return cats


def parse_entries(text: str) -> list[dict]:
    """解析所有 '## K-NNN: 标题' 条目及其 '- 字段: 值'。"""
    entries: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        s = line.strip()
        m = ENTRY_RE.match(s)
        if m:
            if cur:
                entries.append(cur)
            cur = {"id": m.group(1), "title": m.group(2).strip(), "fields": {}}
            continue
        if cur:
            fm = FIELD_RE.match(s)
            if fm:
                cur["fields"][fm.group(1)] = fm.group(2).strip()
    if cur:
        entries.append(cur)
    return entries


def render_index(entries: list[dict]) -> str:
    lines = [INDEX_HEADER]
    for e in entries:
        f = e["fields"]
        lines.append(
            f'{e["id"]} | {f.get("分类", "")} | {f.get("状态", "")} | {e["title"]} | {f.get("最后复核", "")}'
        )
    return "\n".join(lines).rstrip() + "\n"


def expected_index_text(target_repo: Path) -> str:
    kn = project_living_path(target_repo, "knowledge.md")
    text = read_text(kn) if kn.exists() else ""
    return render_index(parse_entries(text))


def rebuild_index(target_repo: Path) -> Path:
    dst = project_living_path(target_repo, "knowledge_index.md")
    write_text(dst, expected_index_text(target_repo))
    return dst


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild the AIP knowledge index from knowledge.md.")
    parser.add_argument("--repo-root", required=True, help="Target project root.")
    args = parser.parse_args()
    dst = rebuild_index(Path(args.repo_root).resolve())
    print(f"Knowledge index rebuilt: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
