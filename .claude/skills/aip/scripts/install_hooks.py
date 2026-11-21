from __future__ import annotations

"""把 `aip check` 挂成自动检查——"没法忘"那一级。

- git pre-commit（主检查，硬挡）：每次提交前跑 `aip check`，红了挡住提交。
- Claude Code SessionStart 钩子（--session-start，aip init 默认装）：新会话、恢复会话、
  以及上下文被压缩之后，把看板（在建线、待处理问题）打进上下文；压缩后多提醒一句"以在建线为准"。
- Claude Code PreCompact 钩子（--pre-compact，aip init 默认装）：压缩**之前**把"摘要里必须留下
  什么"和在建线全文交给写摘要的那一轮（这个钩子的标准输出就是写摘要的指示）。
- Claude Code PostToolUse 钩子（--post-tool-use，aip init 默认装）：Edit / Write 之后对刚改的文件
  跑一次反查，一个会话里同一个文件只提一次。
- Claude Code SubagentStart 钩子（--subagent-start，aip init 默认装）：开子代理时把在建线、主题目录
  和"只有主代理写 .aip/"交给它。
- 可选 Claude Code Stop 钩子（--claude-stop，非阻塞）：每轮结束跑一次 check 把状态摆出来。

git 钩子放 git 的钩子目录（`git rev-parse --git-path hooks`，即时生效、无框架依赖）。bypass 用 `git commit --no-verify`。
同一仓库的各个 worktree 共用这一份钩子；项目级安装时钩子按当前检出的根目录找引擎，
每个 worktree 跑的是它自己检出的那版引擎，而不是装钩子那个工作区的。
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]

PRE_COMMIT_MARK = "# AIP gate (install_hooks.py)"

# 钩子在非交互环境运行，裸 `python` 在只有 python3 的机器上会失败；
# 烧进装钩子时所用解释器的绝对路径，保证以后跑得起来。
def _check_cmd(engine_root: Path) -> str:
    py = Path(sys.executable).as_posix()
    return f'"{py}" "{engine_root.as_posix()}/scripts/aip_check.py" --repo-root .'


def engine_expr(repo_root: Path | None, engine_root: Path) -> str:
    """钩子里怎么写引擎位置：引擎在仓库里（项目级安装）就从当前检出的根目录算，否则写绝对路径。"""
    if repo_root is not None:
        try:
            rel = engine_root.resolve().relative_to(repo_root.resolve()).as_posix()
            return f"$(git rev-parse --show-toplevel)/{rel}"
        except ValueError:
            pass
    return engine_root.as_posix()


def pre_commit_body(engine_root: Path, repo_root: Path | None = None) -> str:
    # 提交前只查格式，不算到期提醒：提醒不挡提交，算它要跑 git 历史，白白拖慢每次提交。
    # 查过之后列出这次改动相关的主题和条目：开工时按任务说法挑文件会漏，这里按改动的文件兜一次，只列不挡。
    # 检出里没有引擎（比如切到了装 AIP 之前的分支）就跳过，不挡提交。
    py = Path(sys.executable).as_posix()
    return (
        "#!/bin/sh\n"
        f"{PRE_COMMIT_MARK}\n"
        f'ENGINE="{engine_expr(repo_root, engine_root)}"\n'
        'if [ ! -f "$ENGINE/scripts/aip_check.py" ]; then\n'
        '  echo "AIP: no engine at $ENGINE in this checkout, check skipped" >&2\n'
        "  exit 0\n"
        "fi\n"
        f'"{py}" "$ENGINE/scripts/aip_check.py" --repo-root . --no-reminders || {{\n'
        '  echo "AIP check failed — fix the above, or bypass once with: git commit --no-verify" >&2\n'
        "  exit 1\n"
        "}\n"
        f'"{py}" "$ENGINE/scripts/aip_lookup.py" --repo-root . relevant --staged || true\n'
    )


def git_hooks_dir(repo_root: Path) -> Path:
    """git 的钩子目录。worktree 里 .git 是个文件，不能直接拼 .git/hooks；core.hooksPath 也要认。"""
    try:
        r = subprocess.run(["git", "rev-parse", "--git-path", "hooks"], cwd=repo_root, capture_output=True,
                           text=True, encoding="utf-8", timeout=10, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        r = None
    if r is None or r.returncode != 0 or not r.stdout.strip():
        raise SystemExit(f"Not a git repo: {repo_root}")
    p = Path(r.stdout.strip())
    return p if p.is_absolute() else repo_root / p


def install_pre_commit(repo_root: Path, engine_root: Path, force: bool) -> None:
    if not (repo_root / ".git").exists():
        raise SystemExit(f"Not a git repo (no .git): {repo_root}")
    hooks_dir = git_hooks_dir(repo_root)
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook = hooks_dir / "pre-commit"
    if hook.exists():
        existing = hook.read_text(encoding="utf-8", errors="ignore")
        if PRE_COMMIT_MARK in existing:
            hook.write_text(pre_commit_body(engine_root, repo_root), encoding="utf-8", newline="\n")
            print(f"Updated pre-commit hook: {hook}")
            return
        if not force:
            raise SystemExit(
                f"pre-commit hook exists and is not AIP-managed: {hook}\n"
                "Re-run with --force to overwrite, or add the AIP check line manually."
            )
    hook.write_text(pre_commit_body(engine_root, repo_root), encoding="utf-8", newline="\n")
    try:
        hook.chmod(0o755)
    except OSError:
        pass
    print(f"Installed pre-commit hook: {hook}")


# 引擎脚本要求的最低 Python 版本
MIN_PYTHON = (3, 9)

# 历代 AIP 装过的脚本；认出来的旧条目在重装时换掉，不留指向已删路径的死钩子。
AIP_SESSION_SCRIPTS = ("aip_session_start.py", "aip_overview.py")
AIP_PRECOMPACT_SCRIPTS = ("aip_precompact.py",)
AIP_AFTER_EDIT_SCRIPTS = ("aip_after_edit.py",)
AIP_SUBAGENT_SCRIPTS = ("aip_subagent.py",)
# 这两枚钩子的输出是 JSON，解释器探测失败时不能打中文提示（会被当成坏 JSON），所以静默
QUIET = ""


def hook_cmd(repo_root: Path, engine_root: Path, script: str, miss_note: str) -> str:
    try:
        rel = engine_root.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        py = Path(sys.executable).as_posix()
        return f'"{py}" "{engine_root.as_posix()}/scripts/{script}" --repo-root .'
    # 项目级安装：引擎在仓库里，写成相对项目根，settings.json 进版本库后换台机器也能用。
    # 换了机器解释器名也不能写死：Linux 上 python 可能是 2.7，Windows 上 python3 可能是
    # 应用商店的占位程序。所以挨个试，用第一个 3.9 以上的；-c 不读 stdin，钩子的输入留给脚本。
    target = f'"$CLAUDE_PROJECT_DIR/{rel}/scripts/{script}" --repo-root "$CLAUDE_PROJECT_DIR"'
    return (f'for py in python3 python; do "$py" -c "import sys; sys.exit(sys.version_info < {MIN_PYTHON})" '
            f'2>/dev/null && exec "$py" {target}; done; echo "AIP：没找到 Python 3.9 以上的解释器，{miss_note}"')


def session_start_cmd(repo_root: Path, engine_root: Path) -> str:
    return hook_cmd(repo_root, engine_root, "aip_session_start.py", "看板没打印")


def pre_compact_cmd(repo_root: Path, engine_root: Path) -> str:
    return hook_cmd(repo_root, engine_root, "aip_precompact.py", "压缩指示没给出")


def after_edit_cmd(repo_root: Path, engine_root: Path) -> str:
    return hook_cmd(repo_root, engine_root, "aip_after_edit.py", QUIET)


def subagent_cmd(repo_root: Path, engine_root: Path) -> str:
    return hook_cmd(repo_root, engine_root, "aip_subagent.py", QUIET)


def install_claude_hook(repo_root: Path, engine_root: Path, event: str, cmd: str,
                        known: tuple[str, ...], what: str, matcher: str | None = None) -> None:
    """把一条 AIP 钩子写进 .claude/settings.json 的某个事件下。

    同命令不重复加；认得出的旧 AIP 条目（指向改过名或搬过家的脚本）顺手换掉；别人的钩子不动。
    """
    settings = repo_root / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raise SystemExit(f"Cannot parse {settings}; fix it manually.")
    hooks = data.setdefault("hooks", {})
    starts = hooks.setdefault(event, [])
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
            elif any(name in command for name in known):
                replaced += 1
            else:
                kept.append(h)
        if kept:
            kept_groups.append({**group, "hooks": kept})
    if present and not replaced:
        print(f"Claude {event} hook already present in {settings}")
        return
    if not present:
        group = {"hooks": [{"type": "command", "command": cmd}]}
        if matcher:
            group["matcher"] = matcher
        kept_groups.append(group)
    hooks[event] = kept_groups
    settings.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    note = f"（换掉了 {replaced} 条旧的 AIP 钩子）" if replaced else ""
    print(f"Installed Claude {event} hook（{what}）: {settings}{note}")


def install_claude_session_start(repo_root: Path, engine_root: Path) -> None:
    install_claude_hook(repo_root, engine_root, "SessionStart",
                        session_start_cmd(repo_root, engine_root), AIP_SESSION_SCRIPTS, "会话开始打看板")


def install_claude_pre_compact(repo_root: Path, engine_root: Path) -> None:
    install_claude_hook(repo_root, engine_root, "PreCompact",
                        pre_compact_cmd(repo_root, engine_root), AIP_PRECOMPACT_SCRIPTS, "压缩前给写摘要的指示")


def install_claude_after_edit(repo_root: Path, engine_root: Path) -> None:
    install_claude_hook(repo_root, engine_root, "PostToolUse", after_edit_cmd(repo_root, engine_root),
                        AIP_AFTER_EDIT_SCRIPTS, "改完文件就列相关条目", matcher="Edit|Write")


def install_claude_subagent(repo_root: Path, engine_root: Path) -> None:
    install_claude_hook(repo_root, engine_root, "SubagentStart", subagent_cmd(repo_root, engine_root),
                        AIP_SUBAGENT_SCRIPTS, "给子代理交底", matcher="*")


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
    parser.add_argument("--session-start", action="store_true", help="装 Claude Code SessionStart 钩子（新会话/恢复/压缩后把看板打进上下文）。")
    parser.add_argument("--post-tool-use", action="store_true",
                        help="装 Claude Code PostToolUse 钩子（Edit / Write 之后对刚改的文件跑一次反查）。")
    parser.add_argument("--subagent-start", action="store_true",
                        help="装 Claude Code SubagentStart 钩子（把在建线和两条规矩交给子代理）。")
    parser.add_argument("--pre-compact", action="store_true",
                        help="装 Claude Code PreCompact 钩子（压缩前把「摘要里必须留下什么」和在建线交给写摘要的那一轮）。")
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
    if args.pre_compact:
        install_claude_pre_compact(repo_root, engine_root)
    if args.post_tool_use:
        install_claude_after_edit(repo_root, engine_root)
    if args.subagent_start:
        install_claude_subagent(repo_root, engine_root)

    if args.no_pre_commit:
        print("Hooks installed (pre-commit left untouched).")
    else:
        print("Hooks installed. pre-commit now runs `aip check`; bypass once with `git commit --no-verify`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
