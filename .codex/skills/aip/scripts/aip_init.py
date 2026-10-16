from __future__ import annotations
import argparse
from datetime import date
from pathlib import Path
from _aip_common import (
    OLD_LAYOUT_FILES, PROJECT_FILES, TOPIC_DIR, aip_root, ensure_dir, force_utf8, load_template,
    project_living_path, read_text, remove_old_board, write_text,
)
from aip_discovery import BEGIN, upsert_managed_block
from aip_item import TYPES, type_dir

# 整篇文档名 → 模板名。零配置：不向用户索取工程信息。
TEMPLATE_OF = {
    "conventions.md": "conventions-template.md",
    "config.yaml": "config-template.yaml",
}
# 空目录进不了 git，放个占位文件让条目目录随仓库走
KEEP_FILE = ".gitkeep"

def scaffold(repo: Path, engine_root: Path) -> list[Path]:
    root = aip_root(repo); ensure_dir(root)
    created = []
    for name in PROJECT_FILES:
        dst = root / name
        if dst.exists():
            continue  # 幂等：不覆盖
        text = load_template(engine_root, TEMPLATE_OF[name])
        if name == "config.yaml":
            # 新建即从零开始：今天记为上次整份 review，按当前版本的模板建的也不用再做升级调整
            version = read_text(engine_root / "VERSION").strip()
            text = (text.replace('review_last_full: ""', f'review_last_full: "{date.today().isoformat()}"')
                        .replace('aip_version: ""', f'aip_version: "{version}"'))
        write_text(dst, text)
        created.append(dst)
    # 主题文件不预建：有内容时 AI 按 templates/topic-template.md 写，空文件只会占目录
    for keep in [type_dir(repo, t) / KEEP_FILE for t in TYPES] + [root / TOPIC_DIR / KEEP_FILE]:
        if not keep.exists() and not (keep.parent.is_dir() and any(keep.parent.iterdir())):
            write_text(keep, "")
            created.append(keep)
    remove_old_board(repo)
    return created

def guide_files(repo: Path) -> list[str]:
    """要写托管块的说明文件。CLAUDE.md 只是引用 AGENTS.md（写了 `@AGENTS.md`）时不写它：
    托管块在 AGENTS.md 里，Claude Code 读 CLAUDE.md 时会一起读进来，再写一份就重复了。"""
    claude = repo / "CLAUDE.md"
    if claude.is_file():
        text = read_text(claude)
        if BEGIN not in text and any(l.strip() == "@AGENTS.md" for l in text.splitlines()):
            return ["AGENTS.md"]
    return ["CLAUDE.md", "AGENTS.md"]

def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="Init AIP into a repo (zero-config).")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--engine-root", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--no-hooks", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo_root).resolve(); engine = Path(a.engine_root).resolve()
    old = [n for n in OLD_LAYOUT_FILES if project_living_path(repo, n).exists()]
    if old:
        print(f"这个仓库的 .aip/ 还是旧格式（{'、'.join(old)}）：先跑 {engine.as_posix()}/scripts/aip_migrate.py 迁移，再 init。")
        return 1
    scaffold(repo, engine)
    for guide in guide_files(repo):
        upsert_managed_block(repo / guide)
    if not a.no_hooks and (repo / ".git").exists():
        import install_hooks
        try:
            install_hooks.install_pre_commit(repo, engine, force=False)
        except SystemExit as e:
            # 项目已有非 AIP 的 pre-commit 钩子：不覆盖、不中断 init，提示人自行处理。
            print(f"（跳过 pre-commit 钩子：{e}）")
        install_hooks.install_claude_session_start(repo, engine)
    print("AIP 已初始化（零配置）。工程信息将在用到时自动捕获，不在此追问。")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
