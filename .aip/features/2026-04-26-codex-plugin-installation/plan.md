# Feature Plan

## Phase Overview

1. Define Codex plugin support as a repo-local, self-contained plugin package.
2. Add the Codex plugin manifest, marketplace entry, AIP skill, and packaged resources.
3. Verify the plugin structure and bundled CLI flow.
4. Close the AIP feature with handoff and verification evidence.

## File Structure

- `.agents/plugins/marketplace.json`
  Repo-local Codex marketplace entry for the AIP plugin.
- `plugins/ai-implementation-protocol/.codex-plugin/plugin.json`
  Codex plugin manifest.
- `plugins/ai-implementation-protocol/skills/aip/SKILL.md`
  Skill instructions loaded by Codex after plugin installation.
- `plugins/ai-implementation-protocol/scripts/`
  Plugin-packaged copies of AIP CLI tools.
- `plugins/ai-implementation-protocol/docs/`
  Plugin-packaged protocol references.
- `plugins/ai-implementation-protocol/templates/`
  Plugin-packaged templates used by the scripts.
- `plugins/ai-implementation-protocol/schemas/`
  Plugin-packaged schema references.
- `README.md`
  Repository-facing plugin installation and usage notes.

## Tasks

### Task 1

- scope:
  Create the Codex plugin shape and marketplace registration.
- files:
  - `.agents/plugins/marketplace.json`
  - `plugins/ai-implementation-protocol/.codex-plugin/plugin.json`
- verification:
  Parse both JSON files and check that no `[TODO:` scaffold placeholders remain.

### Task 2

- scope:
  Package AIP as a self-contained plugin capability.
- files:
  - `plugins/ai-implementation-protocol/skills/aip/SKILL.md`
  - `plugins/ai-implementation-protocol/scripts/*.py`
  - `plugins/ai-implementation-protocol/docs/*.md`
  - `plugins/ai-implementation-protocol/templates/*`
  - `plugins/ai-implementation-protocol/schemas/*.json`
- verification:
  Run the plugin-bundled scripts with `--template-root plugins/ai-implementation-protocol` against a temporary repository.

### Task 3

- scope:
  Document the plugin and close the AIP feature.
- files:
  - `README.md`
  - `project_docs/features/2026-04-26-codex-plugin-installation/*`
  - `project_docs/_runtime/current_task.json`
- verification:
  Run repository-local `aip_check.py` after the feature is marked done.

## Risks

- Codex plugin UI behavior may still depend on the host Codex version, but the repository now has the expected plugin manifest and marketplace structure.
- The plugin packages copies of root resources, so future changes to root scripts or templates should be synchronized into `plugins/ai-implementation-protocol/`.

## Rollback Notes

Remove `.agents/plugins/marketplace.json` and `plugins/ai-implementation-protocol/` to return to manual-script-only usage. Keep root `scripts/`, `docs/`, `templates/`, and `schemas/` unchanged.
