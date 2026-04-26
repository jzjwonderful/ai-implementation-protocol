---
name: aip
description: Use when a repository should follow AI Implementation Protocol, including initializing project_docs, starting a feature package, resuming current task state, validating handoff completeness, or closing a feature according to AIP.
---

# AI Implementation Protocol

Use this skill to apply AIP from the installed Codex plugin.

## Plugin Root

Resolve the plugin root as two directories above this file:

```text
<plugin-root>/skills/aip/SKILL.md
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
python <plugin-root>/scripts/aip_init.py --repo-root . --template-root <plugin-root>
```

Start a feature:

```bash
python <plugin-root>/scripts/aip_start_feature.py --repo-root . --feature-id YYYY-MM-DD-short-feature-id --title "Human readable title" --template-root <plugin-root>
```

Resume current work:

```bash
python <plugin-root>/scripts/aip_resume.py --repo-root .
```

Validate handoff completeness:

```bash
python <plugin-root>/scripts/aip_check.py --repo-root .
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
- `python <plugin-root>/scripts/aip_check.py --repo-root .` passes.
