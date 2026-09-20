# AI Implementation Protocol Plugin

This directory is the installable package for Claude Code, Codex, and Grok.

It contains:

- `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json` and `.grok-plugin/plugin.json` — manifests (their `version` must match `skills/aip/VERSION`)
- `skills/aip/` — the `aip` engine skill. **Everything the skill needs travels with it**:
  - `SKILL.md` — the always-loaded core (short)
  - `reference/` — the review checklist, completion check and init details, read on demand
  - `scripts/` — the CLI tools (`aip_init.py`, `aip_check.py`, `aip_knowledge.py`, `aip_overview.py`, `aip_doctor.py`, `aip_brainstorm.py`, `install_hooks.py`, `aip_session_start.py`)
  - `templates/` — the living-doc templates `aip_init.py` scaffolds from
  - `VERSION` — the engine version (single source)
- `skills/root-cause/SKILL.md` — root-cause investigation + knowledge sedimentation
- `skills/aip-brainstorm/SKILL.md` — multi-terminal multi-AI discussion through a shared topic document (turn-taking, convergence, user input relay)

There is no separate copy of scripts or templates anywhere else in the repository, so nothing needs syncing.

## Where it lands

Installers, all run from the repository root:

```bash
python scripts/install_all.py             # recommended: Claude + Codex + Grok in one shot
python scripts/install_claude_plugin.py   # → ~/.claude/skills/
python scripts/install_codex_plugin.py    # → ~/.agents/skills/ + $CODEX_HOME/skills + marketplace + ~/plugins/
python scripts/install_grok_plugin.py     # → ~/.grok/skills/ + ~/plugins/
```

Every installer copies whole skill directories, for example:

```text
~/.claude/skills/aip/        (SKILL.md + reference/ + scripts/ + templates/ + VERSION)
~/.claude/skills/root-cause/
~/.claude/skills/aip-brainstorm/
```

Codex and Grok also keep the packaged source under `~/plugins/ai-implementation-protocol/` and install from
there; Codex additionally writes a local marketplace entry to `~/.agents/plugins/marketplace.json`. The
single-runtime Claude installer writes nothing to `~/plugins/`. Existing AIP install files are replaced.

Grok optional user-plugin registration:

```bash
python scripts/install_grok_plugin.py --user-plugin
# → ~/.grok/plugins/ai-implementation-protocol/
```

After installation, run `/aip init` (Claude Code) or `$aip init` (Codex / Grok) once per repository. Everything else — capturing knowledge, running `aip check`, rebuilding the index/digest, resuming from the OVERVIEW board — is triggered by the AI at the right moment, not typed by the human.

The `root-cause` skill auto-triggers on bug / unexpected-behavior tasks: it recalls known causes from `.aip/knowledge_index.md`, digs past the symptom, hands the cause to you, then deposits verified causes into `.aip/knowledge.md`. The `aip-brainstorm` skill drives `aip_brainstorm.py`: AIs in separate terminals discuss one topic through a shared document in `.aip/brainstorm/`, with enforced turn-taking, user-input relay, and convergence exits (consensus / user arbitration / round cap).
