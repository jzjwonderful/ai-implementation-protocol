# AI Implementation Protocol

AI Implementation Protocol (AIP) is a portable workflow for AI-assisted software delivery.

Its purpose is simple:

- preserve requirement context across sessions
- let any AI resume work without guesswork
- reduce implementation quality drop caused by interruption
- enforce handoff quality with local scripts instead of good intentions

This repository contains:

- the protocol itself
- a plugin package that ships two skills (`aip`, `root-cause`) for Claude Code and Codex — scripts and templates travel inside the `aip` skill
- local validation scripts
- optional adapters such as Nexus integration

## Install For Claude Code

Install from GitHub:

```bash
git clone https://github.com/jzjwonderful/ai-implementation-protocol.git
cd ai-implementation-protocol
python scripts/install_claude_plugin.py
```

Update an existing local install:

```bash
git pull
python scripts/install_claude_plugin.py
```

> **Upgrading from an older AIP?** After updating, run `/aip init` (or `python ~/.claude/skills/aip/scripts/aip_init.py --repo-root <target>`) once in each AIP-enabled repository to scaffold any missing living docs and refresh the hooks. `aip init` is idempotent and preserves your existing files; until you do, `aip check` reports them as missing.

The installer copies the whole skill directories to:

```text
~/.claude/skills/aip/          # SKILL.md + reference/ + scripts/ + templates/ + VERSION
~/.claude/skills/root-cause/
```

Existing AIP install files are replaced. Nothing is written to `~/plugins/` any more; an old copy there is harmless and can be deleted if you only use Claude Code.

`aip` routes `/aip` commands; `root-cause` auto-triggers on bug/unexpected-behavior tasks to drive root-cause investigation and deposit verified causes into `.aip/knowledge.md`.

Open a new Claude Code session after installation. `/aip init` is the only command a human types — everything else (capture, checks, index rebuilds, resuming from the OVERVIEW board) is triggered by the AI at the right moment:

```text
/aip init
```

## Install The Codex Plugin

Install from GitHub:

```bash
git clone https://github.com/jzjwonderful/ai-implementation-protocol.git
cd ai-implementation-protocol
python scripts/install_codex_plugin.py
```

Update an existing local install:

```bash
git pull
python scripts/install_codex_plugin.py
```

> **Upgrading from an older AIP?** After updating, run `$aip init` once in each AIP-enabled repository, as above.

The installer copies the plugin package to:

```text
~/plugins/ai-implementation-protocol/
```

and creates or updates:

```text
~/.agents/plugins/marketplace.json
```

It also installs the whole skill directories to:

```text
~/.agents/skills/aip/
~/.agents/skills/root-cause/
```

The installer also writes the same skill directories to `$CODEX_HOME/skills` when `CODEX_HOME` is set, otherwise `~/.codex/skills`. Existing AIP install files are replaced by default.

Restart Codex or refresh the plugin list after installation. The installed plugin provides the `aip` and `root-cause` skills.

Use it from Codex the same way — `$aip init` once per repo, the rest is AI-triggered:

```text
$aip init
```

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
- `plugins/ai-implementation-protocol/`: the installable package (Codex + Claude Code)
  - `skills/aip/`: the engine skill — `SKILL.md`, `reference/` (details loaded on demand), `scripts/` (CLI), `templates/`, `VERSION`
  - `skills/root-cause/`: the root-cause investigation skill
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
