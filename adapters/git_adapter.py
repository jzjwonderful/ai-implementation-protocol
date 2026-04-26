from __future__ import annotations

from pathlib import Path


def detect_git_repo(repo_root: str | Path) -> bool:
    return (Path(repo_root).resolve() / ".git").exists()
