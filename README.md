# AI Implementation Protocol

AI Implementation Protocol (AIP) is a portable workflow for AI-assisted software delivery.

Its purpose is simple:

- preserve requirement context across sessions
- let any AI resume work without guesswork
- reduce implementation quality drop caused by interruption
- enforce handoff quality with local scripts instead of good intentions

This repository contains:

- the protocol itself
- project templates
- local validation scripts
- optional adapters such as Nexus integration

## Core Ideas

AIP separates project knowledge into four layers:

1. repository knowledge
2. feature work package
3. machine-readable runtime state
4. local validation tools

Recommended structure inside a target project:

```text
project_docs/
├── _runtime/
│   └── current_task.json
├── features/
│   └── <feature-id>/
│       ├── spec.md
│       ├── plan.md
│       ├── task_board.yaml
│       ├── file_scope.yaml
│       ├── decisions.md
│       ├── handoff.md
│       ├── verification.md
│       └── session_log.md
└── protocols/
    └── ai-implementation-protocol.md
```

## Repository Layout

- `docs/`: protocol and product docs
- `templates/`: reusable project files
- `scripts/`: local CLI scripts
- `schemas/`: machine-readable file schemas
- `adapters/`: optional integrations
- `examples/`: sample project layouts

## First Commands

Initialize a target repository:

```bash
python scripts/aip_init.py --repo-root <target-project>
```

Start a feature:

```bash
python scripts/aip_start_feature.py --repo-root <target-project> --feature-id 2026-04-26-sample-feature
```

Resume work:

```bash
python scripts/aip_resume.py --repo-root <target-project>
```

Validate handoff completeness:

```bash
python scripts/aip_check.py --repo-root <target-project>
```

## Nexus Dependency

AIP does not require Nexus.

If a target project contains `.nexus-map/`, AIP can treat it as an optional knowledge source.
If `.nexus-map/` does not exist, AIP still works.

## Current State

This repository is intentionally scaffolded as a minimal but runnable first version.
The next conversation can continue from here without re-deciding the basic architecture.
