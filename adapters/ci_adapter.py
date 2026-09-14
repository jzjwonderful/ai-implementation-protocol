from __future__ import annotations


def recommended_ci_step() -> str:
    return "python ~/.claude/skills/aip/scripts/aip_check.py --repo-root ."
