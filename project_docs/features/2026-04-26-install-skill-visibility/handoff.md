# Handoff

## Current Phase

Done

## Current Task

Fix installer so the `aip` skill is visible in Codex after installation.

## Completed Work

- Confirmed the plugin was installed under `~/plugins/ai-implementation-protocol/`.
- Confirmed marketplace was installed under `~/.agents/plugins/marketplace.json`.
- Identified that Codex Desktop also loads custom skills from `~/.agents/skills/`.
- Updated installer to write `~/.agents/skills/aip/SKILL.md`.
- Updated docs and skill instructions for home-skill loading.
- Reinstalled into the current user home with `--force`.

## Remaining Work

Restart Codex so the newly installed `aip` skill is discovered.

## Blockers

None.

## Next Action

Restart Codex and check for the `aip` skill. If it still does not appear, inspect Codex startup/plugin logs for skill discovery errors.

## Files Touched

- `scripts/install_codex_plugin.py`
- `plugins/ai-implementation-protocol/skills/aip/SKILL.md`
- `plugins/ai-implementation-protocol/README.md`
- `README.md`
- `docs/github-distribution.md`
- `project_docs/features/2026-04-26-install-skill-visibility/`
- `project_docs/_runtime/current_task.json`

## Verification Status

Temporary-home install and current-user `--force` install both created `.agents/skills/aip/SKILL.md`. Repository-local `python scripts/aip.py check --repo-root .` passed after closeout.

## Notes For Next AI

The root cause was not missing plugin files; it was missing direct registration in the user skill directory that this Codex environment loads.
