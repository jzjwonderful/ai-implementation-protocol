# AI Implementation Protocol

## Goal

AI Implementation Protocol defines how work must be recorded so any AI can resume a task without requirement drift, hidden assumptions, or quality loss.

## Output Location

All AIP outputs in a target repository live under a single hidden directory `.aip/`
(like `.git`). Nothing is scattered into the project root.

## Mandatory Objects

Project-level living docs (cross-feature, long-lived) under `.aip/`:

- `STATUS.md` — current-state source of truth (read first on resume)
- `canonical-assets.md` — registry of assets to reuse (anti-accretion)
- `decisions.md` — ADR-lite decision log (append-only)
- `findings.md` — side-finding inbox (capture, don't chase)
- `config.yaml` — project adaptation (truth sources / machine-gate commands / lenses)

Every active feature must have:

- one feature directory under `.aip/features/<feature-id>/`
- one runtime pointer at `.aip/_runtime/current_task.json`
- one task board with explicit statuses
- one handoff file with a fixed structure

## Work-Unit Kinds

A work unit is either a **feature** (new development) or a **bug** (fix, light track).
`current_task.json.kind` distinguishes them (absent ⇒ `feature`, backward-compatible).

A **bug** package is lighter: it drops `spec.md` / `plan.md` / `task_board.yaml` and tracks
progress through `current_task.current_phase` (`investigate` → `fix` → `verify`). Its core
living doc is `report.md` (症状/复现 → 竞争假设 → 根因+证据 → 触类旁通 · 同类波及面 → 修复选项 →
沉淀). Verification adds a `## Regression` gate (a repro that failed before and passes after).

Bug completeness gate (`aip check`, status==done): 根因 + 证据 + 同类波及面 + 沉淀 节非空；
`resolution==fixed` 时必有回归证据；`resolution` ∈ {fixed, wont_fix, by_design}. Pure
"won't fix / by-design" closes via `resolution` without a regression gate but still requires
a root cause. The bug track binds the `root-cause` skill (Safeguard #9) to a resumable work unit.

## Mandatory Lifecycle

### Before implementation

Required:

- `spec.md`
- `plan.md`
- `task_board.yaml`
- `file_scope.yaml`
- `current_task.json`

### During implementation

After each meaningful task update:

- update `task_board.yaml`
- append `session_log.md`
- update `handoff.md`

### Before claiming completion

Required:

- update `verification.md` with a **machine-gate table bound to real evidence**
  (every gate declared in `config.yaml` run, result pass/fail + evidence; nothing skipped silently)
- record an **independent (fresh-eyes) review** result in `verification.md`
- every `findings.md` entry added this round is **classified** (no `待分类` left)
- update `handoff.md`, update `current_task.json`
- pass `aip_check.py`

## Required Handoff Sections

Every `handoff.md` must include:

- current phase
- current task
- completed work
- remaining work
- blockers
- next action
- files touched
- verification status

## Allowed Status Values

Task board task statuses:

- `pending`
- `in_progress`
- `blocked`
- `done`

Feature runtime statuses:

- `planned`
- `in_progress`
- `blocked`
- `done`

## Resume Rule

Any AI resuming work must:

1. read `.aip/_runtime/current_task.json`
2. read the files listed under `must_read` (includes `.aip/STATUS.md` and the project's truth sources)
3. inspect `task_board.yaml`
4. read `handoff.md`
5. only then begin editing or planning

## Safeguard Mechanisms

These make delivery resist the recurring failures of AI-assisted work — wrong guesses,
silent omissions, entropy/accretion, and getting derailed. They are tool-agnostic; a
project binds them via `config.yaml`.

1. **Machine gates bound to real evidence** — "done" is hard-bound to the `config.yaml`
   gate commands actually passing (tests/build/lint-or-drift/e2e), not to paperwork being
   filled in. `aip_check` enforces it.
2. **Stop-and-ask** — on any uncertainty / spec gap / ambiguity, stop and put it to the
   user as a decision item. Never guess and continue; wrong guesses are the root cause of
   repeated corrections.
3. **Fresh-eyes review** — verification includes an independent review (reviewer ≠ author)
   with a falsification mindset; no rubber-stamping one's own work.
4. **Traceability / no silent drop** — numbered acceptance criteria tracked to completion;
   `task_board` allows ≤1 in-progress task; nothing claimed done that wasn't verified.
5. **Thin slices** — split large work into end-to-end independently-acceptable slices; earlier
   feedback is cheaper.
6. **ADR-lite decisions** — architecture/trade-off decisions recorded with rationale in
   `decisions.md` so they aren't re-litigated.
7. **Reuse-first & anti-accretion** — before creating any new tool/scaffold, refresh the
   project index and search `canonical-assets.md`; creating new requires written justification.
   Replacing old scaffolds follows Strangler (migrate consumers, delete in the same change).
8. **Side-finding protocol** — unrelated problems found while doing task A are captured in
   `findings.md` (capture, don't chase) with a 3-second triage, never silently dropped and
   never allowed to derail the current task. Boundary: a sibling site sharing the **same root
   cause** as the bug being fixed is *not* a side-finding — it is in-scope and handled under
   #9's sweep; only genuinely *unrelated* problems go here.
9. **Root-cause-first investigation & knowledge sedimentation** — on any bug/unexpected
   behavior, don't patch the symptom: recall known causes from `.aip/knowledge_index.md`
   (a hit is a prior hypothesis to re-verify, not an answer), enumerate competing
   hypotheses, dig to a cause you can point at in code/config/environment, then hand the
   cause + evidence + options to the user. Verified causes are deposited (append-only) in
   `.aip/knowledge.md` under a declared `## 类目`; the derived `.aip/knowledge_index.md` is
   rebuilt via `aip knowledge`. `aip check` validates index consistency (always), entry
   completeness + legal category (done gate), and flags entries unverified for >180 days.
   Once a cause is confirmed, **generalize it (触类旁通)**: treat it as a defect *class*, not a
   single site — sweep the current change scope (`file_scope`) for every sibling sharing that
   root cause and fix them in the same change; siblings outside the declared scope are recorded
   in `findings.md`, never silently left.

### Cross-cutting disciplines
- **输出语言风格** — 面向用户的回答与说明（不含代码、命令、文件内容）遵守四条：
  1. **用中文**；专业技术名词可保留英文（commit、build、lint、token 等），不硬翻。
  2. **说大白话，不用黑话**；不生造词、不堆抽象比喻。能用日常说法讲清楚就用日常说法；
     必须用专业术语或协议内部术语（如 machine gate、lens）时，第一次出现要用一句话说明它指什么，
     不直接甩术语让人去猜。
  3. **专业、客观，以事实和结果为准**；不说恭维话、不自夸、不用"很棒/好问题"这类填充。
     结论先行再给依据；不确定就直说不确定，不糊弄。
  4. **第一性原理思考**；遇到问题先拆到最基本的事实和约束，从那里推导，而不是照搬惯例。
     能质疑的前提就质疑，能去掉的步骤就去掉。
- **Comment hygiene** — code comments must not reference drift-prone external ids
  (requirement #, plan line #, doc section #). Reference only immutable anchors (`ADR-N`).
- **Refresh manual indexes before query** — codegraph/nexus/etc. are manually updated;
  refresh before querying or a stale index misleads you into creating duplicates.
- **Conditional domain lenses** — when a change touches a domain declared in `config.yaml`
  `lenses` (e.g. frontend, industrial client), mount that expert checklist during design and review.

### Process-skill integration (optional method layer)
AIP owns the **slots** (artifacts, state, gates); an external process-skill framework, when present,
owns the **methods** (how to fill each slot well). They compose:
- Slots belong to AIP; methods' output lands in the AIP slot, never a parallel location.
- **Resume is AIP-only**: `_runtime/current_task.json` + `handoff.md` is the single resumable-state
  source. Any external "execute plan in a separate session" checkpointing maps onto `task_board.yaml`;
  no second progress/plan file.
- AIP runs standalone if no method layer is present.
- The concrete phase→skill mapping is single-sourced in the installed `aip` skill, not duplicated here
  or in project docs (drift prevention).

### Enforcement (how this is 100% vs advisory)
What is load-bearing is enforced by **deterministic gates that block**, not prose:
- **Scaffold** (`aip start`) creates slots in the one correct place — no location drift.
- **`aip check`** is a blocking gate: living docs present, ≤1 in-progress, findings classified,
  required slot shape, machine-gate evidence (no `fail`, no unfilled `| <...>` placeholders) on done,
  and **no competing AIP artifacts outside `.aip/`** (drift/dup detector).
- **Hooks** (`install_hooks.py`): git pre-commit (+ optional Claude Stop) run `aip check` automatically
  so it can't be forgotten.
Method *quality* (was the brainstorming deep, the TDD real) cannot be machine-forced — gates check the
*residue* a method must leave (sources cited, real command output, reviewer≠author note). Beyond residue
it is best-effort by design: a poorly executed method yields an incomplete slot the gate rejects.

## Schemas Are Reference-Only

`schemas/*.json` document the shape of `current_task.json` / `task_board.yaml` for humans
and tooling. `aip check` does **not** validate against them (no third-party dependency);
they are guidance, not an enforced gate.

## Optional Knowledge Sources

If present, these may be consumed as enhancement inputs:

- `.nexus-map/`
- git history
- CI records

They are optional. The protocol itself must remain usable without them.
