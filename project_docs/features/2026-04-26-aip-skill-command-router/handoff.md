# Handoff

## Current Phase

Done

## Current Task

Parameterized `$aip` skill command routing completed.

## Completed Work

- Added `scripts/aip.py` as a root AIP command router.
- Added `plugins/ai-implementation-protocol/scripts/aip.py` as the plugin-packaged router.
- Updated `plugins/ai-implementation-protocol/skills/aip/SKILL.md` to route `$aip init`, `$aip start`, `$aip resume`, `$aip check`, and aliases.
- Updated README docs and plugin prompts to show `$aip` command-style usage.
- Verified root and plugin router flows against temporary repositories.

## Remaining Work

None inside this feature scope.

## Blockers

None.

## Next Action

Commit and push the router update so installed users can pull and reinstall with `python scripts/install_codex_plugin.py --force`.

## Files Touched

- `scripts/aip.py`
- `plugins/ai-implementation-protocol/scripts/aip.py`
- `plugins/ai-implementation-protocol/skills/aip/SKILL.md`
- `plugins/ai-implementation-protocol/.codex-plugin/plugin.json`
- `plugins/ai-implementation-protocol/README.md`
- `README.md`
- `plugin.json`
- `project_docs/features/2026-04-26-aip-skill-command-router/`
- `project_docs/_runtime/current_task.json`

## Verification Status

Root router and plugin router both passed `init -> start -> resume -> check` flows against temporary repositories. Repository-local `python scripts/aip.py check --repo-root .` passed after closeout.

## Notes For Next AI

`$aip` command aliases live in the skill instructions. The terminal CLI intentionally supports only canonical subcommands: `init`, `start`, `resume`, and `check`.
