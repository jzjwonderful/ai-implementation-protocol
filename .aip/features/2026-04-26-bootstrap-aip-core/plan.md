# Feature Plan

## Phase Overview

1. Freeze the milestone definition for the minimal runnable AIP core.
2. Verify the current script set against the defined workflow in a temporary repository.
3. Record verification evidence and close the feature with a complete handoff.

## File Structure

- `project_docs/features/2026-04-26-bootstrap-aip-core/spec.md`
  Defines the milestone scope, goals, non-goals, and acceptance criteria.
- `project_docs/features/2026-04-26-bootstrap-aip-core/plan.md`
  Captures the execution sequence for closing this bootstrap feature.
- `project_docs/features/2026-04-26-bootstrap-aip-core/task_board.yaml`
  Tracks the active phase and task completion state.
- `project_docs/features/2026-04-26-bootstrap-aip-core/file_scope.yaml`
  Constrains work to repository docs, templates, schemas, scripts, and feature artifacts relevant to the bootstrap flow.
- `project_docs/features/2026-04-26-bootstrap-aip-core/handoff.md`
  Summarizes completed work, residual follow-up, and verification state for the next AI.
- `project_docs/features/2026-04-26-bootstrap-aip-core/verification.md`
  Stores the exact commands and results used to prove the workflow.
- `project_docs/_runtime/current_task.json`
  Advertises whether this feature is still active or has been completed.

## Tasks

### Task 1

- scope:
  Write the repository-facing definition of what "minimal runnable AIP core" means for this feature.
- files:
  - `project_docs/features/2026-04-26-bootstrap-aip-core/spec.md`
  - `project_docs/features/2026-04-26-bootstrap-aip-core/plan.md`
  - `project_docs/features/2026-04-26-bootstrap-aip-core/file_scope.yaml`
  - `project_docs/features/2026-04-26-bootstrap-aip-core/decisions.md`
- verification:
  Cross-check the written scope against `README.md`, `docs/protocol.md`, `docs/architecture.md`, and the current `scripts/*.py` behavior.

### Task 2

- scope:
  Validate the end-to-end bootstrap workflow in a temporary target repository using the existing CLI scripts.
- files:
  - `project_docs/features/2026-04-26-bootstrap-aip-core/verification.md`
  - `project_docs/features/2026-04-26-bootstrap-aip-core/session_log.md`
- verification:
  Run `aip_init.py`, `aip_start_feature.py`, `aip_resume.py`, and `aip_check.py` against a temporary directory and record the observed outputs.

### Task 3

- scope:
  Close the feature package cleanly after verification by updating runtime state, handoff status, and task tracking.
- files:
  - `project_docs/features/2026-04-26-bootstrap-aip-core/handoff.md`
  - `project_docs/features/2026-04-26-bootstrap-aip-core/task_board.yaml`
  - `project_docs/_runtime/current_task.json`
- verification:
  Re-run `aip_check.py` for the repository feature state and confirm the handoff contains all required sections.

## Risks

- `aip_check.py` only performs structural checks, so some semantic mistakes can still pass this milestone.
- The bootstrap proof depends on a local Python environment being available in the user's shell.
- The generated target repository state is intentionally generic and may need project-specific template customization later.

## Rollback Notes

If verification exposes a script mismatch, reopen this feature as `in_progress`, fix the affected script or template in place, and re-run the temporary-repository workflow before marking the feature done.
