from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


# 业务仓库里 AIP 的全部产出都落在这个隐藏目录下（像 .git/.nexus-map），不污染项目根。
AIP_DIR = ".aip"

REQUIRED_FEATURE_FILES = [
    "spec.md",
    "plan.md",
    "task_board.yaml",
    "file_scope.yaml",
    "handoff.md",
    "verification.md",
    "session_log.md",
]

# 项目级活文档（跨 feature，长期存在）。init 生成、check 校验存在。
PROJECT_LIVING_FILES = [
    "STATUS.md",
    "canonical-assets.md",
    "decisions.md",
    "findings.md",
    "knowledge.md",
    "knowledge_index.md",
    "config.yaml",
]

# AIP 的"槽位"文件名。这些只允许出现在 .aip/ 内；出现在别处 = 状态漂移/并行产物。
AIP_SLOT_FILENAMES = [
    "current_task.json",
    "task_board.yaml",
    "handoff.md",
    "verification.md",
    "session_log.md",
]

# 扫描"无并行产物"时跳过的重目录。
SCAN_PRUNE_DIRS = {
    ".git", ".aip", "node_modules", ".venv", "venv", "dist", "build",
    "__pycache__", ".pytest_cache", "bin", "obj", "packages", ".idea", ".vscode",
}


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def repo_path(path: str | Path) -> Path:
    return Path(path).resolve()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8", newline="\n")


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def load_template(repo_root: Path, name: str) -> str:
    template_path = repo_root / "templates" / name
    return read_text(template_path)


def aip_root(target_repo: Path) -> Path:
    return target_repo / AIP_DIR


def feature_dir(target_repo: Path, feature_id: str) -> Path:
    return aip_root(target_repo) / "features" / feature_id


def current_task_path(target_repo: Path) -> Path:
    return aip_root(target_repo) / "_runtime" / "current_task.json"


def protocol_path(target_repo: Path) -> Path:
    return aip_root(target_repo) / "protocols" / "ai-implementation-protocol.md"


def project_living_path(target_repo: Path, name: str) -> Path:
    return aip_root(target_repo) / name


# 向后兼容旧调用名（现在指向 .aip 根）。
def project_docs_root(target_repo: Path) -> Path:
    return aip_root(target_repo)


def list_missing(paths: Iterable[Path]) -> list[str]:
    return [str(p) for p in paths if not p.exists()]
