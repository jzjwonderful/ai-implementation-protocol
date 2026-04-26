from __future__ import annotations

import argparse
from pathlib import Path

from _aip_common import ensure_dir, load_template, project_docs_root, protocol_path, write_json, write_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize AIP in a target repository.")
    parser.add_argument("--repo-root", required=True, help="Target project root.")
    parser.add_argument(
        "--template-root",
        default=Path(__file__).resolve().parents[1],
        help="AIP repository root. Defaults to this script's repository.",
    )
    args = parser.parse_args()

    target_repo = Path(args.repo_root).resolve()
    template_root = Path(args.template_root).resolve()

    docs_root = project_docs_root(target_repo)
    ensure_dir(docs_root / "_runtime")
    ensure_dir(docs_root / "features")
    ensure_dir(docs_root / "protocols")

    write_text(protocol_path(target_repo), (template_root / "docs" / "protocol.md").read_text(encoding="utf-8"))

    current_task = {
        "feature_id": "",
        "status": "planned",
        "current_phase": "spec",
        "current_task": "",
        "next_action": "",
        "last_updated": "",
        "owner": "ai",
        "blocking": [],
        "must_read": ["project_docs/protocols/ai-implementation-protocol.md"],
    }
    write_json(docs_root / "_runtime" / "current_task.json", current_task)
    write_json(docs_root / "_runtime" / "current_task.template.json", current_task)

    readme = """# 项目文档\n\n本目录由 AIP 初始化生成。\n\n- `_runtime/`：当前任务指针\n- `features/`：功能工作包\n- `protocols/`：项目内协议副本\n"""
    write_text(docs_root / "README.md", readme)

    print(f"AIP initialized in: {target_repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
