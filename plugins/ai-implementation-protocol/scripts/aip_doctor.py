from __future__ import annotations

"""aip doctor —— 安装与环境健康检查（诊断用，不挡提交；硬闸门是 aip check）。

四类检查：
1. 项目 .aip/ 健康（活文档齐全、索引一致、无旧机制残留、knowledge 复核超期）
2. 安装健康（~/plugins 下的插件包、skills 文件、装的版本 vs 引擎版本）
3. hook 健康（pre-commit 是否在、是否 AIP 管理、指向的引擎还在不在）
4. 引擎仓库健康（root 与 plugins/ 副本逐字节一致、VERSION 同步）

输出分级：ERROR（AIP 用不了）/ WARN（体验差或有漂移风险）/ INFO（可选建议），
每条带修复命令；有 ERROR 时退出码 1，否则 0。
"""

import argparse
import os
import re
from datetime import date, datetime
from pathlib import Path

import aip_check
from _aip_common import aip_root, force_utf8, read_text
from aip_knowledge import parse_entries
from install_hooks import PRE_COMMIT_MARK

ENGINE_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "ai-implementation-protocol"
# knowledge 条目复核超过这个天数只提醒（WARN），不判死刑。
STALE_DAYS = 90

Item = tuple[str, str, str | None]  # (级别, 说明, 修复命令)


def _read_version(path: Path) -> str | None:
    try:
        return read_text(path).strip() or None
    except OSError:
        return None


def default_codex_home(home: Path) -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return home / ".codex"


def codex_skill_paths(home: Path, skill: str, codex_home: Path | None = None) -> list[Path]:
    roots = [home / ".agents" / "skills"]
    roots.append((codex_home or default_codex_home(home)) / "skills")
    out: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        path = (root / skill / "SKILL.md").expanduser().resolve()
        key = str(path).casefold()
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


def check_project(repo: Path, engine: Path, stale_days: int = STALE_DAYS) -> list[Item]:
    out: list[Item] = []
    if not aip_root(repo).is_dir():
        out.append(("INFO", f"项目未初始化 AIP（无 {aip_root(repo)}）",
                    f"python {engine}/scripts/aip_init.py --repo-root {repo}"))
        return out
    init_fix = f"python {engine}/scripts/aip_init.py --repo-root {repo}"
    for v in aip_check.check_living_files(repo):
        out.append(("ERROR", v, init_fix))
    for v in aip_check.check_index_sync(repo):
        out.append(("ERROR", v, f"python {engine}/scripts/aip_knowledge.py --repo-root {repo}"))
    for v in aip_check.check_knowledge_fields(repo):
        out.append(("ERROR", v, "补齐该条目的必填字段"))
    for v in aip_check.check_no_orphan_slots(repo):
        out.append(("ERROR", v, "内容迁入现行活文档后删除该文件"))
    out.extend(check_knowledge_freshness(repo, stale_days=stale_days))
    return out


def check_knowledge_freshness(repo: Path, today: date | None = None, stale_days: int = STALE_DAYS) -> list[Item]:
    kn = aip_root(repo) / "knowledge.md"
    if not kn.exists():
        return []
    today = today or date.today()
    out: list[Item] = []
    for e in parse_entries(read_text(kn)):
        status = e["fields"].get("状态", "")
        if status.startswith("superseded"):
            continue
        raw = e["fields"].get("最后复核", "")
        try:
            reviewed = datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            out.append(("WARN", f'知识条目 {e["id"]} 的「最后复核」不是 YYYY-MM-DD：{raw!r}',
                        "改成日期格式，复核后更新"))
            continue
        age = (today - reviewed).days
        if age > stale_days:
            out.append(("WARN", f'知识条目 {e["id"]} 已 {age} 天未复核（最后复核 {raw}，阈值 {stale_days} 天）',
                        "复核内容是否仍成立，更新「最后复核」日期"))
    return out


def check_install(home: Path, engine: Path, codex_home: Path | None = None) -> list[Item]:
    out: list[Item] = []
    installed = home / "plugins" / PLUGIN_NAME
    reinstall = f"python {engine}/scripts/install_all.py（或分端 install_claude/codex/grok_plugin.py）"
    if not installed.is_dir():
        out.append(("WARN", f"未找到已安装的插件包：{installed}", reinstall))
        return out
    for skill in ["aip", "root-cause"]:
        if not (home / ".claude" / "skills" / skill / "SKILL.md").exists():
            out.append(("WARN", f"Claude 技能未安装：~/.claude/skills/{skill}/SKILL.md", reinstall))
        paths = codex_skill_paths(home, skill, codex_home)
        if not any(path.exists() for path in paths):
            pretty = " 或 ".join(str(path) for path in paths)
            out.append(("INFO", f"Codex 技能未安装：{pretty}（不用 Codex 可忽略）",
                        f"python {engine}/scripts/install_codex_plugin.py"))
        if not (home / ".grok" / "skills" / skill / "SKILL.md").exists():
            out.append(("INFO", f"Grok 技能未安装：~/.grok/skills/{skill}/SKILL.md（不用 Grok 可忽略）",
                        f"python {engine}/scripts/install_grok_plugin.py"))
    engine_ver = _read_version(engine / "VERSION")
    installed_ver = _read_version(installed / "VERSION")
    if installed_ver is None:
        out.append(("WARN", "已安装的插件包没有 VERSION（旧版安装）", reinstall))
    elif engine_ver and installed_ver != engine_ver:
        out.append(("WARN", f"版本不一致：引擎 {engine_ver}，已安装 {installed_ver}", reinstall))
    return out


def check_hooks(repo: Path, engine: Path) -> list[Item]:
    out: list[Item] = []
    if not (repo / ".git").exists():
        out.append(("INFO", f"{repo} 不是 git 仓库，跳过 hook 检查", None))
        return out
    install_fix = f"python {engine}/scripts/install_hooks.py --repo-root {repo}"
    hook = repo / ".git" / "hooks" / "pre-commit"
    if not hook.exists():
        out.append(("WARN", "未装 pre-commit 钩子，aip check 只能靠自觉", install_fix))
        return out
    body = hook.read_text(encoding="utf-8", errors="ignore")
    if PRE_COMMIT_MARK not in body:
        out.append(("WARN", "pre-commit 钩子存在但不是 AIP 管理的（不会自动跑 aip check）",
                    f"{install_fix} --force（会覆盖现有钩子，先确认）"))
        return out
    m = re.search(r'"([^"]+/scripts/aip_check\.py)"', body)
    if m and not Path(m.group(1)).exists():
        out.append(("WARN", f"钩子指向的引擎脚本不存在：{m.group(1)}（引擎搬家或删了）", install_fix))
    return out


def check_engine_repo(repo: Path) -> list[Item]:
    plugin_root = repo / "plugins" / PLUGIN_NAME
    if not plugin_root.is_dir():
        return []
    sync_fix = f"python {repo}/scripts/sync_plugin.py"
    out: list[Item] = [("ERROR", v, sync_fix) for v in aip_check.check_dual_copy(repo)]
    root_ver = _read_version(repo / "VERSION")
    plugin_ver = _read_version(plugin_root / "VERSION")
    if root_ver != plugin_ver:
        out.append(("ERROR", f"VERSION 不同步：根 {root_ver!r}，插件副本 {plugin_ver!r}", sync_fix))
    return out


def run_all(repo: Path, home: Path, engine: Path, stale_days: int = STALE_DAYS,
            codex_home: Path | None = None) -> list[Item]:
    return (check_project(repo, engine, stale_days) + check_install(home, engine, codex_home)
            + check_hooks(repo, engine) + check_engine_repo(repo))


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="AIP install/environment health check.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--home", default=str(Path.home()), help="含 plugins/、.claude/、.agents/、.grok/ 的主目录。")
    ap.add_argument("--codex-home", default=None,
                    help="Codex home；默认取 CODEX_HOME，未设置则为 <home>/.codex。")
    ap.add_argument("--engine-root", default=str(ENGINE_ROOT))
    ap.add_argument("--stale-days", type=int, default=STALE_DAYS,
                    help=f"knowledge 条目超过多少天未复核就提醒（默认 {STALE_DAYS}）。")
    a = ap.parse_args()
    home = Path(a.home).resolve()
    codex_home = Path(a.codex_home).expanduser().resolve() if a.codex_home else None
    items = run_all(Path(a.repo_root).resolve(), home,
                    Path(a.engine_root).resolve(), a.stale_days, codex_home)
    for level, msg, fix in items:
        print(f"[{level}] {msg}" + (f"\n        修复：{fix}" if fix else ""))
    errors = sum(1 for lv, _, _ in items if lv == "ERROR")
    warns = sum(1 for lv, _, _ in items if lv == "WARN")
    print(f"aip doctor：{errors} 个 ERROR，{warns} 个 WARN，{len(items) - errors - warns} 个 INFO"
          if items else "aip doctor：一切健康")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
