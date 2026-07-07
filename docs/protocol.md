# AI Implementation Protocol

## Goal

AI Implementation Protocol (AIP) defines the minimal records that let any AI resume a task without requirement drift, hidden assumptions, or quality loss.

## Output Location

All AIP outputs in a target repository live under a single hidden directory `.aip/` (like `.git`). Nothing is scattered into the project root.

## Project-Level Living Docs

AIP keeps project state in a small set of living docs (cross-task, long-lived) under `.aip/`. There are **no per-feature work-package directories and no runtime pointer** — task state lives on the OVERVIEW board.

- `OVERVIEW.md` — multi-line board (hand-written top) + auto-generated digest. Read this first when starting or resuming any work.
- `decisions.md` — architecture/direction-level decision log (append-only).
- `knowledge.md` (+ the derived `knowledge_index.md`) — verified root causes and pitfalls.
- `reference.md` — domain concepts/terms, core invariants, and reusable implementations (the canonical pick).
- `inbox.md` — side-finding inbox (problems hit while doing something unrelated).
- `conventions.md` — project conventions (standing how-we-work rules).
- `config.yaml` — project adaptation (truth sources / machine-check commands / lenses / iron rules).

`aip init` creates these, and `aip check` validates their presence (the derived `knowledge_index.md` counts as required too).

### Retired slots (must not reappear)

Earlier AIP versions used per-feature packages, a runtime pointer, and a separate bug track. Those are gone. `aip check` treats these filenames as **forbidden anywhere in the repo** (a migration guard): `current_task.json`, `task_board.yaml`, `handoff.md`, `verification.md`, `session_log.md`, `report.md`, `file_scope.yaml`, `STATUS.md`, `findings.md`, `canonical-assets.md`. Their roles moved: current state → `OVERVIEW.md`; side-findings → `inbox.md`; reusable-asset registry → `reference.md`.

## Resume / Onboarding

Any AI starting or resuming work:

1. Read `OVERVIEW.md`, find the `▶[active]` line, read its **next step** and `must_read`.
2. Read every file listed in `must_read` (includes `decisions.md` and `knowledge_index.md`).
3. Only then start — don't replay history.

## Capture + Completion Check

### Two capture paths

- **Main path** — a pitfall/root cause hit during the task → confirm with the `root-cause` skill → write to `knowledge.md` (`状态: draft` while evidence is incomplete; `active` once the review checklist passes — the AI promotes autonomously but must notify).
- **Side path** — a problem unrelated to the current task → search `knowledge.md` + `inbox.md` first → if new, file it in `inbox.md` (don't blindly append).

### Write discipline (all sedimentation)

Run the review checklist (next section) → write → notify the user in-session (which docs changed, a one-line reason each) → the edit lands in the same git commit as the work. There is no pre-approval gate: the human audits after the fact via the notification plus git diff, which is why skipping the notification is forbidden.

- `状态: draft` marks an entry the AI itself is not yet sure of (evidence incomplete); `active` means the review checklist passed. The AI may write `active` directly but must state the evidence in the notification.
- Only **verified** items enter knowledge; guesses and side-issues go to `inbox.md`.
- **Overturning a decision/convention** — past decisions are not iron law: an AI that finds one no longer fits current needs is expected to say so and correct it. The only mechanism is appending a new entry marked "supersedes ADR-N" with the reason; the old entry is flagged superseded, never rewritten or deleted in place.
- **Deleting/merging existing content** — the only two valid reasons are "proven wrong" and "duplicate of another entry"; "unused this round" is not one. The notification must name what was removed and why.

### Review checklist (`aip review`, soft quality)

The goal is always **doc quality**, never content volume: clear, accurate, necessary, minimal — when in doubt, write less. Run it entry-by-entry before writing any living doc, and over the whole `.aip/` on `$aip review`:

1. Read the target doc in full (not just the tail); merge or cross-link near-duplicates instead of adding.
2. Only write facts verified first-hand (ran the command, read the code, reproduced it); mark uncertain items `draft` or file them in `inbox.md`.
3. Necessity: could a new AI six months from now read this and act without asking anyone? If not, rewrite; if still not, drop it.
4. Minimal: one entry states one thing; don't restate what git history or the code itself derives.
5. Right slot: pitfalls/root causes → knowledge; concepts/reusables → reference; standing rules → conventions; side-issues → inbox; direction → decisions. A misplaced entry is worse than none.
6. Afterwards run `aip check` and rebuild the derived files (`aip knowledge` / `aip overview`).

A full-`.aip/` review triggers when any of: the change deletes or merges content; ≥3 entries changed at once; more than a month since the last review (per `.aip/` git history); the user runs `$aip review` (unconditional). Findings are reported as *problem + suggested edit + reason + impact* before applying. `aip review` owns doc quality only — problem analysis stays with the `root-cause` skill; they don't overlap.

### Completion check (when a work line is done)

**Tier 1 (every time a line wraps up):**

1. Run `aip check` (red blocks the commit; fix item by item).
2. Scoped correction: tidy only the entries you touched this round and their direct links (checklist-reviewed and notified; no silent edits outside the line's scope).
3. Capture sweep: list what you concretely learned/hit this round — into knowledge / inbox / reference / conventions / config?
4. Rebuild derived files: `aip knowledge` (index) and `aip overview` (digest).
5. Move the line off the OVERVIEW board.

**Tier 2 (on an architecture/trade-off decision):** append one record to `decisions.md` (context, decision, rationale, impact) so it isn't re-litigated later.

## `aip check` (the one machine check)

`aip check` (`python scripts/aip_check.py --repo-root .`) validates:

1. **Living docs present** — the living docs above exist under `.aip/`.
2. **Index consistent** — `knowledge_index.md` matches the current `knowledge.md` (rebuild with `aip knowledge` if not).
3. **Knowledge fields complete** — each entry's required fields (分类 / 状态 / 症状 / 根因 / 适用范围 / 最后复核) are non-empty.
4. **No legacy residue** — none of the forbidden filenames appear in the repo.
5. **Dual-copy sync** (engine repo only) — the synced top-level sources (`scripts/`, `docs/`, `templates/`, `VERSION`) match the `plugins/ai-implementation-protocol/` copies byte-for-byte, with no stale extras on the plugin side (rebuild with `sync_plugin.py` if not; the compare logic lives once, in `sync_plugin.drift`, which `sync_plugin.py --check` also runs).

Exit 0 = pass; non-zero = violations listed on stdout.

## `aip doctor` (diagnosis, non-blocking)

`aip doctor` (`python scripts/aip_doctor.py --repo-root .`) checks install/environment health — advisory, while `aip check` stays the one blocking gate. Four areas: project `.aip/` health (including knowledge entries whose `最后复核` is >90 days old — WARN only), install health (plugin package, skill files, installed VERSION vs engine VERSION), hook health (pre-commit present, AIP-managed, engine path still valid), and engine-repo dual-copy sync. Output is graded ERROR (AIP unusable) / WARN (drift risk or degraded experience) / INFO (optional), each with a fix command; exit 1 only on ERROR. The installers print the doctor command after a successful install.

## Commands (AI-autonomous; the human only runs init)

Day-to-day actions (capture, check, review, rebuild index/digest, read OVERVIEW to resume) are triggered by the AI at the right moment — the human doesn't type them. The human runs one command once per new repo:

```
python scripts/aip_init.py --repo-root .
```

`aip init` has two phases. **Phase A** is the deterministic script above: scaffold the living docs, write the guide blocks, install hooks, rebuild derived files — idempotent, existing files are never overwritten. **Phase B** is AI-driven and runs immediately after: the AI analyzes the project itself (README, build/dependency manifests, test dirs, CI config, directory layout — it never interrogates the user; zero-config means "don't ask", not "don't know"), then fills **only files still in template or empty state** — build/test commands into `config.yaml` gates, core concepts and directory roles into `reference.md`, established practices into `conventions.md`. For legacy/test-less projects it records "no tests — start with characterization tests" as a known gap on the OVERVIEW board instead of inventing tests. Phase B must end with an init summary: what was detected / what was written per file / what's uncertain / what the user should confirm.

**Three reliability layers:** hooks (`install_hooks.py` adds a git pre-commit that runs `aip check`), the completion check, and onboarding (read the OVERVIEW active line on every resume). The concrete command lines and the phase→skill mapping are single-sourced in the installed `aip` skill, not duplicated here (drift prevention).

## External-Tool Degradation Chain

When looking up references / finding an equivalent implementation / searching an index, pick the simplest tool that matches:

1. LSP available → `findReferences` / `incomingCalls` (precise).
2. No LSP → grep + read candidates + check `reference.md` (good enough).
3. Large codebase → nexus-query / CodeGraph (if installed).

AIP doesn't record which external tools are installed (the platform lists what's available each session). Adapter outputs (a nexus index, CI records) may enrich inputs, but the protocol stays fully usable without them.

## Cross-cutting disciplines

- **输出语言风格** — 面向用户的回答与说明（不含代码、命令、文件内容）遵守四条：
  1. **用中文**；专业技术名词可保留英文（commit、build、lint、token 等），不硬翻。
  2. **说大白话，不用黑话**；不生造词、不堆抽象比喻。能用日常说法讲清楚就用日常说法；
     必须用专业术语或协议内部术语时，第一次出现要用一句话说明它指什么，不直接甩术语让人去猜。
  3. **专业、客观，以事实和结果为准**；不说恭维话、不自夸、不用"很棒/好问题"这类填充。
     结论先行再给依据；不确定就直说不确定，不糊弄。
  4. **第一性原理思考**；遇到问题先拆到最基本的事实和约束，从那里推导，而不是照搬惯例。
     能质疑的前提就质疑，能去掉的步骤就去掉。
- **Comment hygiene** — code comments must not reference drift-prone external ids
  (requirement #, plan line #, doc section #). Reference only immutable anchors (`ADR-N`,
  i.e. Architecture Decision Record entries; likewise `K-NNN` knowledge and `I-N` inbox ids).
- **Refresh manual indexes before query** — codegraph/nexus/etc. are manually updated;
  refresh before querying or a stale index misleads you into creating duplicates.
- **Conditional domain lenses** — when a change touches a domain declared in `config.yaml`
  `lenses` (e.g. frontend, industrial client), mount that expert checklist during design and review.

### Process-skill integration (optional method layer)

AIP owns the **slots** (living docs, state, checks); an external process-skill framework, when present, owns the **methods** (how to fill each slot well). They compose:

- Slots belong to AIP; a method's output lands in the AIP slot, never a parallel location.
- **Resume is AIP-only**: the `OVERVIEW.md` active line (next step + `must_read`) is the single resumable-state source. Any external "execute the plan in a separate session" checkpointing maps onto the OVERVIEW board, not a second progress/plan file.
- AIP runs standalone if no method layer is present.
- The concrete phase→skill mapping is single-sourced in the installed `aip` skill.

### Enforcement (load-bearing vs advisory)

What is load-bearing is enforced by **deterministic checks that block**, not prose:

- **Scaffold** (`aip init`) creates the living docs in the one correct place — no location drift.
- **`aip check`** is a blocking check: living docs present, knowledge index consistent and fields complete, no forbidden legacy files, dual-copy synced. A hook runs it automatically.
- **Hooks** (`install_hooks.py`): git pre-commit (+ optional Claude Stop) run `aip check` so it can't be forgotten.

Method *quality* (was the investigation deep, the review real) can't be machine-forced — the checks verify the *residue* a method must leave (verified causes, sources cited, in-session notification of every doc edit, the git trail). Beyond residue it is best-effort by design: a poorly executed method leaves an incomplete slot the check rejects.

## Optional Knowledge Sources

If present, these may be consumed as enhancement inputs:

- `.nexus-map/`
- git history
- CI records

They are optional. The protocol itself stays usable without them.
