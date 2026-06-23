# Feature Plan

## Phase Overview

1. Add a unified AIP CLI router.
2. Teach the installed `aip` skill how to route `$aip` subcommands.
3. Update user-facing docs.
4. Verify root and plugin router behavior.

## File Structure

- `scripts/aip.py`
  Root command router for local terminal usage.
- `plugins/ai-implementation-protocol/scripts/aip.py`
  Plugin-packaged command router used by the `aip` skill.
- `plugins/ai-implementation-protocol/skills/aip/SKILL.md`
  Parameterized skill command routing rules.
- `README.md`
  User-facing `$aip` examples and terminal command updates.
- `plugins/ai-implementation-protocol/README.md`
  Plugin-local `$aip` examples.
- `plugin.json`
  Project metadata listing the new router script.

## Tasks

### Task 1

- scope:
  Add the `aip.py` command router.
- files:
  - `scripts/aip.py`
  - `plugins/ai-implementation-protocol/scripts/aip.py`
- verification:
  Run `python scripts/aip.py --help` and end-to-end router commands in a temporary repository.

### Task 2

- scope:
  Update skill and docs for `$aip` parameterized usage.
- files:
  - `plugins/ai-implementation-protocol/skills/aip/SKILL.md`
  - `README.md`
  - `plugins/ai-implementation-protocol/README.md`
  - `plugin.json`
- verification:
  Confirm docs include `$aip init`, `$aip start`, `$aip resume`, and `$aip check`.

### Task 3

- scope:
  Close the AIP feature.
- files:
  - `project_docs/features/2026-04-26-aip-skill-command-router/*`
  - `project_docs/_runtime/current_task.json`
- verification:
  Run `python scripts/aip.py check --repo-root .`.

## Risks

- Skill invocation parsing is performed by Codex, so the skill must be explicit about how to interpret text after `$aip`.
- `aip.py` is a router and does not replace the underlying scripts; future changes should keep both paths aligned.

## Rollback Notes

Remove `scripts/aip.py`, remove `plugins/ai-implementation-protocol/scripts/aip.py`, and revert the skill and README command examples to individual scripts.
