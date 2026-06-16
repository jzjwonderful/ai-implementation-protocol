# AI Implementation Protocol Codex Plugin

This plugin packages AIP as a repo-local Codex plugin.

It includes:

- `.codex-plugin/plugin.json`
- `skills/aip/SKILL.md` — `$aip` command router
- `skills/root-cause/SKILL.md` — root-cause investigation + knowledge sedimentation
- `scripts/` CLI tools
- `docs/`, `templates/`, and `schemas/` resources used by the scripts

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

After installation, use the `aip` skill to initialize a repository, start a feature package, resume work, or validate handoff completeness.

Codex skill examples:

```text
$aip init
$aip start 2026-04-26-my-feature --title "My feature"
$aip resume
$aip check
$aip knowledge
```

The skill routes these invocations to `scripts/aip.py` inside the installed plugin package. The `root-cause` skill auto-triggers on bug / unexpected-behavior tasks: it recalls known causes from `.aip/knowledge_index.md`, digs past the symptom, hands the cause to you, then deposits verified causes into `.aip/knowledge.md`.

For GitHub distribution, publish the repository and ask users to run:

```bash
python scripts/install_codex_plugin.py
```

from the cloned repository root. The installer copies this plugin to the user's home-local plugin directory and updates `~/.agents/plugins/marketplace.json`.
