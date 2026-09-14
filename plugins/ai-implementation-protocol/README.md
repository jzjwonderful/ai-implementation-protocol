# AI Implementation Protocol Plugin

This directory is the installable package for both Codex and Claude Code.

It contains:

- `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json` — manifests (their `version` must match `skills/aip/VERSION`)
- `skills/aip/` — the `aip` engine skill. **Everything the skill needs travels with it**:
  - `SKILL.md` — the always-loaded core (short)
  - `reference/` — the review checklist, completion check and init details, read on demand
  - `scripts/` — the CLI tools (`aip_init.py`, `aip_check.py`, `aip_knowledge.py`, `aip_overview.py`, `aip_doctor.py`, `install_hooks.py`, `aip_session_start.py`)
  - `templates/` — the living-doc templates `aip_init.py` scaffolds from
  - `VERSION` — the engine version (single source)
- `skills/root-cause/SKILL.md` — root-cause investigation + knowledge sedimentation

There is no separate copy of scripts or templates anywhere else in the repository, so nothing needs syncing.

## Where it lands

Claude Code (`python scripts/install_claude_plugin.py` from the repository root):

```text
~/.claude/skills/aip/        (SKILL.md + reference/ + scripts/ + templates/ + VERSION)
~/.claude/skills/root-cause/
```

Codex (`python scripts/install_codex_plugin.py`): the whole package goes to `~/plugins/ai-implementation-protocol/`, a local marketplace entry is written to `~/.agents/plugins/marketplace.json`, and the same whole skill directories are copied to `~/.agents/skills/` and `$CODEX_HOME/skills` (default `~/.codex/skills`). Existing AIP install files are replaced.

After installation, run `/aip init` (Claude Code) or `$aip init` (Codex) once per repository. Everything else — capturing knowledge, running `aip check`, rebuilding the index/digest, resuming from the OVERVIEW board — is triggered by the AI at the right moment.

The `root-cause` skill auto-triggers on bug / unexpected-behavior tasks: it recalls known causes from `.aip/knowledge_index.md`, digs past the symptom, hands the cause to you, then deposits verified causes into `.aip/knowledge.md`.
