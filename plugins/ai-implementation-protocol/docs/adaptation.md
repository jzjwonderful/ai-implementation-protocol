# Project Adaptation Guide

## Objective

Adapt AIP to any software project without rewriting the protocol.

## Integration Model

The target project receives a single hidden `.aip/` directory containing:

- project-level living docs (`STATUS.md`, `canonical-assets.md`, `decisions.md`, `findings.md`, `config.yaml`)
- runtime state files (`_runtime/current_task.json`)
- feature work package directories (`features/<id>/`)
- optional `.nexus-map/` linkage

## Engine vs Config

AIP is the project-agnostic **engine** (protocol + CLI + check). A project binds it by editing
one file — `.aip/config.yaml` — declaring its truth sources, machine-gate commands, applicable
domain lenses, index tools, and iron rules. Porting AIP to a new project = fill that config; no
protocol or script changes.

## Recommended Steps

1. Run `aip init` (scaffolds `.aip/`)
2. Fill `.aip/config.yaml` (truth sources / gate commands / lenses / iron rules)
3. Review `.aip/protocols/ai-implementation-protocol.md`
4. Create the first feature with `aip start <feature-id>`
5. Add `aip check` to local workflow or CI

## Install Targets

- **Codex**: `python scripts/install_codex_plugin.py` (installs the `aip` plugin + skill).
- **Claude Code**: `python scripts/install_claude_code.py --repo-root <target>` (installs an `aip`
  skill into the target's `.claude/skills/`; add `--user` for `~/.claude/skills/`).

Both drive the same tool-agnostic CLI under `scripts/`.

### Enforcement hooks (make `aip check` automatic)

```bash
python scripts/install_hooks.py --repo-root <target>            # git pre-commit gate
python scripts/install_hooks.py --repo-root <target> --claude-stop  # + non-blocking Claude Stop hook
```

The git pre-commit hook blocks commits when `aip check` fails (bypass once with `git commit --no-verify`).
This is the level that turns "the AI should" into "the commit is blocked unless." Load-bearing rules are
enforced by the deterministic check; method *quality* stays best-effort (gates check only the residue a
method must leave). See `docs/protocol.md` → Enforcement.

## Project-Specific Customization

Projects may customize:

- required read files
- default verification commands
- repository-specific notes
- CI policy

Projects should not customize:

- core status vocabulary
- current task runtime shape
- handoff required sections

## Nexus Integration

If the target repository contains `.nexus-map/INDEX.md`, add it to `must_read`.
If it does not exist, skip it.

No failure should occur if Nexus is absent.
