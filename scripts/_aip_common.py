from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REQUIRED_FEATURE_FILES = [
    "spec.md",
    "plan.md",
    "task_board.yaml",
    "file_scope.yaml",
    "handoff.md",
    "verification.md",
    "session_log.md",
]


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


def feature_dir(target_repo: Path, feature_id: str) -> Path:
    return target_repo / "project_docs" / "features" / feature_id


def current_task_path(target_repo: Path) -> Path:
    return target_repo / "project_docs" / "_runtime" / "current_task.json"


def protocol_path(target_repo: Path) -> Path:
    return target_repo / "project_docs" / "protocols" / "ai-implementation-protocol.md"


def project_docs_root(target_repo: Path) -> Path:
    return target_repo / "project_docs"


def list_missing(paths: Iterable[Path]) -> list[str]:
    return [str(p) for p in paths if not p.exists()]
