# Feature Spec

## Summary

Prepare the AIP Codex plugin for distribution through a user-owned GitHub repository.

## Goal

Let other users clone the GitHub repository and install the AIP Codex plugin into their own local Codex plugin directory with a single Python command.

## Problem

The repository now contains a valid repo-local Codex plugin, but users outside this checkout still need a clear, repeatable installation flow. Without an installer and publishing guide, each user would have to manually copy the plugin and edit `~/.agents/plugins/marketplace.json`.

## Scope

- Add a standard-library installer for cloned GitHub repositories.
- Copy `plugins/ai-implementation-protocol/` into the user's home-local plugin directory.
- Create or update `~/.agents/plugins/marketplace.json`.
- Document publisher and user installation flows.
- Verify installation in a temporary home directory.

## Non-Goals

- Do not create GitHub releases automatically.
- Do not publish to an official OpenAI marketplace.
- Do not add package-manager distribution.

## Constraints

- The installer must run with Python standard library only.
- The installer must not require a known GitHub repository URL.
- Existing installed plugin directories must only be replaced when `--force` is provided.
- Verification must not modify the real user home plugin directory.

## Acceptance Criteria

- `scripts/install_codex_plugin.py` installs from a cloned repository into `<home>/plugins/ai-implementation-protocol/`.
- The installer creates or updates `<home>/.agents/plugins/marketplace.json`.
- Re-running against an existing install without `--force` fails safely.
- Re-running with `--force` replaces the installed plugin.
- README and `docs/github-distribution.md` explain publisher and user flows.

## Open Questions

None. The GitHub repository URL is `https://github.com/jzjwonderful/ai-implementation-protocol`.
