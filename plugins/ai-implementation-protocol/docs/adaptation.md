# Project Adaptation Guide

## Objective

Adapt AIP to any software project without rewriting the protocol.

## Integration Model

The target project receives:

- `project_docs/`
- runtime state files
- feature work package directories
- optional `.nexus-map/` linkage

## Recommended Steps

1. Run `aip_init.py`
2. Review `project_docs/protocols/ai-implementation-protocol.md`
3. Create the first feature with `aip_start_feature.py`
4. Update project-specific read lists and commands if needed
5. Add `aip_check.py` to local workflow or CI

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
