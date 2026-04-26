from __future__ import annotations

from pathlib import Path


def detect_nexus_map(repo_root: str | Path) -> Path | None:
    path = Path(repo_root).resolve() / ".nexus-map" / "INDEX.md"
    return path if path.exists() else None
