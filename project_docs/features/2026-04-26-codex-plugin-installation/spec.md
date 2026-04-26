# Feature Spec

## Summary

Package AIP as a real repo-local Codex plugin so Codex can install it from `.agents/plugins/marketplace.json` and load an `aip` skill from `plugins/ai-implementation-protocol/`.

## Goal

Make the current AIP protocol usable through Codex's plugin system without requiring users to manually discover this repository's root scripts. The plugin must include a valid Codex plugin manifest, a marketplace entry, an AIP skill, and the protocol resources needed by the bundled CLI scripts.

## Problem

The repository had a root-level `plugin.json`, but it was project metadata rather than a Codex plugin manifest. Codex plugins require a `.codex-plugin/plugin.json` inside a plugin directory and a marketplace entry that points to the plugin source. Without those files, AIP can be used manually but cannot be installed as a proper Codex plugin.

## Scope

- Add a repo-local plugin under `plugins/ai-implementation-protocol/`.
- Add `plugins/ai-implementation-protocol/.codex-plugin/plugin.json`.
- Add an `aip` skill under `plugins/ai-implementation-protocol/skills/aip/`.
- Package protocol docs, templates, schemas, and CLI scripts inside the plugin directory so the plugin is self-contained.
- Add `.agents/plugins/marketplace.json` with a local plugin entry.
- Document plugin installation and usage in the repository README.
- Verify the plugin manifest, marketplace file, skill file, and bundled CLI workflow.

## Non-Goals

- Do not publish the plugin to a remote marketplace.
- Do not add MCP servers, hooks, apps, authentication, or external services.
- Do not replace the root-level scripts; keep them available for non-plugin use.
- Do not implement richer validation than the current AIP CLI already provides.

## Constraints

- The plugin must follow the Codex plugin structure: `plugins/<name>/.codex-plugin/plugin.json`.
- The marketplace source path must be repo-relative: `./plugins/ai-implementation-protocol`.
- The plugin must work with Python standard library only.
- AIP feature state must remain complete and pass `aip_check.py`.

## Acceptance Criteria

- `plugins/ai-implementation-protocol/.codex-plugin/plugin.json` is valid JSON and contains no scaffold placeholders.
- `.agents/plugins/marketplace.json` is valid JSON and points to `./plugins/ai-implementation-protocol`.
- `plugins/ai-implementation-protocol/skills/aip/SKILL.md` exists and explains the AIP resume, init, start, resume, and check workflows.
- Plugin-bundled scripts can initialize a temporary repository, create a feature, resume it, and pass `aip_check.py`.
- The root README documents the Codex plugin entry and marketplace path.

## Open Questions

None for this feature. Publishing, icons, screenshots, MCP, hooks, and app integrations are deferred.
