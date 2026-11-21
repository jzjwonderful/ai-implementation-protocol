from __future__ import annotations

import fnmatch
import json
import re
import shutil
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
# 知识、决策、旁路问题、在建线、可复用实现是一条一个文件，放在各自目录下，见 aip_item.TYPES。
# conventions.md 每次动手前都要读，所以只放跨模块的铁律和不变量，体积有上限（aip_check 查）。
PROJECT_FILES = ["conventions.md", "config.yaml"]

# 按需读的主题资料：一个主题一个文件，文件名就是主题、不带时间戳（要让别人稳定引用）。
# 文件头写 title、read_when（什么时候读）、paths（涉及哪些代码，可选）。
# 会话开始只打印目录（主题 + 什么时候读），AI 挑跟当前任务有关的读，不整篇全读。
TOPIC_DIR = "reference"
# 0.8.0 之前的整篇参照，0.8.0 起拆进 TOPIC_DIR
OLD_REFERENCE_FILE = "reference.md"

# 这一版起有主题目录、体积检查和引用检查。仓库的 .aip/ 按这一版整理过（config.yaml 的
# aip_version）才查：没拆的大文件一查就红，连做拆分的那次提交都过不了 pre-commit。
SPLIT_LAYOUT_VERSION = (0, 8, 0)
# 这一版起体积和引用也查项目自己的技能、size_check_paths 列的文档、.aip/ 下条目以外的文档（如 specs/）。
# 同样按 aip_version 才查：0.8.0 整理过的仓库里，这些地方原有的大文件和旧引用一查就红。
WIDER_CHECK_VERSION = (0, 8, 1)

# 0.5.0–0.6.x 生成的看板文件。看板现在由会话开始钩子直接按目录打印、不落盘：
# 存下来的文件没人刷新就会过期，AI 读到旧看板会以为没有在建线。
OLD_BOARD_FILE = "OVERVIEW.md"
OLD_BOARD_HEADER = "# 总览（自动生成，勿手改）"

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
SKILL_NAMES = ["aip"]

# 以前随包分发、0.6.0 删掉的技能。安装、更新时从技能目录里清掉，卸载时一并删：
# 留着的话，头脑风暴技能会去调已经不存在的脚本。
RETIRED_SKILL_NAMES = ["root-cause", "aip-brainstorm"]

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


def remove_old_board(target_repo: Path) -> bool:
    """删掉以前生成的看板文件（只删认得出是生成的那种），返回删没删。"""
    p = project_living_path(target_repo, OLD_BOARD_FILE)
    if not p.is_file() or not read_text(p).startswith(OLD_BOARD_HEADER):
        return False
    p.unlink()
    return True


AIP_VERSION_RE = re.compile(r"^aip_version:\s*[\"']?([^\"'#\s]*)", re.M)


def version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", text))


def aip_version(target_repo: Path) -> tuple[int, ...]:
    """这个仓库的 .aip/ 按哪一版模板整理过；没写（0.7.0 之前建的）是空元组。"""
    cfg = project_living_path(target_repo, "config.yaml")
    if not cfg.exists():
        return ()
    m = AIP_VERSION_RE.search(read_text(cfg))
    return version_tuple(m.group(1)) if m else ()


def split_layout(target_repo: Path) -> bool:
    """.aip/ 已经按主题拆分整理过（0.8.0 及以后的模板）。"""
    return aip_version(target_repo) >= SPLIT_LAYOUT_VERSION


def resolve_path(p: str, files: list[str]) -> list[str]:
    """条目里写的路径 → 仓库里对应的文件。

    允许写部分路径（如 `routers/admin.py`），目录算它下面全部；带 * ? 的按通配匹配，* 可以跨目录。
    """
    p = p.strip().rstrip("/")
    if any(c in p for c in "*?["):
        return [f for f in files if fnmatch.fnmatchcase(f, p) or fnmatch.fnmatchcase(f, "*/" + p)]
    exact = [f for f in files if f == p or f.startswith(p + "/")]
    if exact:
        return exact
    return [f for f in files if f.endswith("/" + p) or ("/" + p + "/") in ("/" + f)]


def py_cmd() -> str:
    """印给人或 AI 照着跑的命令里用哪个解释器：就是正在跑这个脚本的那个（探测结果，一定是 Python 3）。

    不写死 python3 或 python：Linux 上 python 可能是 2.7，Windows 上常常只有 python。
    写完整路径，不在 PATH 上也能用；路径带空格就加引号。
    """
    exe = Path(sys.executable).as_posix() if sys.executable else "python3"
    return f'"{exe}"' if " " in exe else exe


def remove_retired_skills(skills_root: Path) -> list[Path]:
    """清掉 skills_root 下已删除的 AIP 技能目录，返回删了哪些。"""
    removed: list[Path] = []
    for name in RETIRED_SKILL_NAMES:
        skill_dir = skills_root / name
        if skill_dir.is_dir():
            shutil.rmtree(skill_dir)
            removed.append(skill_dir)
    return removed
