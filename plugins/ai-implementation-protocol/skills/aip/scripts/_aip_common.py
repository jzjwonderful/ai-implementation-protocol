from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def force_utf8() -> None:
    """让中文输出在各终端/git 钩子里不乱码（默认编码常是 cp936 等非 UTF-8）。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass


# 业务仓库里 AIP 的全部产出都落在这个隐藏目录下（像 .git/.nexus-map），不污染项目根。
AIP_DIR = ".aip"

# 项目级整篇文档（长期存在、整篇维护）。init 生成、check 校验存在。
# 知识、决策、旁路问题、在建线是一条一个文件，放在各自目录下，见 aip_item.TYPES。
PROJECT_FILES = ["reference.md", "conventions.md", "config.yaml"]

# 现场生成、不进仓库的文件（init 写进 .aip/.gitignore）。进了仓库，并行分支每次合并都会冲突。
GENERATED_FILES = ["OVERVIEW.md"]

# 0.5.0 之前「一类一个大文件」的布局。还在就说明没迁移，check 报红并指向迁移脚本。
OLD_LAYOUT_FILES = ["knowledge.md", "decisions.md", "inbox.md", "knowledge_index.md"]

# 不该出现在仓库任何地方的文件名：旧 per-feature 接管残留 + 已被取代的旧文档名（迁移守卫）。
FORBIDDEN_SLOT_FILENAMES = [
    "current_task.json", "task_board.yaml", "handoff.md", "verification.md",
    "session_log.md", "report.md", "file_scope.yaml",
    "STATUS.md", "findings.md", "canonical-assets.md",
]

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
