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
- a Codex plugin package
- optional adapters such as Nexus integration

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

The installer copies the plugin package to:

```text
~/plugins/ai-implementation-protocol/
```

and creates or updates:

```text
~/.agents/plugins/marketplace.json
```

Restart Codex or refresh the plugin list after installation. The installed plugin provides the `aip` skill.

Use it from Codex with command-like skill prompts:

```text
$aip init
$aip start 2026-04-26-my-feature --title "My feature"
$aip resume
$aip check
```

## Core Ideas

AIP separates project knowledge into four layers:

1. repository knowledge
2. feature work package
3. machine-readable runtime state
4. local validation tools

Recommended structure inside a target project:

```text
project_docs/
├── _runtime/
│   └── current_task.json
├── features/
│   └── <feature-id>/
│       ├── spec.md
│       ├── plan.md
│       ├── task_board.yaml
│       ├── file_scope.yaml
│       ├── decisions.md
│       ├── handoff.md
│       ├── verification.md
│       └── session_log.md
└── protocols/
    └── ai-implementation-protocol.md
```

## Repository Layout

- `docs/`: protocol and product docs
- `templates/`: reusable project files
- `scripts/`: local CLI scripts
- `schemas/`: machine-readable file schemas
- `plugins/ai-implementation-protocol/`: installable Codex plugin package
- `.agents/plugins/marketplace.json`: repo-local Codex marketplace entry
- `adapters/`: optional integrations
- `examples/`: sample project layouts

## Why The Plugin Directory Duplicates Files

`plugins/ai-implementation-protocol/` is the package Codex installs. It intentionally contains its own `docs/`, `templates/`, `schemas/`, and `scripts/` copies so the installed plugin can run from `~/plugins/ai-implementation-protocol/` without depending on the original cloned repository path.

The top-level directories remain the source project layout for developing AIP itself. The plugin directory is the distributable Codex package.

## First Commands

Initialize a target repository:

```bash
python scripts/aip.py init --repo-root <target-project>
```

Start a feature:

```bash
python scripts/aip.py start 2026-04-26-sample-feature --repo-root <target-project>
```

Resume work:

```bash
python scripts/aip.py resume --repo-root <target-project>
```

Validate handoff completeness:

```bash
python scripts/aip.py check --repo-root <target-project>
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

The plugin provides the `aip` skill and packages its own copy of the protocol docs, templates, schemas, and CLI scripts. See `docs/github-distribution.md` for publisher and user installation details.

## Nexus Dependency

AIP does not require Nexus.

If a target project contains `.nexus-map/`, AIP can treat it as an optional knowledge source.
If `.nexus-map/` does not exist, AIP still works.

## Current State

This repository is intentionally scaffolded as a minimal but runnable first version.
The next conversation can continue from here without re-deciding the basic architecture.
