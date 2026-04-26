# Architecture

## Overview

AIP has four layers.

### 1. Protocol Layer

Human and machine rules that define:

- required files
- allowed statuses
- handoff format
- resume behavior
- validation expectations

Key files:

- `docs/protocol.md`
- `schemas/*.json`

### 2. Template Layer

Reusable markdown, JSON, and YAML templates that seed a target repository.

Key files:

- `templates/*.md`
- `templates/*.json`
- `templates/*.yaml`

### 3. Tooling Layer

Local scripts that enforce protocol correctness.

Key scripts:

- `aip_init.py`
- `aip_start_feature.py`
- `aip_resume.py`
- `aip_check.py`

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
- adapters may not be required for feature continuity

## Why This Architecture

This split keeps the product portable:

- protocol can evolve independently
- templates can be customized per project
- scripts can stay small and deterministic
- adapters can vary by environment
