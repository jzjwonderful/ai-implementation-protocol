# AI Implementation Protocol

## Goal

AI Implementation Protocol defines how work must be recorded so any AI can resume a task without requirement drift, hidden assumptions, or quality loss.

## Mandatory Objects

Every active feature must have:

- one feature directory under `project_docs/features/<feature-id>/`
- one runtime pointer at `project_docs/_runtime/current_task.json`
- one task board with explicit statuses
- one handoff file with a fixed structure

## Mandatory Lifecycle

### Before implementation

Required:

- `spec.md`
- `plan.md`
- `task_board.yaml`
- `file_scope.yaml`
- `current_task.json`

### During implementation

After each meaningful task update:

- update `task_board.yaml`
- append `session_log.md`
- update `handoff.md`

### Before claiming completion

Required:

- update `verification.md`
- update `handoff.md`
- update `current_task.json`
- pass `aip_check.py`

## Required Handoff Sections

Every `handoff.md` must include:

- current phase
- current task
- completed work
- remaining work
- blockers
- next action
- files touched
- verification status

## Allowed Status Values

Task board task statuses:

- `pending`
- `in_progress`
- `blocked`
- `done`

Feature runtime statuses:

- `planned`
- `in_progress`
- `blocked`
- `done`

## Resume Rule

Any AI resuming work must:

1. read `current_task.json`
2. read the files listed under `must_read`
3. inspect `task_board.yaml`
4. read `handoff.md`
5. only then begin editing or planning

## Optional Knowledge Sources

If present, these may be consumed as enhancement inputs:

- `.nexus-map/`
- git history
- CI records

They are optional. The protocol itself must remain usable without them.
