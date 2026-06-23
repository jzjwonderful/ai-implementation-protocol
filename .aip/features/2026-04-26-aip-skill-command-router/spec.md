# Feature Spec

## Summary

Make the installed `aip` Codex skill behave like a parameterized command router so users can invoke commands such as `$aip init`, `$aip start`, `$aip resume`, and `$aip check`.

## Goal

Let users operate AIP from Codex with memorable skill commands while also providing an equivalent terminal command router through `scripts/aip.py`.

## Problem

The plugin already installs an `aip` skill, but the skill primarily describes the protocol and lists individual scripts. Users expect to invoke `$aip` with subcommands and arguments, rather than manually translating intent into script paths.

## Scope

- Add a unified `aip.py` CLI router with `init`, `start`, `resume`, and `check` subcommands.
- Package the same router inside the Codex plugin.
- Update the `aip` skill to route `$aip <command>` invocations.
- Document supported command forms and aliases.
- Verify the router end-to-end in a temporary repository.

## Non-Goals

- Do not add shell completions.
- Do not add network or GitHub operations to `$aip`.
- Do not add feature closing automation beyond the existing `check` gate.

## Constraints

- The router must use Python standard library only.
- The plugin skill must preserve normal AIP resume rules.
- Existing individual scripts must continue to work.

## Acceptance Criteria

- `$aip init` is documented and maps to the plugin-bundled router.
- `$aip start <feature-id> --title "..."` is documented and maps to feature creation.
- `$aip resume` is documented and maps to current task summary.
- `$aip check` is documented and maps to handoff validation.
- `python scripts/aip.py init/start/resume/check` works against a temporary repository.

## Open Questions

None.
