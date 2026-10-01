# AI Implementation Protocol

## Goal

AI Implementation Protocol (AIP) defines the minimal records that let any AI resume a task without requirement drift, hidden assumptions, or quality loss.

## Output Location

All AIP outputs in a target repository live under a single hidden directory `.aip/` (like `.git`). Nothing is scattered into the project root.

## Project-Level Living Docs

AIP keeps project state under `.aip/` in two shapes. There are **no per-feature work-package directories and no runtime pointer** — task state lives in track files.

**Items — one file each.** Knowledge, decisions, side issues and work lines each have a directory; every entry is one Markdown file named `<timestamp>_<type>_<status>_<short title>.md`, e.g. `20260928-153012_knowledge_active_gbrain健康分是扣分制.md`:

- `knowledge/` — verified root causes and pitfalls (`active` / `draft` / `fixed` / `superseded`).
- `decisions/` — architecture/direction-level decisions (`accepted` / `superseded`).
- `inbox/` — side issues hit while doing something unrelated (`open` / `closed`).
- `tracks/` — work lines (`active` / `blocked` / `paused`). A finished line's file is deleted (`aip_item.py status <track> done`), in the same MR as the line's last change — see the completion check.

The timestamp is the creation time to the second. The short title is written by whoever creates the item (the AI): an 8–24 character name that says what the item is, not the first half of the title sentence. `aip_item.py new` requires `--slug` when the title is longer than 24 characters and suggests a fallback cut at a clause boundary; the automatic cut (whole leading clauses, hard cut only when no clause fits) is used only by migration when no name was given. The short title never changes afterwards, because it is part of the id. An item's **id is `<timestamp>_<short title>`**: references between items and code-comment anchors always use the full id (`.aip/knowledge/20260928-153012_gbrain健康分是扣分制`) — never the timestamp alone (unreadable) and never the status (it changes). The status sits both in the file name (for filtering and sorting) and in the file's front matter (`status:`), and `aip check` requires the two to match; status changes go through `aip_item.py status`, which renames the file and rewrites the header together. Why files instead of numbered entries in one big file: numbering by "highest + 1" collided whenever two branches or clones added entries in parallel (observed in a real project: two different K-186s, two I-14s, two I-25s), and every parallel append conflicted at the end of the same file. Separate files never collide on creation and merge without conflicts. A database was considered and rejected: a binary file can't be merged by git or GitLab's web merge, can't be reviewed in a diff, and can't be read or grepped directly.

Front matter is plain `key: value` lines between `---` markers: `title` and `status` always; knowledge also needs `category`, `scope` and `last_reviewed` (a `YYYY-MM-DD` date) and a body with non-empty `症状` and `根因`; `superseded` knowledge/decisions need `superseded_by` (the replacing item's id, or a sentence when a mechanism rather than an entry replaced it). Optional: `related` (comma-separated ids), `aliases` (old ids from before migration, e.g. `K-185`), `rule_id`.

`aip_item.py` is the one tool for items: `new` (knowledge items must give `--category` and `--scope`), `status` (`done` on a track deletes it), `reviewed`, `list` (`--grep` matches title, short title, category and scope), `show` (by full id, file name, or old alias).

**Whole documents:**

- `reference.md` — domain concepts/terms, core invariants, and reusable implementations (the canonical pick).
- `conventions.md` — project conventions (standing how-we-work rules).
- `config.yaml` — verification commands (`gates`), the date of the last full review, `aip_version` (which AIP template version this repo's `.aip/` was last tidied to), and an optional update remote. Nothing else: fields nobody reads are worse than none.

**The board is not a file.** The SessionStart hook prints it straight from the directories: live tracks in full, then the file names of open side issues (newest first, capped at 10). Knowledge and decisions are not on it — find them by file name or `aip_item.py list --grep`. Without a hook (e.g. Codex) the AI reads `tracks/` and lists `inbox/` files with `_open_` itself. Up to 0.6.x the board was generated into `OVERVIEW.md`; it went stale whenever nothing regenerated it, so it was dropped in 0.7.0.

`aip init` creates the three documents and the four item directories (with a `.gitkeep`); `aip check` validates them. Project iron rules live at the top of `conventions.md`, which the guide block tells the AI to read before starting work.

### Retired slots (must not reappear)

Earlier AIP versions used per-feature packages, a runtime pointer, and a separate bug track. Those are gone. `aip check` treats these filenames as **forbidden anywhere in the repo** (a migration guard): `current_task.json`, `task_board.yaml`, `handoff.md`, `verification.md`, `session_log.md`, `report.md`, `file_scope.yaml`, `STATUS.md`, `findings.md`, `canonical-assets.md`. Their roles moved: current state → `tracks/`; side-findings → `inbox/`; reusable-asset registry → `reference.md`.

The pre-0.5.0 layout — `knowledge.md`, `decisions.md`, `inbox.md`, `knowledge_index.md` as single files and a hand-written board — is migrated by `aip_migrate.py` (preview by default, `--apply` to write, `--rewrite-anchors` to also rewrite `.aip/knowledge.md::<rule_id or old id>` code-comment anchors; `--names-out <file>` exports the items whose titles are too long so the AI can name them, and `--names <file>` reads the names back). A migrated item's timestamp is the author time of the commit where its heading first appeared (following file renames), not `git blame`, which reports the last edit of the heading line (e.g. the day a side issue was struck through); when that can't be found it falls back to `git blame`, then to now. Entries committed together share one second and are told apart by their short titles. Old ids become `aliases` on each item. Everywhere under `.aip/` — item bodies, header fields other than `title`, `reference.md`, `conventions.md`, `config.yaml`, `specs/` and other remaining files — old ids and `.aip/knowledge.md::…` anchors are replaced by full ids without needing the flag (the flag only covers code outside `.aip/`); titles keep their old ids, and an old id shared by two entries is left as is and reported. While those files exist, `aip check` reports only "still the old layout", `aip init` refuses to run, and the SessionStart hook asks for the migration. The steps live in the skill's `reference/migrate.md`.

## Resume / Onboarding

Any AI starting or resuming work:

1. Read the live tracks (printed by the SessionStart hook, or the files under `tracks/`), read the line's **next step** and its "read first" list.
2. Read those files; look up related knowledge and decisions by file name or `aip_item.py list` and open only the relevant ones — never read a whole item directory.
3. Only then start — don't replay history.

The SessionStart hook also reports the checkout state before any `.aip/` write: a checkout behind its upstream (from local refs only, no fetch) and uncommitted changes under `.aip/`. In a real project, entries written in a checkout 50 commits behind and never committed were lost and their numbers reused.

## Capture + Completion Check

### Coding delivery verification

For any coding work, including business feature development and bug fixes, verification is part of the work rather than an optional follow-up.

Before editing code, the AI must understand the repository's verification mechanism and inspect the applicable plan or requirements, existing tests, build/lint commands, CI configuration, and other constraints. It must identify the verification path before implementation starts and create an acceptance matrix mapping each requirement to an implementation location and behavioral evidence. The matrix may live in the active track file.

Before declaring the work complete, the AI must compare the implementation against those constraints and run the applicable verification chain. The normal chain is: constraint comparison → implementation check → tests/build/lint/static or end-to-end checks → result comparison. If the full chain cannot run, the AI must at least run the relevant lint or build checks and state every skipped check, the reason, and the remaining risk. It must not describe unverified behavior as completed.

Build and lint results alone never prove that a plan requirement was implemented. Each matrix row needs behavioral evidence or an explicit reason why behavioral evidence is not applicable. Existing tests must not be deleted, skipped, weakened, or changed only to make checks pass; any test change must be justified against the requirement and reviewed as part of the implementation.

Every completion report for coding work must include the changed result, constraint comparison, commands run and their results, skipped checks and reasons, and remaining risks. If the full loop did not complete, the report must say “partially verified / verification loop incomplete”.

### Two capture paths

- **Main path** — a pitfall/root cause verified during the task → search `knowledge/` for a match first (extend it or link it via `related` if similar) → `aip_item.py new --type knowledge` (`draft` while evidence is incomplete; `active` once the review checklist passes — the AI promotes autonomously but must notify).
- **Side path** — a problem unrelated to the current task → search `knowledge/` and `inbox/` first → if new, `aip_item.py new --type inbox` (don't blindly add).

### Write discipline (all sedimentation)

Run the review checklist (next section) → write → notify the user in-session (which docs changed, a one-line reason each) → the edit lands in the same git commit as the work. There is no pre-approval gate: the human audits after the fact via the notification plus git diff, which is why skipping the notification is forbidden.

- Knowledge `draft` marks an entry the AI itself is not yet sure of (evidence incomplete); `active` means the review checklist passed; `fixed` means the defect was fixed but the lesson still helps; `superseded` means replaced (`superseded_by` says by what). The AI may write `active` directly but must state the evidence in the notification.
- Only **verified** items enter knowledge; guesses and side-issues go to `inbox/`.
- **Overturning a decision/convention** — past decisions are not iron law: an AI that finds one no longer fits current needs is expected to say so and correct it. The only mechanism is a new decision whose body says "supersedes <old id>" with the reason, and `aip_item.py status <old> superseded --by <new>`; the old entry is never rewritten or deleted in place.
- **Deleting/merging existing content** — the only two valid reasons are "proven wrong" and "duplicate of another entry"; "unused this round" is not one. The notification must name what was removed and why.

### Review checklist (`aip review`, soft quality)

The goal is always **doc quality**, never content volume: clear, accurate, necessary, minimal — when in doubt, write less. **The default action is delete or merge, not add**: every addition must first clear the necessity bar below, or it doesn't get written. Run it entry-by-entry before writing any living doc, and over the whole `.aip/` on `/aip review` (`$aip review` in Codex):

1. Look for near-duplicates first: items by file name and `aip_item.py list`, opening the close ones in full; whole documents in full. Merge or cross-link (`related`) instead of adding.
2. Only write facts verified first-hand (ran the command, read the code, reproduced it); mark uncertain items `draft` or file them in `inbox/`. Promote an entry to `active` only after every checklist item passes, and only with the evidence stated in the notification.
3. Necessity: without this entry, would a new AI six months from now clearly pay a higher comprehension cost? If no, delete it; if yes but it reads unclearly, rewrite; if still unclear, drop it.
4. Minimal: one entry states one thing; don't restate what git history or the code itself derives.
5. Right slot: pitfalls/root causes → knowledge; concepts/reusables → reference; standing rules → conventions; side-issues → inbox; direction → decisions. A misplaced entry is worse than none.
6. Afterwards run `aip check`.

A full-`.aip/` review triggers when any of: the change deletes or merges content; ≥3 entries changed at once; more than a month since the last review (`review_last_full` in `.aip/config.yaml`); the user runs `/aip review` (unconditional). Findings are reported as *problem + suggested edit + reason + impact* before applying. A full review also re-verifies the knowledge entries the reminders list, checks that reference paths still exist, and checks project skills and instruction files against the code; it ends by setting `review_last_full` to today. `aip review` owns doc quality only; it does not analyse problems.

### Keeping living docs current

Docs rot unless something makes them get re-checked. Two mechanisms:

- **Check on use.** Whenever the AI reads a `.aip/` entry, a convention, a project skill or an instruction file (`CLAUDE.md` / `AGENTS.md`) and finds it no longer matches the code, it fixes it in the same commit: a still-valid knowledge entry gets `aip_item.py reviewed`; one whose defect is fixed becomes `fixed`; one replaced by a newer mechanism becomes `superseded`; conventions, skills and instruction files get their text corrected; anything needing a human decision goes to the inbox. The completion check's capture sweep asks about this explicitly.
- **Due reminders.** `aip_upkeep.py` decides what is due from what actually changed, not only from the calendar. For each active knowledge entry it reads the file paths and code names the entry cites in backticks: if a cited file or name existed in the repo on the review date and is gone now, the entry is due; otherwise if any cited code file (docs and `.aip/` don't count) has a commit after `last_reviewed`, it is due (names that were never in the repo — external APIs, env vars, server paths — are ignored, so they never cause noise). Entries that cite no code fall back to 90 days; entries whose code never moved get a one-year ceiling. The same "was there, now gone" check runs over `reference.md` against the last full review date. It also lists `draft` entries, a full review overdue by 30 days, live tracks longer than 12 lines, and AIP script paths written in `CLAUDE.md` / `AGENTS.md` (outside the managed block) that no longer exist on disk. Without git it falls back to the 90-day rule.

  Each item lands in exactly one bucket, and the list is sorted by urgency: repo not yet tidied after an AIP upgrade → dead guide paths → cited code gone → cited code changed / reference gone → full review → drafts / long tracks → 90-day → one-year. A real project produced 171 reminders at once, which nobody reads; so the SessionStart hook and `aip check` show a one-line summary plus the top 5, and `aip_upkeep.py --all` prints everything. The hook prints them on startup and resume (not right after a compaction, mid-task). They never block a commit, and the pre-commit hook skips computing them (`aip check --no-reminders`). The AI handles them when it touches those entries or when the current line wraps up, or tells the user it is deferring them.

### Completion check (when a work line is done)

**Tier 1 (every time a line wraps up):**

1. For coding work, perform the coding delivery verification above and include its evidence in the completion report.
2. Run `aip check` (red blocks the commit; fix item by item).
3. Scoped correction: tidy only the entries you touched this round and their direct links (checklist-reviewed and notified; no silent edits outside the line's scope).
4. Capture sweep: list what you concretely learned/hit this round — into knowledge / inbox / reference / conventions / config?
5. Close the line in its last MR: `aip_item.py status <track> done` deletes the track file, committed with that MR rather than after it merges. If the MR merges, the line is gone from the main branch; if it doesn't, the line stays live there — no follow-up MR, no rollback. Leftover work outside this repo goes to `inbox/` or a line in that repo. (Detecting "merged" from git was rejected: squash merges and unfetched refs make `git branch --merged` unreliable.)

**Tier 2 (on an architecture/trade-off decision):** `aip_item.py new --type decision` (context, decision, rationale, impact) so it isn't re-litigated later.

### Updating an installed engine (`/aip update`)

Installers write `SOURCE.json` into the installed `aip` skill: remote URL, branch, installed commit, scope (user / project) and target. At session start (not after a compaction) the hook runs a quiet check — `git ls-remote` against the remote branch, 5-second timeout, no credential prompts — and prints a notice only when the remote has a newer commit; a missing record, no network, or an unknown remote stay silent. If the machine happens to hold the source repo and the remote commit is an ancestor of the installed one, the install is ahead (unpushed work) and nothing is shown. A project can pin the remote with `aip_remote` / `aip_remote_branch` in `config.yaml`.

`aip_update.py --apply` updates in place without the source repo or the installers: shallow-clone the remote branch into a temp dir, verify the package is complete, then swap each installed skill directory (for a project install, both `.claude/skills` and `.codex/skills`) by staging the new copy beside it and renaming; any failure renames the old copies back. The skills removed in 0.6.0 (`root-cause`, `aip-brainstorm`) are deleted from the same skill directories afterwards; the installers and the uninstaller do the same. `SOURCE.json` is rewritten with the new commit. Project installs then commit the changed skill directories.

**Tidying existing repos after an upgrade.** A new version may change templates or rules in ways existing `.aip/` directories don't follow on their own (fields dropped, content moved, old files deleted). The skill's `reference/upgrade.md` has one section per such version, headed by the version number, saying exactly what to change. Each repo records in `config.yaml`'s `aip_version` the version it was last tidied to (missing = before 0.7.0). When `upgrade.md` has a section newer than that, the session-start reminders (top priority) tell the AI to tidy up: tell the user, follow the sections oldest to newest, set `aip_version`, run `aip check`, one commit. The reminder lives at session start rather than in `/aip update` because the update is executed by the old version's script, and a user-level install upgrades every repo on the machine at once — each repo is tidied in its own session. Versions that need no repo changes add no section.

## `aip check` (the one machine check)

`aip check` (`python3 <skill>/scripts/aip_check.py --repo-root .`, where `<skill>` is the installed `aip` skill directory) validates:

1. **Not the old layout** — if `knowledge.md` / `decisions.md` / `inbox.md` / `knowledge_index.md` still exist, that is the only finding reported (run the migration).
2. **Documents and item directories present** — `reference.md`, `conventions.md`, `config.yaml`, and the four item directories.
3. **Item file names** — `<timestamp>_<type>_<status>_<short title>.md`, type matching its directory, status valid for the type.
4. **Items well-formed** — the header status matches the file name; required header fields and body sections present; `last_reviewed` is a date; `superseded` items say by what; `related` and id-shaped `superseded_by` point to existing items; **no duplicate ids** (e.g. both sides of a merge changed the same item's status).
5. **No legacy residue** — none of the forbidden filenames appear under `.aip/`.
6. **Engine version consistency** (engine repo only) — the plugin manifests' `version` match `skills/aip/VERSION`, the single version source; and the repo's own project-level copies (`.claude/skills/aip`, `.codex/skills/aip`) match the engine source file by file (install record and caches aside) — after changing the engine, reinstall with `scripts/install_all.py --project .`.

Commands printed for a human or the AI to run (installers, doctor, reminders, check messages) use the interpreter that is actually running, not a fixed `python3`; the SessionStart hook probes `python3` then `python` (3.9+ only) and prints the one it found at the end of the board, and the AI uses it for the whole session.

Exit 0 = pass; non-zero = violations listed on stdout.

## `aip doctor` (diagnosis, non-blocking)

`aip doctor` (`python3 <skill>/scripts/aip_doctor.py --repo-root .`) checks install/environment health — advisory, while `aip check` stays the one blocking gate. Four areas: project `.aip/` health (the checks above, plus the due reminders summarised as one WARN line), install health (skill directories complete, installed VERSION vs engine VERSION, leftovers of the skills removed in 0.6.0), hook health (pre-commit present, AIP-managed, engine path still valid), and engine-repo version consistency. Output is graded ERROR (AIP unusable) / WARN (drift risk or degraded experience) / INFO (optional), each with a fix command; exit 1 only on ERROR. The installers print the doctor command after a successful install.

## Commands (AI-autonomous; the human only runs init)

Day-to-day actions (capture, check, review, read the live tracks to resume) are triggered by the AI at the right moment — the human doesn't type them. The human runs one command once per new repo:

```
python3 <skill>/scripts/aip_init.py --repo-root .
```

In Claude Code the human types `/aip init`; in Codex `$aip init`. The skill runs the script.

`aip init` has two phases. **Phase A** is the deterministic script above: scaffold the living docs, upgrade the marked AIP guide blocks, install hooks (git pre-commit plus a Claude Code SessionStart hook that prints the board on startup, resume and after context compaction; for a project install its command tries `python3`, then `python`, and only runs one that is 3.9+), delete a board file generated by an older version, and record the current version as `aip_version` in a new `config.yaml` — idempotent, existing living docs and user content are never overwritten. **Phase B** is AI-driven and runs immediately after: the AI analyzes the project itself (README, build/dependency manifests, test dirs, CI config, directory layout — it never interrogates the user; zero-config means "don't ask", not "don't know"), then fills **only files still in template or empty state** — build/test commands into `config.yaml` gates, core concepts and directory roles into `reference.md`, iron rules and established practices into `conventions.md`. For legacy/test-less projects it files "no tests — start with characterization tests" as a side issue instead of inventing tests. Phase B must end with an init summary: what was detected / what was written per file / what's uncertain / what the user should confirm.

**Three reliability layers:** hooks (`install_hooks.py` adds a git pre-commit that runs `aip check`), the completion check, and onboarding (read the live tracks on every resume). The concrete command lines are single-sourced in the installed `aip` skill, not duplicated here (drift prevention).

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
  (requirement #, plan line #, doc section #). Reference only immutable anchors: an item's full
  id (`.aip/knowledge/<timestamp>_<short title>`); pre-migration ids like `ADR-3` / `K-185` still resolve via `aliases`.
- **Refresh manual indexes before query** — codegraph/nexus/etc. are manually updated;
  refresh before querying or a stale index misleads you into creating duplicates.

### Boundary with the AI's own memory

Tools like Claude Code keep a personal, per-machine memory that only that AI sees. AIP docs are project-level: committed, shared by every person and every tool. Facts, decisions, pitfalls and conventions **about the project** go to `.aip/` only; the user's own preferences and habits stay in the tool's memory. On conflict `.aip/` wins — fix it there rather than keeping two versions.

### Multi-agent and parallel branches

Only the **main agent** writes `.aip/`; subagents report findings and never write living docs. Feed relevant knowledge/reference entries to subagents when delegating. Each parallel line has its own track file and every new entry is a new file, so branches merge without conflicts; if both sides changed the same item's status, git reports a rename conflict — keep one, and `aip check` flags duplicate ids. Run `aip check` after merging.

### Process-skill integration (optional method layer)

AIP owns the **slots** (living docs, state, checks); an external process-skill framework, when present, owns the **methods** (how to fill each slot well). They compose:

- Slots belong to AIP; a method's output lands in the AIP slot, never a parallel location.
- **Resume is AIP-only**: the active track file (next step + read-first list) is the single resumable-state source. Any external "execute the plan in a separate session" checkpointing maps onto the track file, not a second progress/plan file.
- AIP runs standalone if no method layer is present.

### Enforcement (load-bearing vs advisory)

What is load-bearing is enforced by **deterministic checks that block**, not prose:

- **Scaffold** (`aip init`) creates the living docs in the one correct place — no location drift.
- **`aip check`** is a blocking check: documents and item directories present, item names and headers well-formed, no duplicate ids, no finished track files left, no forbidden legacy files, engine versions consistent. A hook runs it automatically.
- **Hooks** (`install_hooks.py`): git pre-commit (`aip check --no-reminders`, + optional Claude Stop) run `aip check` so it can't be forgotten.

Method *quality* (was the investigation deep, the review real) can't be machine-forced — the checks verify the *residue* a method must leave (verified causes, sources cited, in-session notification of every doc edit, the git trail). Beyond residue it is best-effort by design: a poorly executed method leaves an incomplete slot the check rejects.

## Optional Knowledge Sources

If present, these may be consumed as enhancement inputs:

- `.nexus-map/`
- git history
- CI records

They are optional. The protocol itself stays usable without them.
