# AI Implementation Protocol

AI Implementation Protocol (AIP) is a portable workflow for AI-assisted software delivery.

Its purpose is simple:

- preserve requirement context across sessions
- let any AI resume work without guesswork
- reduce implementation quality drop caused by interruption
- enforce handoff quality with local scripts instead of good intentions

This repository contains:

- the protocol itself
- a plugin package that ships three skills (`aip`, `root-cause`, `aip-brainstorm`) for Claude Code, Codex and Grok — scripts and templates travel inside the `aip` skill
- local validation scripts
- optional adapters such as Nexus integration

## Install (all supported AIs)

One command installs the shared engine plus skills for **Claude Code, Codex, and Grok**:

```bash
git clone https://github.com/jzjwonderful/ai-implementation-protocol.git
cd ai-implementation-protocol
python scripts/install_all.py
```

Update an existing install (re-running always overwrites):

```bash
git pull
python scripts/install_all.py
```

Only some runtimes:

```bash
python scripts/install_all.py --targets claude,grok
# legal names: claude, codex, grok, or all
```

Optional Grok user-plugin registration (`~/.grok/plugins/`):

```bash
python scripts/install_all.py --user-plugin
```

Engine package always lands at:

```text
~/plugins/ai-implementation-protocol/
```

Skills land at:

```text
~/.claude/skills/{aip,root-cause,aip-brainstorm}/   # Claude Code
~/.agents/skills/{aip,root-cause,aip-brainstorm}/   # Codex
~/.grok/skills/{aip,root-cause,aip-brainstorm}/     # Grok
```

Codex also updates `~/.agents/plugins/marketplace.json`. `aip` routes `$aip` commands; `root-cause` auto-triggers on bug/unexpected-behavior tasks and deposits verified causes into `.aip/knowledge.md`; `aip-brainstorm` lets AIs in multiple terminals hold a turn-based discussion through a shared topic document in `.aip/brainstorm/`.

> **Upgrading from an older AIP?** After updating, re-run `$aip init` (or `python ~/.claude/skills/aip/scripts/aip_init.py --repo-root <target>`) once in each AIP-enabled repository. It scaffolds missing living docs and upgrades the marked AIP guide blocks in `AGENTS.md`/`CLAUDE.md`; it preserves existing living docs and project-owned content. Until you do, the repository may still use the older onboarding rules.

Open a new session in each tool after installation. `$aip init` is the only command a human types — everything else is AI-triggered:

```text
$aip init
```

Per-runtime installers below are still available if you only want one tool.

## Install Into One Project

Instead of the user home, the skills can live inside a single repository and travel with it:

```bash
python scripts/install_all.py --project /path/to/repo     # Claude Code + Codex
python scripts/install_claude_plugin.py --project /path/to/repo   # → <repo>/.claude/skills/
python scripts/install_codex_plugin.py --project /path/to/repo    # → <repo>/.codex/skills/
```

Everyone who clones that repository then gets the same engine version, with no personal install. The
installer prints the follow-up steps: repoint that repository's hooks at the in-repo copy, then run
`/aip init` (or `$aip init`) once. Grok has no established project-level skill directory, so
`--project` covers Claude Code and Codex only.

## Install For Claude Code Only

```bash
python scripts/install_claude_plugin.py
# update: re-run the same command (existing files are replaced)
```

Skills → `~/.claude/skills/{aip,root-cause,aip-brainstorm}/`, whole directories, nothing under `~/plugins/`.

## Install For Codex Only

```bash
python scripts/install_codex_plugin.py
# update: re-run the same command (existing files are replaced)
```

Skills → `~/.agents/skills/`, and to `$CODEX_HOME/skills` (or `~/.codex/skills` when `CODEX_HOME` is unset); also updates `~/.agents/plugins/marketplace.json`. Existing AIP install files are replaced by default.

## Install For Grok Only

```bash
python scripts/install_grok_plugin.py
# update: re-run the same command (existing files are replaced)
# optional user plugin: python scripts/install_grok_plugin.py --user-plugin
```

Skills → `~/.grok/skills/`. Optional `--user-plugin` also copies to `~/.grok/plugins/`.

> **Upgrading from an older AIP?** After updating, run `/aip init` (Claude Code) or `$aip init` (Codex / Grok)
> once in each AIP-enabled repository. It scaffolds any missing living docs and refreshes the hooks — including
> repointing hooks that older versions aimed at `~/plugins/.../scripts/`, which 0.3.0 moved into the `aip` skill.
> `aip init` is idempotent and preserves your existing files.

## Core Ideas

AIP keeps project state in a small set of **living docs** (cross-task, long-lived) plus local validation scripts. There are no per-feature work packages and no runtime pointer — task state lives on the OVERVIEW board.

All AIP outputs inside a target project live under a single hidden `.aip/` directory (like `.git`):

```text
.aip/
├── OVERVIEW.md               # multi-line board + auto digest (read first)
├── decisions.md              # ADR-lite decision log (append-only)
├── knowledge.md              # verified root causes / gotchas (append-only, recall-first)
├── knowledge_index.md        # generated catalog of knowledge.md (rebuilt via `aip knowledge`)
├── reference.md              # domain concepts, core invariants, reusable implementations
├── inbox.md                  # side-finding inbox (capture, don't chase)
├── conventions.md            # standing how-we-work rules
└── config.yaml               # project adaptation (truth sources / gates / lenses)
```

The AIP docs are project-level and committed. The AI's own cross-session memory (e.g. Claude Code's) is personal and stays on one machine; project facts go to `.aip/` only, user preferences stay in the tool's memory. Only the main agent writes `.aip/`; subagents report back. See `docs/protocol.md`.

## Repository Layout

- `docs/`: protocol and product docs
- `plugins/ai-implementation-protocol/`: the installable package (Claude Code + Codex + Grok)
  - `skills/aip/`: the engine skill — `SKILL.md`, `reference/` (details loaded on demand), `scripts/` (CLI), `templates/`, `VERSION`
  - `skills/root-cause/`: the root-cause investigation skill
  - `skills/aip-brainstorm/`: the multi-terminal multi-AI discussion skill
- `scripts/`: installers and uninstaller only
- `tests/`: unit tests for the scripts
- `.agents/plugins/marketplace.json`: repo-local Codex marketplace entry
- `adapters/`: optional integrations
- `examples/`: sample project layouts

There is exactly one copy of the engine (scripts + templates) in this repository: inside the `aip` skill. Edit it there — not in `~/.claude/skills/` or `~/plugins/` — and re-run the installer.

## First Commands

Initialize a target repository (the only command a human runs; in Claude Code just type `/aip init`):

```bash
python ~/.claude/skills/aip/scripts/aip_init.py --repo-root <target-project>
```

The remaining scripts are triggered by the AI at the right moment, per the installed `aip` skill:

```bash
python ~/.claude/skills/aip/scripts/aip_check.py --repo-root <target-project>      # hygiene gate (also runs in the pre-commit hook)
python ~/.claude/skills/aip/scripts/aip_knowledge.py --repo-root <target-project>  # rebuild knowledge_index.md
python ~/.claude/skills/aip/scripts/aip_overview.py --repo-root <target-project>   # rebuild the OVERVIEW auto digest
python ~/.claude/skills/aip/scripts/aip_doctor.py --repo-root <target-project>     # install/environment health check
```

For Codex, replace `~/.claude/skills/aip` with `~/.agents/skills/aip` (or `$CODEX_HOME/skills/aip`).

## Codex Plugin Internals

This repository can also be used as a repo-local Codex plugin during development.

Plugin entry:

```text
plugins/ai-implementation-protocol/.codex-plugin/plugin.json
```

Repo-local marketplace:

```text
.agents/plugins/marketplace.json
```

See `docs/github-distribution.md` for publisher and user installation details.

## Nexus Dependency

AIP does not require Nexus.

If a target project contains `.nexus-map/`, AIP can treat it as an optional knowledge source.
If `.nexus-map/` does not exist, AIP still works.

## Current State

The engine runs on the flat living-doc model (see `.aip/decisions.md`, ADR-2): eight living docs under `.aip/`, an OVERVIEW board for task lines, and `aip check` as the one blocking machine gate. Since 0.3.0 (ADR-4) the engine lives inside the `aip` skill directory and is installed as one unit.
