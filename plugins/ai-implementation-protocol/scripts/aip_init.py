from __future__ import annotations

import argparse
from pathlib import Path

from _aip_common import (
    AIP_DIR,
    PROJECT_LIVING_FILES,
    aip_root,
    ensure_dir,
    project_living_path,
    protocol_path,
    write_json,
    write_text,
)


# 项目级活文档 → 生成它用哪个模板。
LIVING_TEMPLATE_MAP = {
    "STATUS.md": "status-template.md",
    "canonical-assets.md": "canonical-assets-template.md",
    "decisions.md": "decisions-template.md",
    "findings.md": "findings-template.md",
    "config.yaml": "config-template.yaml",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize AIP in a target repository.")
    parser.add_argument("--repo-root", required=True, help="Target project root.")
    parser.add_argument(
        "--template-root",
        default=Path(__file__).resolve().parents[1],
        help="AIP repository root. Defaults to this script's repository.",
    )
    parser.add_argument("--force", action="store_true", help="覆盖已存在的项目级活文档。")
    args = parser.parse_args()

    target_repo = Path(args.repo_root).resolve()
    template_root = Path(args.template_root).resolve()

    root = aip_root(target_repo)
    ensure_dir(root / "_runtime")
    ensure_dir(root / "features")
    ensure_dir(root / "protocols")

    write_text(protocol_path(target_repo), (template_root / "docs" / "protocol.md").read_text(encoding="utf-8"))

    # 项目级活文档：已存在则保留（除非 --force），避免覆盖用户内容。
    for name in PROJECT_LIVING_FILES:
        dest = project_living_path(target_repo, name)
        if dest.exists() and not args.force:
            continue
        tpl = template_root / "templates" / LIVING_TEMPLATE_MAP[name]
        write_text(dest, tpl.read_text(encoding="utf-8"))

    current_task = {
        "feature_id": "",
        "status": "planned",
        "current_phase": "spec",
        "current_task": "",
        "next_action": "",
        "last_updated": "",
        "owner": "ai",
        "blocking": [],
        "must_read": [
            f"{AIP_DIR}/protocols/ai-implementation-protocol.md",
            f"{AIP_DIR}/STATUS.md",
        ],
    }
    write_json(root / "_runtime" / "current_task.json", current_task)
    write_json(root / "_runtime" / "current_task.template.json", current_task)

    readme = (
        "# .aip\n\n"
        "本目录由 AIP 初始化生成，存放该仓库 AIP 机制的全部产出（隐藏工具目录，类比 .git）。\n\n"
        "- `STATUS.md`：现状真理源（实现到哪/缺口/部署）——新会话先读这页\n"
        "- `canonical-assets.md`：正典构件登记（造新前先查，防堆积）\n"
        "- `decisions.md`：架构决策记录（ADR-lite，append-only）\n"
        "- `findings.md`：侧发现收件箱（开发时撞见的无关问题，捕获别追）\n"
        "- `config.yaml`：本项目适配配置（真理源/机器闸门命令/适用 lens）\n"
        "- `_runtime/`：当前任务指针\n"
        "- `features/`：功能工作包\n"
        "- `protocols/`：项目内协议副本\n"
    )
    write_text(root / "README.md", readme)

    print(f"AIP initialized in: {target_repo / AIP_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
