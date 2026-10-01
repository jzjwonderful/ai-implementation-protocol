# AI Implementation Protocol

AI Implementation Protocol (AIP) is a portable workflow for AI-assisted software delivery.

Its purpose is simple:

- preserve requirement context across sessions
- let any AI resume work without guesswork
- reduce implementation quality drop caused by interruption
- enforce handoff quality with local scripts instead of good intentions

This repository contains:

- the protocol itself
- a plugin package that ships the `aip` skill for Claude Code, Codex and Grok — scripts and templates travel inside it
- local validation scripts
- optional adapters such as Nexus integration

## Install (recommended: into each project)

Install the skills into the repository itself, so they travel with it. Commands below say `python3`; check first with `python3 --version`, and if that's missing (typical on Windows) use `python` after `python --version`. It must be Python 3.9+ — don't run AIP with Python 2.

```bash
git clone https://github.com/jzjwonderful/ai-implementation-protocol.git
cd ai-implementation-protocol
python3 scripts/install_all.py --project /path/to/repo     # Claude Code + Codex
python3 scripts/install_claude_plugin.py --project /path/to/repo   # → <repo>/.claude/skills/
python3 scripts/install_codex_plugin.py --project /path/to/repo    # → <repo>/.codex/skills/
```

Then run `/aip init` (or `$aip init`) once in that repository and commit the skill directories, `.claude/settings.json` and `.aip/`.

Why project-level first:

- Everyone who clones the repository gets the same engine version, with no personal install, and the hooks use paths relative to the project.
- Each repository upgrades on its own schedule (`/aip update`, then commit). A machine-wide upgrade changes every repository at once, while some are mid-migration or on old layouts; their hooks point at the shared copy and break when it moves or is removed.

The installer prints the follow-up steps: repoint that repository's hooks at the in-repo copy, then run `/aip init`. Grok has no established project-level skill directory, so `--project` covers Claude Code and Codex only. The AIP repository installs itself the same way (a real copy, so it also works on Windows, where git symlinks need extra setup). `aip check` compares those copies with `plugins/ai-implementation-protocol/skills/aip` and fails if they differ: after changing the engine, re-run `scripts/install_all.py --project .`.

## Install For The Whole Machine (user home)

If you'd rather have one copy for every repository on this machine, one command installs the shared engine plus skills for **Claude Code, Codex, and Grok**. Upgrading it upgrades every repository at once, and each one then has to be tidied (see the note below).

```bash
git clone https://github.com/jzjwonderful/ai-implementation-protocol.git
cd ai-implementation-protocol
python3 scripts/install_all.py
```

Update an existing install (re-running always overwrites):

```bash
git pull
python3 scripts/install_all.py
```

Only some runtimes:

```bash
python3 scripts/install_all.py --targets claude,grok
# legal names: claude, codex, grok, or all
```

Optional Grok user-plugin registration (`~/.grok/plugins/`):

```bash
python3 scripts/install_all.py --user-plugin
```

Engine package always lands at:

```text
~/plugins/ai-implementation-protocol/
```

Skills land at:

```text
~/.claude/skills/aip/   # Claude Code
~/.agents/skills/aip/   # Codex
~/.grok/skills/aip/     # Grok
```

Codex also updates `~/.agents/plugins/marketplace.json`. `aip` routes `$aip` commands. Installing over an older version removes the `root-cause` and `aip-brainstorm` skills that AIP shipped before 0.6.0.

> **Upgrading from an older AIP?** After updating, re-run `$aip init` (or `python3 ~/.claude/skills/aip/scripts/aip_init.py --repo-root <target>`) once in each AIP-enabled repository. It scaffolds missing living docs and upgrades the marked AIP guide blocks in `AGENTS.md`/`CLAUDE.md`; it preserves existing living docs and project-owned content. Until you do, the repository may still use the older onboarding rules. When a version also needs an existing `.aip/` changed (0.7.0 does), the next session in that repository reminds the AI, which follows the skill's `reference/upgrade.md` after asking you — the steps include re-running init.

Open a new session in each tool after installation. `$aip init` is the only command a human types — everything else is AI-triggered:

```text
$aip init
```

Per-runtime installers below are still available if you only want one tool.

## Install For Claude Code Only

```bash
python3 scripts/install_claude_plugin.py
# update: re-run the same command (existing files are replaced)
```

Skill → `~/.claude/skills/aip/`, the whole directory, nothing under `~/plugins/`.

## Install For Codex Only

```bash
python3 scripts/install_codex_plugin.py
# update: re-run the same command (existing files are replaced)
```

Skills → `~/.agents/skills/`, and to `$CODEX_HOME/skills` (or `~/.codex/skills` when `CODEX_HOME` is unset); also updates `~/.agents/plugins/marketplace.json`. Existing AIP install files are replaced by default.

## Install For Grok Only

```bash
python3 scripts/install_grok_plugin.py
# update: re-run the same command (existing files are replaced)
# optional user plugin: python3 scripts/install_grok_plugin.py --user-plugin
```

Skills → `~/.grok/skills/`. Optional `--user-plugin` also copies to `~/.grok/plugins/`.

> **Upgrading from an older AIP?** After updating, run `/aip init` (Claude Code) or `$aip init` (Codex / Grok)
> once in each AIP-enabled repository. It scaffolds any missing living docs and refreshes the hooks — including
> repointing hooks that older versions aimed at `~/plugins/.../scripts/`, which 0.3.0 moved into the `aip` skill.
> `aip init` is idempotent and preserves your existing files.
>
> **Coming from before 0.5.0?** Knowledge, decisions and side issues moved from single files to one file per item.
> `aip init` refuses to run on the old layout; follow `/aip migrate` (`aip_migrate.py`, preview first, then `--apply`).

## Core Ideas

AIP keeps project state in **living docs** (cross-task, long-lived) plus local validation scripts. There are no per-feature work packages and no runtime pointer — task state lives in track files, which the SessionStart hook prints as the board (nothing is stored).

All AIP outputs inside a target project live under a single hidden `.aip/` directory (like `.git`):

```text
.aip/
├── knowledge/                # verified root causes / gotchas, one file each
├── decisions/                # architecture decisions, one file each
├── inbox/                    # side issues (capture, don't chase), one file each
├── tracks/                   # work lines, one file each; deleted when done
├── reference.md              # domain concepts, core invariants, reusable implementations
├── conventions.md            # iron rules and standing how-we-work rules
└── config.yaml               # verification commands, last full review, aip_version
```

Item files are named `<timestamp>_<type>_<status>_<short title>.md`, e.g.
`knowledge/20260928-153012_knowledge_active_gbrain健康分是扣分制.md`. An item's id is `<timestamp>_<short title>`;
references use the full id. Nothing is numbered, so parallel branches never collide and merge without conflicts.
`aip_item.py` creates items, changes status (renaming the file and its header together), lists and shows them.

The AIP docs are project-level and committed. The AI's own cross-session memory (e.g. Claude Code's) is personal and stays on one machine; project facts go to `.aip/` only, user preferences stay in the tool's memory. Only the main agent writes `.aip/`; subagents report back. See `docs/protocol.md`.

## Repository Layout

- `docs/`: protocol and product docs
- `plugins/ai-implementation-protocol/`: the installable package (Claude Code + Codex + Grok)
  - `skills/aip/`: the engine skill — `SKILL.md`, `reference/` (details loaded on demand), `scripts/` (CLI), `templates/`, `VERSION`
- `scripts/`: installers and uninstaller only
- `tests/`: unit tests for the scripts
- `.agents/plugins/marketplace.json`: repo-local Codex marketplace entry
- `adapters/`: optional integrations
- `examples/`: sample project layouts

There is exactly one copy of the engine (scripts + templates) in this repository: inside the `aip` skill. Edit it there — not in `~/.claude/skills/` or `~/plugins/` — and re-run the installer.

## First Commands

Initialize a target repository (the only command a human runs; in Claude Code just type `/aip init`). Paths below are for a project-level install, run from the repository root:

```bash
python3 .claude/skills/aip/scripts/aip_init.py --repo-root .
```

The remaining scripts are triggered by the AI at the right moment, per the installed `aip` skill:

```bash
python3 .claude/skills/aip/scripts/aip_check.py --repo-root .      # hygiene gate (also runs in the pre-commit hook)
python3 .claude/skills/aip/scripts/aip_item.py --repo-root . list  # items: new / status / reviewed / list / show
python3 .claude/skills/aip/scripts/aip_upkeep.py --repo-root . --all  # everything due for review
python3 .claude/skills/aip/scripts/aip_migrate.py --repo-root .    # pre-0.5.0 layout: preview, then --apply
python3 .claude/skills/aip/scripts/aip_doctor.py --repo-root .     # install/environment health check (project-level counts; no global install needed)
```

For Codex use `.codex/skills/aip`. With a whole-machine install use `~/.claude/skills/aip` (Codex: `~/.agents/skills/aip` or `$CODEX_HOME/skills/aip`) and `--repo-root <target-project>`.

## Codex Plugin Internals

This repository can also be used as a repo-local Codex plugin during development.

Plugin entry:

```text
plugins/ai-implementation-protocol/.codex-plugin/plugin.json
```

Repo-local marketplace:

```text
.agents/plugins/marketplace.json
```

See `docs/github-distribution.md` for publisher and user installation details.

## Nexus Dependency

AIP does not require Nexus.

If a target project contains `.nexus-map/`, AIP can treat it as an optional knowledge source.
If `.nexus-map/` does not exist, AIP still works.

## Current State

The engine runs on the flat living-doc model (ADR-2 in `.aip/decisions/`): living docs under `.aip/`, track files for work lines, and `aip check` as the one blocking machine gate. Since 0.3.0 (ADR-4) the engine lives inside the `aip` skill directory and is installed as one unit.

Living docs are kept current in two ways (0.3.1, ADR-5). First, "check on use": whenever the AI reads a knowledge entry, convention, project skill or instruction file that no longer matches the code, it fixes it in the same commit. Second, reminders: at session start and in `aip check`, `aip_upkeep.py` lists knowledge whose cited code changed after its last review, cited files or code names that existed then and are gone now, entries without code references older than 90 days, draft entries, and an overdue full review (`review_last_full` in `config.yaml`, 30 days). Reminders never block a commit.

Installed skills update themselves (0.4.0, ADR-6): the session-start hook quietly checks the recorded remote and says so when a newer commit exists; `/aip update` (`aip_update.py --apply`) shallow-clones the remote and swaps the installed skill directories in place, rolling back on failure.

Since 0.5.0 knowledge, decisions, side issues and work lines are one file per item (see decision `20261001-004400_条目改成一条一个文件` in `.aip/decisions/`). Numbered entries in one big file kept colliding when branches or clones added entries in parallel; files named by timestamp and short title don't. The board is generated and no longer committed, reminders are sorted and capped at five with a summary line, the session-start hook also reports a checkout behind its upstream or uncommitted `.aip/` changes, and `aip_migrate.py` converts the old layout.

Since 0.6.0 the package ships only the `aip` skill (decision `20261001-070424_删除随包的头脑风暴和根因技能`): the `root-cause` and `aip-brainstorm` skills and `aip_brainstorm.py` were removed as rarely used. The step for recording a verified root cause as a knowledge item moved into the `aip` skill; installers, `/aip update` and the uninstaller delete old copies of the two removed skills.

Since 0.7.0 (decisions `20261001-081613_看板按目录打印且线做完即删` and `20261001-081613_配置只留有用字段且按版本整理`) the board is no longer a file: the SessionStart hook prints live tracks and open side issues straight from the directories, since a stored board went stale whenever nothing regenerated it. A finished track is deleted, in the same MR as its last change, so no follow-up MR is needed after merging. `config.yaml` keeps only the fields something reads; iron rules moved to `conventions.md`. Each repo records `aip_version`, and the skill's `reference/upgrade.md` tells the AI how to tidy an existing `.aip/` after an upgrade — the session-start reminders point to it. The project-level SessionStart hook tries `python3`, then `python`, and refuses anything older than 3.9.
