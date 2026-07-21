# AI Implementation Protocol Plugin

This package ships AIP for Claude Code, Codex, and Grok.

It includes:

- `.claude-plugin/plugin.json` / `.codex-plugin/plugin.json` / `.grok-plugin/plugin.json`
- `skills/aip/SKILL.md` — the `aip` engine skill (AI-autonomous; the human only runs `$aip init`)
- `skills/root-cause/SKILL.md` — root-cause investigation + knowledge sedimentation
- `skills/aip-brainstorm/SKILL.md` — multi-terminal multi-AI discussion through a shared topic document (turn-taking, convergence, user input relay)
- `scripts/` CLI tools
- `docs/` and `templates/` resources used by the scripts
- `VERSION` — the packaged engine version

Installers (from the repository root):

```bash
python scripts/install_all.py             # recommended: Claude + Codex + Grok in one shot
python scripts/install_claude_plugin.py   # → ~/.claude/skills/ + ~/plugins/
python scripts/install_codex_plugin.py    # → ~/.agents/skills/ + marketplace + ~/plugins/
python scripts/install_grok_plugin.py     # → ~/.grok/skills/ + ~/plugins/
```

Codex also updates:

```text
~/.agents/plugins/marketplace.json
```

Grok optional user-plugin registration:

```bash
python scripts/install_grok_plugin.py --user-plugin
# → ~/.grok/plugins/ai-implementation-protocol/
```

The installer also writes the same skills to `$CODEX_HOME/skills` when `CODEX_HOME` is set, otherwise `~/.codex/skills`. Existing AIP install files are replaced by default.

After installation, run `$aip init` once per repository. Everything else — capturing knowledge, running `aip check`, rebuilding the index/digest, resuming from the OVERVIEW board — is triggered by the AI at the right moment, not typed by the human.

```text
$aip init
```

The skill drives the CLI scripts (`aip_init.py`, `aip_check.py`, `aip_knowledge.py`, `aip_overview.py`, `aip_doctor.py`) inside the installed plugin package. The `root-cause` skill auto-triggers on bug / unexpected-behavior tasks: it recalls known causes from `.aip/knowledge_index.md`, digs past the symptom, hands the cause to you, then deposits verified causes into `.aip/knowledge.md`. The `aip-brainstorm` skill drives `aip_brainstorm.py`: AIs in separate terminals discuss one topic through a shared document in `.aip/brainstorm/`, with enforced turn-taking, user-input relay, and convergence exits (consensus / user arbitration / round cap).
