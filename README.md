# AI Implementation Protocol

AI Implementation Protocol (AIP) is a portable workflow for AI-assisted software delivery.

Its purpose is simple:

- preserve requirement context across sessions
- let any AI resume work without guesswork
- reduce implementation quality drop caused by interruption
- enforce handoff quality with local scripts instead of good intentions

This repository contains:

- the protocol itself
- project templates
- local validation scripts
- a Codex plugin package (also usable as a Claude Code skill)
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
python scripts/install_claude_plugin.py --force
```

> **Upgrading from an older AIP?** After updating, re-run `$aip init` (or `python scripts/aip_init.py --repo-root <target>`) once in each AIP-enabled repository to scaffold any missing living docs. `aip init` is idempotent and preserves your existing files; until you do, `aip check` reports them as missing.

The installer copies the plugin package to:

```text
~/plugins/ai-implementation-protocol/
```

and installs the bundled skills to:

```text
~/.claude/skills/aip/SKILL.md
~/.claude/skills/root-cause/SKILL.md
```

`aip` routes `$aip` commands; `root-cause` auto-triggers on bug/unexpected-behavior tasks to drive root-cause investigation and deposit verified causes into `.aip/knowledge.md`.

Open a new Claude Code session after installation. `$aip init` is the only command a human types — everything else (capture, checks, index rebuilds, resuming from the OVERVIEW board) is triggered by the AI at the right moment:

```text
$aip init
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
python scripts/install_codex_plugin.py --force
```

> **Upgrading from an older AIP?** After updating, re-run `$aip init` (or `python scripts/aip_init.py --repo-root <target>`) once in each AIP-enabled repository to scaffold any missing living docs. `aip init` is idempotent and preserves your existing files; until you do, `aip check` reports them as missing.

The installer copies the plugin package to:

```text
~/plugins/ai-implementation-protocol/
```

and creates or updates:

```text
~/.agents/plugins/marketplace.json
```

It also installs the bundled skill entries to:

```text
~/.agents/skills/aip/SKILL.md
~/.agents/skills/root-cause/SKILL.md
```

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

## Repository Layout

- `docs/`: protocol and product docs
- `templates/`: reusable project files
- `scripts/`: local CLI scripts
- `tests/`: unit tests for the scripts
- `plugins/ai-implementation-protocol/`: installable plugin package (Codex + Claude Code)
- `.agents/plugins/marketplace.json`: repo-local Codex marketplace entry
- `adapters/`: optional integrations
- `examples/`: sample project layouts

## Why The Plugin Directory Duplicates Files

`plugins/ai-implementation-protocol/` is the package that gets installed. It intentionally contains its own `docs/`, `templates/`, and `scripts/` copies so the installed plugin can run from `~/plugins/ai-implementation-protocol/` without depending on the original cloned repository path.

The top-level directories remain the single source of truth for developing AIP itself; after editing them, run `python scripts/sync_plugin.py` to regenerate the plugin copies. The plugin directory is the distributable package.

## First Commands

Initialize a target repository (the only command a human runs):

```bash
python scripts/aip_init.py --repo-root <target-project>
```

The remaining scripts are triggered by the AI at the right moment, per the installed `aip` skill:

```bash
python scripts/aip_check.py --repo-root <target-project>      # hygiene gate (also runs in the pre-commit hook)
python scripts/aip_knowledge.py --repo-root <target-project>  # rebuild knowledge_index.md
python scripts/aip_overview.py --repo-root <target-project>   # rebuild the OVERVIEW auto digest
```

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

The plugin provides the `aip` skill and packages its own copy of the protocol docs, templates, and CLI scripts. See `docs/github-distribution.md` for publisher and user installation details.

## Nexus Dependency

AIP does not require Nexus.

If a target project contains `.nexus-map/`, AIP can treat it as an optional knowledge source.
If `.nexus-map/` does not exist, AIP still works.

## Current State

The engine runs on the flat living-doc model (see `.aip/decisions.md`, ADR-2): eight living docs under `.aip/`, an OVERVIEW board for task lines, and `aip check` as the one blocking machine gate.
The next conversation can continue from here without re-deciding the basic architecture.
