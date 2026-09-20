from __future__ import annotations

from pathlib import Path


def recommended_ci_step(engine_root: str | Path) -> str:
    """CI 里跑 aip check 的命令。

    `engine_root` 是**装好的** aip 技能目录，各运行时落点不同（Claude Code 在
    `~/.claude/skills/aip`，Codex 在 `~/.agents/skills/aip` 或 `$CODEX_HOME/skills/aip`，
    Grok 在 `~/.grok/skills/aip`，项目级安装则在仓库里），所以由调用方给，本函数不猜。
    """
    return f"python {Path(engine_root).as_posix()}/scripts/aip_check.py --repo-root ."
