# AI Implementation Protocol Plugin

This directory is the installable package for Claude Code, Codex, and Grok.

It contains:

- `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json` and `.grok-plugin/plugin.json` — manifests (their `version` must match `skills/aip/VERSION`)
- `skills/aip/` — the `aip` engine skill. **Everything the skill needs travels with it**:
  - `SKILL.md` — the always-loaded core (short)
  - `reference/` — the review checklist, completion check and init details, read on demand
  - `scripts/` — the CLI tools (`aip_init.py`, `aip_check.py`, `aip_item.py`, `aip_upkeep.py`, `aip_migrate.py`, `aip_doctor.py`, `aip_update.py`, `install_hooks.py`, `aip_session_start.py`)
  - `templates/` — the living-doc templates `aip_init.py` scaffolds from
  - `VERSION` — the engine version (single source)

There is no separate copy of scripts or templates anywhere else in the repository, so nothing needs syncing.

## Where it lands

Installers, all run from the repository root:

```bash
python3 scripts/install_all.py             # recommended: Claude + Codex + Grok in one shot
python3 scripts/install_claude_plugin.py   # → ~/.claude/skills/
python3 scripts/install_codex_plugin.py    # → ~/.agents/skills/ + $CODEX_HOME/skills + marketplace + ~/plugins/
python3 scripts/install_grok_plugin.py     # → ~/.grok/skills/ + ~/plugins/
```

Every installer copies the whole skill directory, for example:

```text
~/.claude/skills/aip/        (SKILL.md + reference/ + scripts/ + templates/ + VERSION)
```

Codex and Grok also keep the packaged source under `~/plugins/ai-implementation-protocol/` and install from
there; Codex additionally writes a local marketplace entry to `~/.agents/plugins/marketplace.json`. The
single-runtime Claude installer writes nothing to `~/plugins/`. Existing AIP install files are replaced, and the
`root-cause` / `aip-brainstorm` skills that AIP shipped before 0.6.0 are removed.

Project-level install (the skill travels with one repository instead of the machine):

```bash
python3 scripts/install_all.py --project /path/to/repo   # → <repo>/.claude/skills/ + <repo>/.codex/skills/
```

Grok optional user-plugin registration:

```bash
python3 scripts/install_grok_plugin.py --user-plugin
# → ~/.grok/plugins/ai-implementation-protocol/
```

After installation, run `/aip init` (Claude Code) or `$aip init` (Codex / Grok) once per repository. Everything else — capturing knowledge, running `aip check`, resuming from the live tracks, tidying `.aip/` after an upgrade — is triggered by the AI at the right moment, not typed by the human.
