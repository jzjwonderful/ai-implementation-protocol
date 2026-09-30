from __future__ import annotations

"""把 `aip check` 挂成自动检查——"没法忘"那一级。

- git pre-commit（主检查，硬挡）：每次提交前跑 `aip check`，红了挡住提交。
- Claude Code SessionStart 钩子（--session-start，aip init 默认装）：新会话、恢复会话、
  以及上下文被压缩之后，把 OVERVIEW 打进上下文；压缩后多提醒一句"以看板为准"。
- 可选 Claude Code Stop 钩子（--claude-stop，非阻塞）：每轮结束跑一次 check 把状态摆出来。

git 钩子放 .git/hooks/pre-commit（即时生效、无框架依赖）。bypass 用 `git commit --no-verify`。
"""

import argparse
import json
import sys
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]

PRE_COMMIT_MARK = "# AIP gate (install_hooks.py)"

# 钩子在非交互环境运行，裸 `python` 在只有 python3 的机器上会失败；
# 烧进装钩子时所用解释器的绝对路径，保证以后跑得起来。
def _check_cmd(engine_root: Path) -> str:
    py = Path(sys.executable).as_posix()
    return f'"{py}" "{engine_root.as_posix()}/scripts/aip_check.py" --repo-root .'


def pre_commit_body(engine_root: Path) -> str:
    # 提交前只查格式，不算到期提醒：提醒不挡提交，算它要跑 git 历史，白白拖慢每次提交
    cmd = _check_cmd(engine_root) + " --no-reminders"
    return (
        "#!/bin/sh\n"
        f"{PRE_COMMIT_MARK}\n"
        f"{cmd} || {{\n"
        '  echo "AIP check failed — fix the above, or bypass once with: git commit --no-verify" >&2\n'
        "  exit 1\n"
        "}\n"
    )


def install_pre_commit(repo_root: Path, engine_root: Path, force: bool) -> None:
    hooks_dir = repo_root / ".git" / "hooks"
    if not (repo_root / ".git").exists():
        raise SystemExit(f"Not a git repo (no .git): {repo_root}")
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook = hooks_dir / "pre-commit"
    if hook.exists():
        existing = hook.read_text(encoding="utf-8", errors="ignore")
        if PRE_COMMIT_MARK in existing:
            hook.write_text(pre_commit_body(engine_root), encoding="utf-8", newline="\n")
            print(f"Updated pre-commit hook: {hook}")
            return
        if not force:
            raise SystemExit(
                f"pre-commit hook exists and is not AIP-managed: {hook}\n"
                "Re-run with --force to overwrite, or add the AIP check line manually."
            )
    hook.write_text(pre_commit_body(engine_root), encoding="utf-8", newline="\n")
    try:
        hook.chmod(0o755)
    except OSError:
        pass
    print(f"Installed pre-commit hook: {hook}")


# 历代 AIP 装过的 SessionStart 脚本；认出来的旧条目在重装时换掉，不留指向已删路径的死钩子。
AIP_SESSION_SCRIPTS = ("aip_session_start.py", "aip_overview.py")


def session_start_cmd(repo_root: Path, engine_root: Path) -> str:
    try:
        rel = engine_root.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        py = Path(sys.executable).as_posix()
        return f'"{py}" "{engine_root.as_posix()}/scripts/aip_session_start.py" --repo-root .'
    # 项目级安装：引擎在仓库里，写成相对项目根，settings.json 进版本库后换台机器也能用
    return f'python "$CLAUDE_PROJECT_DIR/{rel}/scripts/aip_session_start.py" --repo-root "$CLAUDE_PROJECT_DIR"'


def install_claude_session_start(repo_root: Path, engine_root: Path) -> None:
    settings = repo_root / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raise SystemExit(f"Cannot parse {settings}; fix it manually.")
    cmd = session_start_cmd(repo_root, engine_root)
    hooks = data.setdefault("hooks", {})
    starts = hooks.setdefault("SessionStart", [])
    present = False
    replaced = 0
    kept_groups = []
    for group in starts:
        kept = []
        for h in group.get("hooks", []):
            command = h.get("command", "")
            if command == cmd:
                if not present:
                    kept.append(h)
                present = True
            elif any(name in command for name in AIP_SESSION_SCRIPTS):
                replaced += 1
            else:
                kept.append(h)
        if kept:
            kept_groups.append({**group, "hooks": kept})
    if present and not replaced:
        print(f"Claude SessionStart hook already present in {settings}")
        return
    if not present:
        kept_groups.append({"hooks": [{"type": "command", "command": cmd}]})
    hooks["SessionStart"] = kept_groups
    settings.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    note = f"（换掉了 {replaced} 条旧的 AIP 钩子）" if replaced else ""
    print(f"Installed Claude SessionStart hook: {settings}{note}")


def install_claude_stop(repo_root: Path, engine_root: Path) -> None:
    settings = repo_root / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raise SystemExit(f"Cannot parse {settings}; fix it or remove --claude-stop.")
    cmd = _check_cmd(engine_root)
    hooks = data.setdefault("hooks", {})
    stop = hooks.setdefault("Stop", [])
    # 去重：已含同命令则不重复加。
    for group in stop:
        for h in group.get("hooks", []):
            if h.get("command") == cmd:
                print(f"Claude Stop hook already present in {settings}")
                return
    stop.append({"hooks": [{"type": "command", "command": cmd}]})
    settings.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Installed Claude Stop hook (non-blocking): {settings}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install AIP enforcement hooks into a target repo.")
    parser.add_argument("--repo-root", default=".", type=Path, help="目标仓库根。默认当前目录。")
    parser.add_argument("--engine-root", default=ENGINE_ROOT, type=Path, help="AIP 引擎根。默认本仓库。")
    parser.add_argument("--claude-stop", action="store_true", help="额外装非阻塞的 Claude Code Stop 钩子。")
    parser.add_argument("--session-start", action="store_true", help="装 Claude Code SessionStart 钩子（新会话/恢复/压缩后把 OVERVIEW 打进上下文）。")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的非 AIP pre-commit 钩子。")
    parser.add_argument("--no-pre-commit", action="store_true",
                        help="不碰 pre-commit（项目已有自己的提交前钩子，比如 pre-commit 框架时用）。")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    engine_root = args.engine_root.resolve()

    if not args.no_pre_commit:
        install_pre_commit(repo_root, engine_root, args.force)
    if args.claude_stop:
        install_claude_stop(repo_root, engine_root)
    if args.session_start:
        install_claude_session_start(repo_root, engine_root)

    if args.no_pre_commit:
        print("Hooks installed (pre-commit left untouched).")
    else:
        print("Hooks installed. pre-commit now runs `aip check`; bypass once with `git commit --no-verify`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
