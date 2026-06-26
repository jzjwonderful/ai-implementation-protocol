# Examples

## C++ / Qt Project

Use AIP for:

- tracking multi-session refactors on the OVERVIEW board
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
- change-scope tracking on the board
- browser verification notes

## Common Pattern

Across all examples, the same structure stays stable:

- one hidden `.aip/` directory
- one OVERVIEW board holding work-line state (next step + `must_read`)
- one append-only knowledge base and decision log
- one blocking `aip check`
