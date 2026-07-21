# Project Adaptation Guide

## Objective

Adapt AIP to any software project without rewriting the protocol.

## Integration Model

The target project receives a single hidden `.aip/` directory containing:

- project-level living docs (`OVERVIEW.md`, `decisions.md`, `knowledge.md` + `knowledge_index.md`, `reference.md`, `inbox.md`, `conventions.md`, `config.yaml`)
- optional `.nexus-map/` linkage

Task state lives on the `OVERVIEW.md` board — there is no per-feature directory and no runtime pointer.

## Engine vs Config

AIP is the project-agnostic **engine** (protocol + CLI + check). A project binds it by editing
one file — `.aip/config.yaml` — declaring its truth sources, machine-check commands, applicable
domain lenses, index tools, and iron rules. Porting AIP to a new project = fill that config; no
protocol or script changes.

## Recommended Steps

1. Run `aip init` (scaffolds `.aip/` and installs the git pre-commit hook; zero-config)
2. Add a work line to `OVERVIEW.md` when you start something; track its next step + `must_read` there
3. Fill `.aip/config.yaml` as you go — truth sources, machine-check commands, lenses, iron rules (captured when first needed, not asked upfront)
4. Keep `aip check` running via the hook (or add it to CI); run `aip doctor` any time to check install/environment health

## Install Targets

- **All at once (recommended)**: `python scripts/install_all.py` — one engine copy under `~/plugins/` plus
  skills for Claude Code, Codex, and Grok. Subset with `--targets claude,grok` (or `codex`, or `all`).
- **Codex only**: `python scripts/install_codex_plugin.py` (skills to `~/.agents/skills` and
  `$CODEX_HOME/skills` / `~/.codex/skills`; existing AIP install files are replaced by default).
- **Claude Code only**: `python scripts/install_claude_plugin.py` (skills to `~/.claude/skills/`).
- **Grok only**: `python scripts/install_grok_plugin.py` (skills to `~/.grok/skills/`;
  optional `--user-plugin` → `~/.grok/plugins/`).

The same plugin package serves all three runtimes; they drive the same tool-agnostic CLI under `scripts/`.

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

- `must_read` files per work line
- machine-check commands and verification notes
- repository-specific conventions
- CI policy

Projects should not customize:

- the `.aip/` output location
- the living-doc set and their roles
- the forbidden-filename guard (no per-feature packages, no runtime pointer)

## Nexus Integration

If the target repository contains `.nexus-map/INDEX.md`, add it to `must_read`.
If it does not exist, skip it.

No failure should occur if Nexus is absent.
