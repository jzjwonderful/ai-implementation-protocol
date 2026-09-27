from __future__ import annotations

"""/aip update：已装好的 AIP 技能自己查新版本、自己更新，不依赖本机有没有 AIP 仓库、也不走安装器。

装的时候在 aip 技能目录写 SOURCE.json：远端地址和分支、装的是哪个提交、装在哪（个人级 / 某个项目）。

查：`git ls-remote <远端> <分支>` 取远端最新提交，和装的提交比。
- 一样 → 已是最新；
- 本机恰好有来源仓库、且远端那个提交是装的提交的祖先 → 装的比远端还新（本地没推送），不算更新；
- 其余 → 有更新。
项目 `.aip/config.yaml` 里写了 `aip_remote` / `aip_remote_branch` 就用它们（绑定远端），否则用 SOURCE.json 里的。
会话开始自动查一次：有更新才打印；没有 SOURCE.json、没网、远端不认识、git 出错一律不出声。

更新（--apply）：把远端分支浅克隆到临时目录，核对新版本齐全，再把本机装的每份技能目录
（项目级安装时 `.claude/skills` 和 `.codex/skills` 都算）逐个换成新版：先放到旁边，换成功再删旧的，
中途失败就换回去。最后改写 SOURCE.json 记下新提交。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from _aip_common import SKILL_NAMES, force_utf8, project_living_path, read_text, write_text

SOURCE_FILE = "SOURCE.json"
# 远端仓库里技能包所在的目录
PACKAGE_SKILLS = "plugins/ai-implementation-protocol/skills"
TIMEOUT = 5
CLONE_TIMEOUT = 120
ENGINE_ROOT = Path(__file__).resolve().parents[1]
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")

# 查远端时绝不弹窗、不等人输口令：拿不到就当检查失败。
QUIET_GIT_ENV = {
    "GIT_TERMINAL_PROMPT": "0",
    "GCM_INTERACTIVE": "Never",
    "GIT_SSH_COMMAND": "ssh -o BatchMode=yes",
}


def _git(args: list[str], cwd: Path | None = None, timeout: int = TIMEOUT) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, env={**os.environ, **QUIET_GIT_ENV},
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _git_out(args: list[str], cwd: Path | None = None, timeout: int = TIMEOUT) -> str | None:
    r = _git(args, cwd, timeout)
    if r is None or r.returncode != 0:
        return None
    return r.stdout.strip()


# ---------- 来源记录 ----------

def describe_source(source_repo: Path) -> dict:
    remote = _git_out(["remote", "get-url", "origin"], source_repo) or ""
    head = _git_out(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], source_repo) or ""
    branch = head.split("/", 1)[1] if "/" in head else "master"
    commit = _git_out(["rev-parse", "HEAD"], source_repo) or ""
    dirty = bool(_git_out(["status", "--porcelain"], source_repo))
    return {"remote": remote, "branch": branch, "commit": commit, "dirty": dirty,
            "source_path": str(source_repo.resolve())}


def _write_source(aip_dir: Path, data: dict) -> Path:
    version = aip_dir / "VERSION"
    data = {**data, "version": read_text(version).strip() if version.exists() else ""}
    path = aip_dir / SOURCE_FILE
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return path


def write_install_source(aip_dir: Path, source_repo: Path, scope: str, target: Path | None = None) -> Path:
    """安装器调用：在装好的 aip 技能目录里记下它从哪来、装在哪。"""
    data = describe_source(source_repo)
    data["scope"] = scope
    data["target"] = str(target.resolve()) if target else ""
    return _write_source(aip_dir, data)


def read_source(engine: Path = ENGINE_ROOT) -> dict | None:
    try:
        return json.loads(read_text(engine / SOURCE_FILE))
    except (OSError, ValueError):
        return None


# ---------- 检查 ----------

def config_binding(repo: Path) -> tuple[str, str]:
    cfg = project_living_path(repo, "config.yaml")
    if not cfg.exists():
        return "", ""
    text = read_text(cfg)

    def key(name: str) -> str:
        m = re.search(rf"^{name}:\s*[\"']?([^\"'#\s]*)", text, re.M)
        return m.group(1) if m else ""
    return key("aip_remote"), key("aip_remote_branch")


def remote_head(url: str, branch: str) -> str | None:
    out = _git_out(["ls-remote", url, f"refs/heads/{branch}"])
    if not out:
        return None
    sha = out.split()[0]
    return sha if re.fullmatch(r"[0-9a-f]{40}", sha) else None


def check(repo: Path, engine: Path = ENGINE_ROOT) -> dict:
    """返回 {state: latest|update|ahead|unknown, ...}；unknown 带 reason。"""
    src = read_source(engine)
    if not src:
        return {"state": "unknown", "reason": f"没有 {SOURCE_FILE}（不是用安装器装的，或是旧版安装器装的）"}
    bound_url, bound_branch = config_binding(repo)
    info = {**src,
            "url": bound_url or src.get("remote", ""),
            "branch": bound_branch or src.get("branch", "") or "master",
            "installed": src.get("commit", "")}
    if not info["url"] or not info["installed"]:
        return {**info, "state": "unknown", "reason": "不知道远端地址或装的是哪个提交"}
    remote = remote_head(info["url"], info["branch"])
    if not remote:
        return {**info, "state": "unknown", "reason": f"连不上 {info['url']} 或没有分支 {info['branch']}"}
    info["remote_commit"] = remote
    if remote == info["installed"]:
        return {**info, "state": "latest"}
    src_path = Path(info["source_path"]) if info.get("source_path") else None
    if src_path and (src_path / ".git").exists():
        r = _git(["merge-base", "--is-ancestor", remote, info["installed"]], src_path)
        if r is not None and r.returncode == 0:
            return {**info, "state": "ahead"}
    return {**info, "state": "update"}


def update_notice(repo: Path, engine: Path = ENGINE_ROOT) -> str | None:
    """会话开始用：有更新返回一句提示，其余情况（含任何异常）返回 None。"""
    try:
        info = check(repo, engine)
    except Exception:  # 会话开始绝不能因为查更新出错而打断
        return None
    if info.get("state") != "update":
        return None
    ver = f"{info['version']}，" if info.get("version") else ""
    return (f"AIP 引擎有更新：已装 {ver}提交 {info['installed'][:7]}；远端 {info['branch']} 最新 {info['remote_commit'][:7]}。"
            "先跟用户说一声，征得同意后运行 /aip update 更新，再继续当前任务。")


# ---------- 更新 ----------

def install_roots(info: dict, engine: Path) -> list[Path]:
    """要一起更新的技能目录：本份所在的目录；项目级安装再加上项目里另一端的目录。

    项目根从本份的位置推（<项目>/.claude/skills/aip），不用记录里的绝对路径——
    仓库换了机器、换了目录、或装的时候在临时工作区里，那个路径都不再成立。
    """
    roots = [engine.parent]
    if info.get("scope") == "project":
        project = engine.parents[2]
        for rel in (".claude/skills", ".codex/skills"):
            root = project / rel
            if (root / "aip" / "SKILL.md").exists() and root.resolve() not in [r.resolve() for r in roots]:
                roots.append(root)
    return roots


def fetch(url: str, branch: str, dest: Path) -> Path:
    r = _git(["clone", "--depth", "1", "--branch", branch, url, str(dest)], timeout=CLONE_TIMEOUT)
    if r is None or r.returncode != 0:
        raise RuntimeError(f"取远端失败：{(r.stderr if r else '').strip() or '超时或没装 git'}")
    skills = dest / PACKAGE_SKILLS
    for must in ("aip/SKILL.md", "aip/VERSION", "aip/scripts/aip_check.py", "aip/scripts/aip_update.py"):
        if not (skills / must).exists():
            raise RuntimeError(f"远端版本不完整，缺 {PACKAGE_SKILLS}/{must}，不更新")
    return skills


def swap_skills(new_skills: Path, root: Path) -> list[str]:
    """把 root 下的 AIP 技能逐个换成新版；任何一步失败都换回旧的再抛错。"""
    names = [n for n in SKILL_NAMES if (new_skills / n / "SKILL.md").exists()]
    staged: list[tuple[Path, Path, Path]] = []  # (正式位置, 新版暂存, 旧版备份)
    try:
        for name in names:
            live, new, old = root / name, root / f".{name}.new", root / f".{name}.old"
            for leftover in (new, old):
                if leftover.exists():
                    shutil.rmtree(leftover)
            shutil.copytree(new_skills / name, new, ignore=IGNORE)
            staged.append((live, new, old))
        for live, new, old in staged:
            if live.exists():
                live.rename(old)
            new.rename(live)
    except Exception:
        for live, new, old in staged:
            if old.exists():
                if live.exists():
                    shutil.rmtree(live, ignore_errors=True)
                old.rename(live)
            shutil.rmtree(new, ignore_errors=True)
        raise
    for _, _, old in staged:
        shutil.rmtree(old, ignore_errors=True)
    return names


def apply(repo: Path, engine: Path = ENGINE_ROOT) -> int:
    info = check(repo, engine)
    state = info["state"]
    if state == "latest":
        print(f"已是最新（{info['branch']} {info['installed'][:7]}）。")
        return 0
    if state == "ahead":
        print("装的版本比远端还新（来源仓库有没推送的提交），不需要更新。")
        return 0
    if state == "unknown":
        print(f"查不了更新：{info['reason']}。")
        return 1
    roots = install_roots(info, engine)
    with tempfile.TemporaryDirectory(prefix="aip-update-") as tmp:
        try:
            new_skills = fetch(info["url"], info["branch"], Path(tmp) / "src")
            record = {k: info[k] for k in ("remote", "branch", "scope", "target", "source_path") if k in info}
            record.update(remote=info["url"], branch=info["branch"], commit=info["remote_commit"], dirty=False)
            for root in roots:
                names = swap_skills(new_skills, root)
                _write_source(root / "aip", record)
                print(f"已更新 {root}：{'、'.join(names)}")
        except (OSError, RuntimeError) as e:
            print(f"更新失败，已保留原来的版本：{e}")
            return 1
    new_ver = read_text(engine / "VERSION").strip() if (engine / "VERSION").exists() else ""
    print(f"更新到 {info['branch']} {info['remote_commit'][:7]}" + (f"（版本 {new_ver}）" if new_ver else "") + "。开新会话生效。")
    if info.get("scope") == "project":
        print("项目级安装：把这些技能目录的变化提交进仓库，别人拉代码才能拿到新版。")
    return 0


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="Check for (and optionally apply) AIP engine updates.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--apply", action="store_true", help="有更新就从远端取新版，原地替换已装的技能。")
    a = ap.parse_args()
    repo = Path(a.repo_root).resolve()
    if a.apply:
        return apply(repo)
    info = check(repo)
    msg = {
        "latest": f"已是最新（{info.get('branch')} {info.get('installed', '')[:7]}）。",
        "ahead": "装的版本比远端还新（来源仓库有没推送的提交）。",
        "update": update_notice(repo) or "",
        "unknown": f"查不了更新：{info.get('reason', '')}。",
    }[info["state"]]
    print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
