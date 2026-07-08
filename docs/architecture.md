# Architecture

## Overview

AIP has four layers.

### 1. Protocol Layer

Human and machine rules that define:

- the required living docs
- capture and completion discipline
- resume behavior
- validation expectations (`aip check`)

Key files:

- `docs/protocol.md`
- the installed `aip` skill (single source for command lines and phase→skill mapping)

### 2. Template Layer

Reusable markdown, JSON, and YAML templates that seed a target repository.

Key files:

- `templates/*.md`
- `templates/*.json`
- `templates/*.yaml`

### 3. Tooling Layer

Local scripts that enforce protocol correctness.

Key scripts:

- `aip_init.py` — scaffold `.aip/` (zero-config)
- `aip_check.py` — the blocking validation check
- `aip_doctor.py` — non-blocking install/environment health check (advisory)
- `aip_knowledge.py` — rebuild the knowledge index
- `aip_overview.py` — rebuild the OVERVIEW digest
- `install_hooks.py` — install the git pre-commit (+ optional Claude Stop) hook
- `sync_plugin.py` — regenerate the plugin copies from the top-level sources

### 4. Adapter Layer

Optional integrations with external systems.

Examples:

- Nexus knowledge map
- git metadata
- CI pipelines

## Design Constraint

Adapters must never become hard dependencies of the protocol.

That means:

- AIP must work in a plain repository with Python only
- adapters may enrich resume output or validation
- adapters may not be required for resuming work

## Why This Architecture

This split keeps the product portable:

- protocol can evolve independently
- templates can be customized per project
- scripts can stay small and deterministic
- adapters can vary by environment
