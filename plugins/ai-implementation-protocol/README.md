# AI Implementation Protocol Codex Plugin

This plugin packages AIP as a repo-local Codex plugin.

It includes:

- `.codex-plugin/plugin.json`
- `skills/aip/SKILL.md`
- `scripts/` CLI tools
- `docs/`, `templates/`, and `schemas/` resources used by the scripts

The repository marketplace entry lives at:

```text
.agents/plugins/marketplace.json
```

After installation, use the `aip` skill to initialize a repository, start a feature package, resume work, or validate handoff completeness.

For GitHub distribution, publish the repository and ask users to run:

```bash
python scripts/install_codex_plugin.py
```

from the cloned repository root. The installer copies this plugin to the user's home-local plugin directory and updates `~/.agents/plugins/marketplace.json`.
