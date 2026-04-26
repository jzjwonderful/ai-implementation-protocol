# Feature Spec

## Summary

Make `python scripts/install_codex_plugin.py` install the `aip` skill into Codex's user skill directory so it appears after restart.

## Goal

After installing AIP from GitHub, users should see and invoke the `aip` skill in Codex without manually copying skill files.

## Problem

The installer copied the plugin package to `~/plugins/ai-implementation-protocol/` and updated `~/.agents/plugins/marketplace.json`, but the current Codex Desktop environment also discovers user skills directly from `~/.agents/skills/`. Because the installer did not write `~/.agents/skills/aip/SKILL.md`, the plugin files existed but the `aip` skill was not visible.

## Scope

- Update the installer to copy the `aip` skill into `~/.agents/skills/aip/SKILL.md`.
- Keep the plugin package install and marketplace update behavior.
- Update docs to explain the skill install path.
- Verify in a temporary home directory and the current user home.

## Non-Goals

- Do not remove plugin marketplace installation.
- Do not change the `$aip` command vocabulary.
- Do not depend on Codex private cache directories.

## Constraints

- The installer must remain Python standard-library only.
- Existing installs must still require `--force` before replacement.
- The installed skill must point users back to the plugin package for scripts and templates.

## Acceptance Criteria

- Installer creates `~/.agents/skills/aip/SKILL.md`.
- Installer still creates `~/plugins/ai-implementation-protocol/`.
- Installer still creates or updates `~/.agents/plugins/marketplace.json`.
- Temporary-home install verification passes.
- Current-user `--force` reinstall creates the missing skill file.

## Open Questions

None.
