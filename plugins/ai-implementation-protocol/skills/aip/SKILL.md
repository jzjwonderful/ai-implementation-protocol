---
name: aip
description: Use when the user invokes `$aip` or asks to apply AI Implementation Protocol, including `$aip init`, `$aip start`, `$aip resume`, `$aip check`, initializing project_docs, starting a feature package, resuming current task state, validating handoff completeness, or closing a feature according to AIP.
---

# AI Implementation Protocol

Use this skill to apply AIP from the installed Codex plugin.

## Command Invocation

When the user invokes this skill with a command-like prompt, treat the text after `$aip` as arguments and execute the matching AIP action.

Supported forms:

```text
$aip init
$aip start 2026-04-26-my-feature --title "My feature"
$aip resume
$aip check
$aip help
```

Aliases:

- `$aip create <feature-id>` means `$aip start <feature-id>`.
- `$aip validate` means `$aip check`.
- `$aip status` means `$aip resume`.

If no command is provided, run the resume flow when AIP is already initialized. If AIP is not initialized, explain that `$aip init` is the first command.

If arguments are missing, ask for only the missing required argument. For example, `$aip start` requires a feature id.

## Plugin Root

Resolve the plugin root based on where this skill is loaded from.

If this file is loaded from the plugin package, the plugin root is two directories above this file:

```text
<plugin-root>/skills/aip/SKILL.md
```

If this file is loaded from a home-local skill install such as:

```text
~/.agents/skills/aip/SKILL.md
~/.claude/skills/aip/SKILL.md
```

then use the installed plugin package at:

```text
~/plugins/ai-implementation-protocol/
```

The plugin root contains:

- `docs/`: protocol and architecture references
- `templates/`: feature and runtime templates
- `schemas/`: machine-readable schema references
- `scripts/`: local CLI tools

## Required Resume Flow

Before editing an AIP-enabled repository:

1. Read `project_docs/_runtime/current_task.json`.
2. Read every path listed in `must_read`.
3. Inspect the active feature's `task_board.yaml`.
4. Read the active feature's `handoff.md`.
5. Only then plan or edit.

If `project_docs/_runtime/current_task.json` does not exist, initialize AIP first.

## CLI Commands

Run commands from the target repository root. Use the plugin copy of the scripts as the tool source.

Initialize AIP:

```bash
python <plugin-root>/scripts/aip.py init --repo-root .
```

Start a feature:

```bash
python <plugin-root>/scripts/aip.py start YYYY-MM-DD-short-feature-id --title "Human readable title" --repo-root .
```

Resume current work:

```bash
python <plugin-root>/scripts/aip.py resume --repo-root .
```

Validate handoff completeness:

```bash
python <plugin-root>/scripts/aip.py check --repo-root .
```

Show command help:

```bash
python <plugin-root>/scripts/aip.py --help
```

## Routing Rules

- `$aip init`: run `python <plugin-root>/scripts/aip.py init --repo-root .`.
- `$aip start <feature-id> [--title "..."]`: run `python <plugin-root>/scripts/aip.py start <feature-id> --title "..." --repo-root .`.
- `$aip resume`: run `python <plugin-root>/scripts/aip.py resume --repo-root .`.
- `$aip check`: run `python <plugin-root>/scripts/aip.py check --repo-root .`.
- `$aip help`: summarize these commands and do not edit files.

Preserve explicit `--repo-root <path>` if the user provides it. Otherwise use the current workspace root.

After running a command, report the command outcome and the next AIP action from the output or `current_task.json`.

## Examples

Initialize the current repository:

```text
$aip init
```

Create a new feature package:

```text
$aip start 2026-04-26-add-billing --title "Add billing"
```

Resume the active feature:

```text
$aip resume
```

Run the handoff completeness gate:

```text
$aip check
```

## Working Rules

- Keep one active feature pointer in `project_docs/_runtime/current_task.json`.
- After meaningful changes, update `task_board.yaml`, append `session_log.md`, and refresh `handoff.md`.
- Before claiming completion, update `verification.md`, update `handoff.md`, update `current_task.json`, and run `aip_check.py`.
- Keep adapters optional. A repository without `.nexus-map/`, CI records, or Git metadata must still work.
- Use existing project-specific constraints when they are stricter than the default protocol.

## Completion Gate

Do not call an AIP feature complete until:

- `current_task.json` has the intended final status.
- The active feature directory contains all required files.
- `handoff.md` contains all required sections.
- `task_board.yaml` has no more than one `in_progress` task.
- `python <plugin-root>/scripts/aip.py check --repo-root .` passes.
