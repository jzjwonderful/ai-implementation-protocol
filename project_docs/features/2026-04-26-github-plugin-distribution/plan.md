# Feature Plan

## Phase Overview

1. Add a home-local installer for users who clone the GitHub repository.
2. Document how the owner publishes the repository and how users install or update the plugin.
3. Verify the installer against a temporary home directory.
4. Close the AIP feature with evidence.

## File Structure

- `scripts/install_codex_plugin.py`
  Installs the plugin from a cloned repository into a user's home-local Codex plugin directory.
- `docs/github-distribution.md`
  Documents GitHub publishing, user installation, updates, and verification.
- `README.md`
  Adds the quick GitHub installation path.
- `plugins/ai-implementation-protocol/README.md`
  Notes how the plugin is installed from a cloned repository.
- `project_docs/features/2026-04-26-github-plugin-distribution/`
  Tracks this change according to AIP.

## Tasks

### Task 1

- scope:
  Add the installer.
- files:
  - `scripts/install_codex_plugin.py`
- verification:
  Run the installer with `--home <temp-home>` and confirm copied plugin files and marketplace entry.

### Task 2

- scope:
  Document GitHub distribution.
- files:
  - `README.md`
  - `docs/github-distribution.md`
  - `plugins/ai-implementation-protocol/README.md`
- verification:
  Confirm docs include publisher push flow, user install flow, and update flow.

### Task 3

- scope:
  Close the AIP feature.
- files:
  - `project_docs/features/2026-04-26-github-plugin-distribution/*`
  - `project_docs/_runtime/current_task.json`
- verification:
  Run `python scripts/aip_check.py --repo-root .`.

## Risks

- Users still need Git and Python available locally.
- Codex may require restart or plugin refresh after marketplace changes.
- Documentation uses placeholders until the real GitHub remote is configured.

## Rollback Notes

Remove `scripts/install_codex_plugin.py` and `docs/github-distribution.md`, then revert README additions to return to manual plugin installation only.
