---
name: aip
description: Apply the AI Implementation Protocol (AIP) in this repository. Use when starting, resuming, or closing a feature with discipline, when the user says "aip init / start / resume / check", or to scaffold/maintain the .aip work directory (STATUS, decisions, findings, canonical-assets, feature work packages). Enforces resumable handoffs, machine-gate verification bound to real evidence, fresh-eyes review, reuse-first/anti-accretion, and the side-finding protocol.
---

# AI Implementation Protocol (AIP)

This project uses AIP. All AIP outputs live under the hidden `.aip/` directory.
The AIP engine (CLI) is installed at:

```
{{ENGINE_ROOT}}
```

Run all commands from the **target repository root** via the Bash tool:

```bash
python "{{ENGINE_ROOT}}/scripts/aip.py" <command> --repo-root .
```

## Commands
- `init` — scaffold `.aip/` (STATUS / canonical-assets / decisions / findings / config + runtime).
- `start <YYYY-MM-DD-feature-id> [--title "..."]` — create a feature work package.
- `resume` — print the resume summary (current task / must_read / next action).
- `check` — gate: handoff completeness + project living docs + side-finding classification + machine-gate evidence.

## Required Resume Flow (before editing an AIP repo)
1. Read `.aip/_runtime/current_task.json`.
2. Read every path in `must_read` (includes `.aip/STATUS.md` and the project's truth sources from `.aip/config.yaml`).
3. Inspect the active feature's `task_board.yaml`.
4. Read the active feature's `handoff.md`.
5. Only then plan or edit.

If `.aip/_runtime/current_task.json` does not exist, run `init` first.

## Working Rules (the safeguards — apply throughout)
- **Stop-and-ask**: on uncertainty / spec gap / ambiguity, stop and put it to the user. Never guess and continue.
- **Reuse-first / anti-accretion**: before creating any new tool/scaffold, refresh the project index and check `.aip/canonical-assets.md`; creating new needs written justification. Replacing old → migrate consumers and delete in the same change.
- **Side-finding protocol**: an unrelated problem found mid-task → 3-second triage (blocking → fold in/ask; trivial+same-blast-radius → fix inline; else → log to `.aip/findings.md` and keep going). Never silently drop, never derail.
- **Comment hygiene**: no drift-prone external ids in code comments (requirement #, plan line #, section #); reference only immutable `ADR-N`.
- **Doc same-change**: behavior/architecture change → update `.aip/STATUS.md` (and the relevant truth source) in the same change; record architectural decisions in `.aip/decisions.md`.
- **Respect project config**: honor `.aip/config.yaml` iron_rules / lenses / gates; when a change touches a `lenses` domain, mount that checklist during design and review.

## Completion Gate (do not call a feature done until)
- `verification.md` has a **machine-gate table bound to real evidence** — every gate in `config.yaml` actually run, result pass + evidence (run them via Bash; nothing skipped silently).
- An **independent fresh-eyes review** is recorded (reviewer mindset ≠ author; try to falsify).
- Every `.aip/findings.md` entry added this round is **classified** (no `待分类`).
- `handoff.md` has all required sections; `task_board.yaml` has ≤1 in_progress.
- `python "{{ENGINE_ROOT}}/scripts/aip.py" check --repo-root .` passes.
- Commits still require explicit user authorization.
