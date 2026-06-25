from __future__ import annotations
import argparse
from pathlib import Path
from _aip_common import PROJECT_LIVING_FILES, aip_root, ensure_dir, load_template, write_text
from aip_discovery import upsert_managed_block

# 活文档名 → 模板名（无模板的建空骨架）。零配置：不向用户索取工程信息。
TEMPLATE_OF = {
    "OVERVIEW.md": "overview-template.md",
    "decisions.md": "decisions-template.md",
    "knowledge.md": "knowledge-template.md",
    "reference.md": "reference-template.md",
    "inbox.md": "inbox-template.md",
    "conventions.md": "conventions-template.md",
    "config.yaml": "config-template.yaml",
}

def scaffold(repo: Path, engine_root: Path) -> list[Path]:
    root = aip_root(repo); ensure_dir(root); ensure_dir(root / "protocols")
    created = []
    for name in PROJECT_LIVING_FILES:
        dst = root / name
        if dst.exists():
            continue  # 幂等：不覆盖
        if name == "knowledge_index.md":
            write_text(dst, "# 知识索引（自动生成，勿手改）\n")
        else:
            tpl = TEMPLATE_OF.get(name)
            write_text(dst, load_template(engine_root, tpl) if tpl else "")
        created.append(dst)
    return created

def main() -> int:
    ap = argparse.ArgumentParser(description="Init AIP into a repo (zero-config).")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--engine-root", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--no-hooks", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo_root).resolve(); engine = Path(a.engine_root).resolve()
    scaffold(repo, engine)
    for guide in ["CLAUDE.md", "AGENTS.md"]:
        upsert_managed_block(repo / guide)
    if not a.no_hooks and (repo / ".git").exists():
        import install_hooks
        install_hooks.install_pre_commit(repo, engine, force=False)
    print("AIP 已初始化（零配置）。工程信息将在用到时自动捕获，不在此追问。")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
