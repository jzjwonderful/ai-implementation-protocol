# Feature Spec

## Summary

Bootstrap the first runnable AIP core for this repository by defining the supported workflow, locking the scope of the four local CLI scripts, and proving that the end-to-end protocol flow works in a temporary target repository.

## Goal

Provide a minimal but usable AIP baseline that any Python-capable repository can adopt locally to initialize protocol files, create a feature work package, resume the active feature context, and validate handoff completeness without depending on Nexus, CI, or Git integrations.

## Problem

The repository README already positions AIP as a runnable first version, but the active feature package does not yet describe what "runnable" means for this milestone. Without a concrete spec and verification record, future work can drift into either under-defined documentation or overbuilt tooling.

## Scope

- Define this milestone as the "minimal runnable" AIP core, not the fully extended protocol.
- Treat the current local scripts as the supported workflow surface:
  - `scripts/aip_init.py`
  - `scripts/aip_start_feature.py`
  - `scripts/aip_resume.py`
  - `scripts/aip_check.py`
- Document the expected behavior of each script and the repository artifacts they create or consume.
- Align the feature package files so another AI can resume this repository state without guesswork.
- Verify the workflow end-to-end in a temporary target directory using the current repository as the template root.

## Non-Goals

- Do not add CI integration, Git automation, or remote service dependencies.
- Do not make `.nexus-map/` or any adapter a hard requirement.
- Do not implement full JSON Schema validation inside `aip_check.py` for this milestone.
- Do not add automatic task-board progression, agent orchestration, or UI layers.

## Constraints

- The bootstrap flow must remain usable with Python standard library only.
- The protocol copy written into a target repository must come from this repository's checked-in docs and templates.
- The minimal workflow must succeed in a plain local directory without network access or external daemons.
- The feature package must end in a state that passes `scripts/aip_check.py`.

## Acceptance Criteria

- A temporary repository can be initialized with `python scripts/aip_init.py --repo-root <temp-dir>`.
- A feature work package can be created with `python scripts/aip_start_feature.py --repo-root <temp-dir> --feature-id <id> --title <title>`.
- The resume summary produced by `python scripts/aip_resume.py --repo-root <temp-dir>` shows the active feature, status, phase, next action, blockers, and must-read files.
- `python scripts/aip_check.py --repo-root <temp-dir>` passes after the generated feature package exists.
- The active feature documents in `project_docs/features/2026-04-26-bootstrap-aip-core/` describe the chosen scope, verification evidence, and next follow-up direction.

## Open Questions

None for this milestone. Stronger schema-aware validation, adapter hooks, and richer resume output are intentionally deferred to later features.
