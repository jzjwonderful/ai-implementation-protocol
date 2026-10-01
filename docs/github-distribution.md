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

Users install by cloning the repository and installing **into each project** (recommended — the skills travel with the repository, everyone gets the same version, and each repository upgrades on its own schedule; see "Installing Into One Project" below):

```bash
git clone https://github.com/jzjwonderful/ai-implementation-protocol.git
cd ai-implementation-protocol
python3 scripts/install_all.py --project /path/to/repo
```

A whole-machine install drops `--project`:

```bash
python3 scripts/install_all.py
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
| Claude Code | `~/.claude/skills/aip/` | nothing goes to `~/plugins/` |
| Codex | `~/.agents/skills/aip/` and `$CODEX_HOME/skills` (or `~/.codex/skills`) | updates `~/.agents/plugins/marketplace.json` |
| Grok | `~/.grok/skills/aip/` | optional `--user-plugin` → `~/.grok/plugins/` |

Every installer copies the **whole** skill directory, so the `aip` skill's `scripts/`, `templates/`, `reference/` and `VERSION` always sit next to its `SKILL.md`. Installing over an older version also removes the `root-cause` and `aip-brainstorm` skills that AIP shipped before 0.6.0. The `~/plugins/` copy that Codex and Grok keep is the packaged source they install from; the single-runtime Claude installer does not use it.

## Installing Into One Project (recommended)

```bash
python3 scripts/install_all.py --project /path/to/repo
```

The skills land in `<repo>/.claude/skills/` and `<repo>/.codex/skills/` and are committed with that
repository, so everyone who clones it gets the same engine version without a personal install. Nothing
is written to `~/plugins/` or the marketplace. Grok has no project-level skill directory, so this
covers Claude Code and Codex only. A machine-wide install upgrades every repository at once — including ones
mid-migration or on an old layout, whose hooks point at the shared copy — so prefer this per-project form.

## Updating An Existing Install

A project-level install updates itself: `/aip update` in that repository, then commit the skill directories.
For a whole-machine install, after pulling a newer version:

```bash
git pull
python3 scripts/install_all.py            # overwrites every installed runtime
# or one runtime:
# python3 scripts/install_claude_plugin.py
# python3 scripts/install_codex_plugin.py
# python3 scripts/install_grok_plugin.py
```

## Verification

After installation, confirm these files exist for your runtime:

```text
# packaged engine (Codex / Grok install from here)
~/plugins/ai-implementation-protocol/skills/aip/scripts/aip_init.py

# Claude Code
~/.claude/skills/aip/SKILL.md
~/.claude/skills/aip/scripts/aip_init.py

# Codex
~/plugins/ai-implementation-protocol/.codex-plugin/plugin.json
~/.agents/skills/aip/SKILL.md
~/.agents/skills/aip/scripts/aip_init.py
~/.agents/plugins/marketplace.json

# Grok
~/plugins/ai-implementation-protocol/.grok-plugin/plugin.json
~/.grok/skills/aip/SKILL.md
~/.grok/skills/aip/scripts/aip_init.py
```

Codex users should also confirm the Codex home skill file exists:

```text
$CODEX_HOME/skills/aip/SKILL.md
```

Then restart the tool (or open a new session) and use the `aip` skill.
