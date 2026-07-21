from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def force_utf8() -> None:
    """让中文输出在各终端/git 钩子里不乱码（默认编码常是 cp936 等非 UTF-8）。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass


# 业务仓库里 AIP 的全部产出都落在这个隐藏目录下（像 .git/.nexus-map），不污染项目根。
AIP_DIR = ".aip"

# 项目级活文档（跨 feature，长期存在）。init 生成、check 校验存在。
PROJECT_LIVING_FILES = [
    "OVERVIEW.md", "decisions.md", "knowledge.md", "knowledge_index.md",
    "reference.md", "inbox.md", "conventions.md", "config.yaml",
]

# 不该出现在仓库任何地方的文件名：旧 per-feature 接管残留 + 已被取代的旧文档名（迁移守卫）。
FORBIDDEN_SLOT_FILENAMES = [
    "current_task.json", "task_board.yaml", "handoff.md", "verification.md",
    "session_log.md", "report.md", "file_scope.yaml",
    "STATUS.md", "findings.md", "canonical-assets.md",
]

# knowledge.md 每条目必填字段（check 校验）。
REQUIRED_KNOWLEDGE_FIELDS = ["分类", "状态", "症状", "根因", "适用范围", "最后复核"]

# 插件包携带的全部技能（plugins/.../skills/ 下应有同名目录）。
# 安装器按目录遍历不读这个清单；doctor/uninstall 靠它逐个点名，新增技能只改这里。
SKILL_NAMES = ["aip", "root-cause", "aip-brainstorm"]

# 扫描"无并行产物"时跳过的重目录。
SCAN_PRUNE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "dist", "build",
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


def project_living_path(target_repo: Path, name: str) -> Path:
    return aip_root(target_repo) / name


# 向后兼容旧调用名（现在指向 .aip 根）。
def project_docs_root(target_repo: Path) -> Path:
    return aip_root(target_repo)


def list_missing(paths: Iterable[Path]) -> list[str]:
    return [str(p) for p in paths if not p.exists()]
