from __future__ import annotations
import argparse
from pathlib import Path
from _aip_common import force_utf8, project_living_path, read_text
from aip_knowledge import parse_entries
from aip_discovery import upsert_block

AUTO_BEGIN = "<!-- AIP:AUTO-DIGEST:BEGIN (勿手改) -->"
AUTO_END = "<!-- AIP:AUTO-DIGEST:END -->"

def top_headings(text: str, prefix: str) -> list[str]:
    results = []
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith(prefix):
            heading = line[len(prefix):].strip()
            if heading == "格式":
                continue
            if "<" in heading or ">" in heading:
                continue
            results.append(heading)
    return results

def _read(repo: Path, name: str) -> str:
    p = project_living_path(repo, name)
    return read_text(p) if p.exists() else ""

def build_digest(repo: Path) -> str:
    ks = parse_entries(_read(repo, "knowledge.md"))
    kn = "\n".join(f'- {e["id"]} {e["title"]} [{e["fields"].get("状态","")}]' for e in ks) or "- （空）"
    dec = "\n".join(f"- {h}" for h in top_headings(_read(repo, "decisions.md"), "## ")[-5:]) or "- （空）"
    ref = "\n".join(f"- {h}" for h in top_headings(_read(repo, "reference.md"), "### ")) or "- （空）"
    return (f"### 自动摘要（派生，勿手改）\n**知识（{len(ks)} 条）**\n{kn}\n\n"
            f"**近期决策**\n{dec}\n\n**核心概念**\n{ref}\n")

def rebuild_overview(repo: Path) -> Path:
    p = project_living_path(repo, "OVERVIEW.md")
    upsert_block(p, build_digest(repo), AUTO_BEGIN, AUTO_END)
    return p

def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="Rebuild OVERVIEW auto-digest.")
    ap.add_argument("--repo-root", required=True)
    print(f"OVERVIEW digest rebuilt: {rebuild_overview(Path(ap.parse_args().repo_root).resolve())}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
