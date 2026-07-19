# AI Implementation Protocol Codex Plugin

This plugin packages AIP as a repo-local Codex plugin.

It includes:

- `.codex-plugin/plugin.json`
- `skills/aip/SKILL.md` — the `aip` engine skill (AI-autonomous; the human only runs `$aip init`)
- `skills/root-cause/SKILL.md` — root-cause investigation + knowledge sedimentation
- `scripts/` CLI tools
- `docs/` and `templates/` resources used by the scripts
- `VERSION` — the packaged engine version

The repository marketplace entry lives at:

```text
.agents/plugins/marketplace.json
```

The installer also writes compatibility skill entries to:

```text
~/.agents/skills/aip/SKILL.md
~/.agents/skills/root-cause/SKILL.md
```

This makes the `aip` and `root-cause` skills visible in Codex versions that load user skills directly from `.agents/skills`.

The installer also writes the same skills to `$CODEX_HOME/skills` when `CODEX_HOME` is set, otherwise `~/.codex/skills`. Existing AIP install files are replaced by default.

After installation, run `$aip init` once per repository. Everything else — capturing knowledge, running `aip check`, rebuilding the index/digest, resuming from the OVERVIEW board — is triggered by the AI at the right moment, not typed by the human.

Codex skill example:

```text
$aip init
```

The skill drives the CLI scripts (`aip_init.py`, `aip_check.py`, `aip_knowledge.py`, `aip_overview.py`, `aip_doctor.py`) inside the installed plugin package. The `root-cause` skill auto-triggers on bug / unexpected-behavior tasks: it recalls known causes from `.aip/knowledge_index.md`, digs past the symptom, hands the cause to you, then deposits verified causes into `.aip/knowledge.md`.

For GitHub distribution, publish the repository and ask users to run:

```bash
python scripts/install_codex_plugin.py
```

from the cloned repository root. The installer copies this plugin to the user's home-local plugin directory and updates `~/.agents/plugins/marketplace.json`.
