# Examples

## C++ / Qt Project

Use AIP for:

- tracking multi-session refactors in track files
- recording verified root causes (crashes, races) in the knowledge base
- a decision log for architecture trade-offs
- machine-check evidence (build/tests) bound to "done"

Good fit:

- desktop applications
- embedded tooling
- protocol-heavy systems

## Python Service

Use AIP for:

- API change tracking
- resuming a migration across sessions
- incident root-cause follow-up
- multi-agent implementation

## Frontend Project

Use AIP for:

- design-spec alignment
- change-scope tracking in the work line's track file
- browser verification notes

## Common Pattern

Across all examples, the same structure stays stable:

- one hidden `.aip/` directory
- one track file per work line (next step + read-first list), deleted when the line is done; the session-start hook prints the live ones
- knowledge and decisions as one file per item, never renumbered
- one blocking `aip check`
