from __future__ import annotations

"""把 `aip check` 挂成自动闸门——"没法忘"那一级。

- git pre-commit（主闸门，硬挡）：每次提交前跑 `aip check`，红了挡住提交。
- 可选 Claude Code Stop 钩子（--claude-stop，非阻塞）：每轮结束跑一次 check 把状态摆出来。

git 钩子放 .git/hooks/pre-commit（即时生效、无框架依赖）。bypass 用 `git commit --no-verify`。
"""

import argparse
import json
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]

PRE_COMMIT_MARK = "# AIP gate (install_hooks.py)"


def pre_commit_body(engine_root: Path) -> str:
    cmd = f'python "{engine_root.as_posix()}/scripts/aip.py" check --repo-root .'
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


def install_claude_stop(repo_root: Path, engine_root: Path) -> None:
    settings = repo_root / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raise SystemExit(f"Cannot parse {settings}; fix it or remove --claude-stop.")
    cmd = f'python "{engine_root.as_posix()}/scripts/aip.py" check --repo-root .'
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
    parser.add_argument("--force", action="store_true", help="覆盖已存在的非 AIP pre-commit 钩子。")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    engine_root = args.engine_root.resolve()

    install_pre_commit(repo_root, engine_root, args.force)
    if args.claude_stop:
        install_claude_stop(repo_root, engine_root)

    print("Hooks installed. pre-commit now runs `aip check`; bypass once with `git commit --no-verify`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
