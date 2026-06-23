# Feature Plan

## Phase Overview

1. Identify why installed plugin files do not make the skill visible.
2. Install the `aip` skill into the user skill directory during plugin installation.
3. Verify both temporary and current-user installs.
4. Close the AIP feature.

## File Structure

- `scripts/install_codex_plugin.py`
  Adds direct skill installation under `.agents/skills/aip`.
- `plugins/ai-implementation-protocol/skills/aip/SKILL.md`
  Documents both plugin-package and home-skill loading paths.
- `README.md`
  Documents the installed skill path.
- `docs/github-distribution.md`
  Documents verification of the installed skill path.
- `plugins/ai-implementation-protocol/README.md`
  Documents Codex versions that load user skills from `.agents/skills`.

## Tasks

### Task 1

- scope:
  Update the installer to write `~/.agents/skills/aip/SKILL.md`.
- files:
  - `scripts/install_codex_plugin.py`
- verification:
  Run the installer against a temporary home directory and confirm the skill file exists.

### Task 2

- scope:
  Update docs and skill instructions for home-skill loading.
- files:
  - `plugins/ai-implementation-protocol/skills/aip/SKILL.md`
  - `README.md`
  - `docs/github-distribution.md`
  - `plugins/ai-implementation-protocol/README.md`
- verification:
  Confirm docs mention `~/.agents/skills/aip/SKILL.md`.

### Task 3

- scope:
  Reinstall into the current user home and close the feature.
- files:
  - `project_docs/features/2026-04-26-install-skill-visibility/*`
  - `project_docs/_runtime/current_task.json`
- verification:
  Run `python scripts/install_codex_plugin.py --force` and `python scripts/aip.py check --repo-root .`.

## Risks

- Codex may still require a full app restart before newly installed skills are discovered.
- Future Codex versions may load plugin skills directly, but this compatibility install remains harmless.

## Rollback Notes

Remove the `install_skill` step from `scripts/install_codex_plugin.py` and delete `~/.agents/skills/aip/` from affected machines if direct skill installation is no longer desired.
