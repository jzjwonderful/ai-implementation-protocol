# GitHub Distribution

This repository can be published to a personal or organization GitHub repository and used as the distribution source for the AIP plugin (Claude Code, Codex, and Grok).

## Publisher Flow

1. Create an empty GitHub repository.
2. Add it as the `origin` remote:

```bash
git remote add origin https://github.com/jzjwonderful/ai-implementation-protocol.git
```

3. Push the repository:

```bash
git push -u origin master
```

4. Create a release when the plugin is ready for a stable version:

```bash
git tag v0.1.0
git push origin v0.1.0
```

## User Install Flow

Users install by cloning the repository and running the **all-in-one** installer (recommended):

```bash
git clone https://github.com/jzjwonderful/ai-implementation-protocol.git
cd ai-implementation-protocol
python scripts/install_all.py
```

On Windows PowerShell:

```powershell
git clone https://github.com/jzjwonderful/ai-implementation-protocol.git
Set-Location ai-implementation-protocol
python .\scripts\install_all.py
```

`install_all.py` copies the engine once to `~/plugins/ai-implementation-protocol/` and installs skills for Claude Code, Codex, and Grok. Subset with `--targets claude,grok` (names: `claude`, `codex`, `grok`, or `all`).

Per-runtime installers remain available: `install_claude_plugin.py`, `install_codex_plugin.py`, `install_grok_plugin.py`.

Skill destinations:

| Runtime | Skills | Extra |
|---------|--------|--------|
| Claude Code | `~/.claude/skills/{aip,root-cause,aip-brainstorm}/` | — |
| Codex | `~/.agents/skills/{aip,root-cause,aip-brainstorm}/` and `$CODEX_HOME/skills` (or `~/.codex/skills`) | updates `~/.agents/plugins/marketplace.json` |
| Grok | `~/.grok/skills/{aip,root-cause,aip-brainstorm}/` | optional `--user-plugin` → `~/.grok/plugins/` |

## Updating An Existing Install

After pulling a newer version:

```bash
git pull
python scripts/install_all.py            # overwrites every installed runtime
# or one runtime:
# python scripts/install_claude_plugin.py --force   # Claude still needs --force to overwrite
# python scripts/install_codex_plugin.py
# python scripts/install_grok_plugin.py
```

## Verification

After installation, confirm these files exist for your runtime:

```text
# shared engine
~/plugins/ai-implementation-protocol/scripts/aip_init.py

# Claude Code
~/plugins/ai-implementation-protocol/.claude-plugin/plugin.json
~/.claude/skills/aip/SKILL.md

# Codex
~/plugins/ai-implementation-protocol/.codex-plugin/plugin.json
~/.agents/skills/aip/SKILL.md
~/.agents/skills/root-cause/SKILL.md
~/.agents/plugins/marketplace.json

# Grok
~/plugins/ai-implementation-protocol/.grok-plugin/plugin.json
~/.grok/skills/aip/SKILL.md
```

Codex users should also confirm the Codex home skill files exist:

```text
$CODEX_HOME/skills/aip/SKILL.md
$CODEX_HOME/skills/root-cause/SKILL.md
$CODEX_HOME/skills/aip-brainstorm/SKILL.md
```

Then restart the tool (or open a new session) and use the `aip` skill.
