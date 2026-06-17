---
name: aip
description: Use when the user invokes `$aip` or asks to apply AI Implementation Protocol, including `$aip init`, `$aip start`, `$aip resume`, `$aip check`, `$aip knowledge`, `$aip done`, initializing project_docs, starting a feature package, resuming current task state, rebuilding the knowledge index, validating handoff completeness, or closing a feature according to AIP.
---

# AI Implementation Protocol

Use this skill to apply AIP from the installed Codex plugin.

## Command Invocation

When the user invokes this skill with a command-like prompt, treat the text after `$aip` as arguments and execute the matching AIP action.

Supported forms:

```text
$aip init
$aip start 2026-04-26-my-feature --title "My feature"
$aip resume
$aip check
$aip knowledge
$aip done
$aip help
$aip bug 2026-06-17-crash-on-save --title "Crash on save"
```

Aliases:

- `$aip create <feature-id>` means `$aip start <feature-id>`.
- `$aip validate` means `$aip check`.
- `$aip status` means `$aip resume`.

If no command is provided, run the resume flow when AIP is already initialized. If AIP is not initialized, explain that `$aip init` is the first command.

If arguments are missing, ask for only the missing required argument. For example, `$aip start` requires a feature id.

## Plugin Root

Resolve the plugin root based on where this skill is loaded from.

If this file is loaded from the plugin package, the plugin root is two directories above this file:

```text
<plugin-root>/skills/aip/SKILL.md
```

If this file is loaded from a home-local skill install such as:

```text
~/.agents/skills/aip/SKILL.md
~/.claude/skills/aip/SKILL.md
```

then use the installed plugin package at:

```text
~/plugins/ai-implementation-protocol/
```

The plugin root contains:

- `docs/`: protocol and architecture references
- `templates/`: feature and runtime templates
- `schemas/`: machine-readable schema references
- `scripts/`: local CLI tools

All AIP outputs live under the hidden `.aip/` directory in the target repo.

## Required Resume Flow

Before editing an AIP-enabled repository:

1. Read `.aip/_runtime/current_task.json`.
2. Read every path listed in `must_read` (includes `.aip/STATUS.md` and the project's truth sources from `.aip/config.yaml`).
3. Inspect the active feature's `task_board.yaml`.
4. Read the active feature's `handoff.md`.
5. Only then plan or edit.

If `.aip/_runtime/current_task.json` does not exist, initialize AIP first.

## CLI Commands

Run commands from the target repository root. Use the plugin copy of the scripts as the tool source.

Initialize AIP:

```bash
python <plugin-root>/scripts/aip.py init --repo-root .
```

Start a feature:

```bash
python <plugin-root>/scripts/aip.py start YYYY-MM-DD-short-feature-id --title "Human readable title" --repo-root .
```

Resume current work:

```bash
python <plugin-root>/scripts/aip.py resume --repo-root .
```

Validate handoff completeness:

```bash
python <plugin-root>/scripts/aip.py check --repo-root .
```

Show command help:

```bash
python <plugin-root>/scripts/aip.py --help
```

## Routing Rules

- `$aip init`: run `python <plugin-root>/scripts/aip.py init --repo-root .`.
- `$aip start <feature-id> [--title "..."]`: run `python <plugin-root>/scripts/aip.py start <feature-id> --title "..." --repo-root .`.
- `$aip resume`: run `python <plugin-root>/scripts/aip.py resume --repo-root .`.
- `$aip check`: run `python <plugin-root>/scripts/aip.py check --repo-root .`.
- `$aip knowledge`: run `python <plugin-root>/scripts/aip.py knowledge --repo-root .`.
- `$aip done`: run `python <plugin-root>/scripts/aip.py done --repo-root .`. For bug work units, `--resolution fixed|wont_fix|by_design` is **required**.
- `$aip bug <bug-id> [--title "..."]`: run `python <plugin-root>/scripts/aip.py bug <bug-id> --title "..." --repo-root .`，随后**挂起 `root-cause` skill** 驱动调查，产物落该 bug 包 `report.md`。
- `$aip help`: summarize these commands and do not edit files.

Preserve explicit `--repo-root <path>` if the user provides it. Otherwise use the current workspace root.

After running a command, report the command outcome and the next AIP action from the output or `current_task.json`.

## Examples

Initialize the current repository:

```text
$aip init
```

Create a new feature package:

```text
$aip start 2026-04-26-add-billing --title "Add billing"
```

Resume the active feature:

```text
$aip resume
```

Run the handoff completeness gate:

```text
$aip check
```

## Guided Init (after `$aip init` scaffolds files)

`aip init` 只负责脚手架。脚手架后**由你引导用户填 `.aip/config.yaml`**，逐项 Stop-and-ask，不替用户臆断：

1. **truth_sources**：扫描仓库（README/docs/约定文件）提候选，请用户确认权威文档。
2. **gates**：探测技术栈（package.json / pyproject.toml / *.sln / go.mod 等），为 tests/build/lint_or_drift/e2e 建议真实命令，逐条确认后写入 `cmd`。
3. **lenses**：按改动域（前端/客户端等）建议，可选。
4. **iron_rules**：问项目硬约束（编码要求、契约重生成、未授权不提交等）。
5. **process_skills**：检测到 superpowers 则建议设 `superpowers`，否则留空。

每写一项就更新 `.aip/config.yaml`。完成后跑 `$aip check` 自检。

## Conversational Start (user just describes a need)

用户**口述需求**即可，不要求其先给 id/title：

1. **方法层**：若 `.aip/config.yaml` `process_skills: superpowers`，让位 superpowers **brainstorming** 把需求探清并形成设计；否则走 AIP 原生轻量访谈（目的/范围/验收/约束几问）。
2. **生成**：从对话收敛出 `feature_id = <今天日期>-<标题派生的 kebab slug>`、`title`、以及 `spec.md` 初稿（Goal/Scope/Acceptance Criteria 用对话内容预填）。
3. **脚手架**：调用 `python <plugin-root>/scripts/aip.py start <feature_id> --title "<title>" --repo-root .`，随后把 spec 初稿写入该 feature 的 `spec.md`。

用户全程不手敲 id/`--title`。

## Working Rules

- Keep one active feature pointer in `.aip/_runtime/current_task.json`.
- After meaningful changes, update `task_board.yaml`, append `session_log.md`, and refresh `handoff.md`.
- **Stop-and-ask** on uncertainty/spec gap; never guess and continue.
- **Reuse-first / anti-accretion**: before creating new tools/scaffolds, refresh the index and check `.aip/canonical-assets.md`; creating new needs written justification; replace old via Strangler (migrate + delete same change).
- **Side-finding protocol**: unrelated problems found mid-task → triage and log to `.aip/findings.md` (capture, don't chase); never silently drop or derail.
- **Comment hygiene**: no drift-prone external ids in comments; only `ADR-N`.
- Behavior/architecture change → update `.aip/STATUS.md` (and the truth source) in the same change; decisions → `.aip/decisions.md`.
- Keep adapters optional. A repository without `.nexus-map/`, CI records, or Git metadata must still work.
- Use existing project-specific constraints (`.aip/config.yaml` iron_rules) when stricter than the default protocol.

## 输出语言风格（怎么对用户说话）

适用于一切面向用户的回答与说明；不影响代码、命令、文件内容本身。

1. **用中文**。专业技术名词可保留英文（commit、build、lint、token 等），不硬翻。
2. **说大白话，不用黑话**。不生造词、不堆抽象比喻；能用日常说法讲清楚就用日常说法。必须用专业术语，或用到协议内部术语（如 machine gate 卡点检查、lens 领域检查清单）时，第一次出现先用一句话说明它指什么，不直接甩术语让人猜。
3. **专业、客观，以事实和结果为准**。不说恭维话、不自夸、不用"很棒/好问题"这类填充。结论先行再给依据；不确定就直说不确定，不糊弄。
4. **第一性原理思考**。先把问题拆到最基本的事实和约束，从那里推导，而不是照搬惯例或"大家都这么做"。能质疑的前提就质疑，能去掉的步骤就去掉。

## Process-skill integration (optional method layer — Claude Code + superpowers)

If a process-skill framework (e.g. **superpowers**, when `.aip/config.yaml` `process_skills: superpowers`)
is available, defer the *method* per phase to it. **This table is the single source for the mapping — do
not restate it in project docs; point here.**

| AIP phase | AIP slot (you own) | superpowers skill (method) |
|-----------|--------------------|----------------------------|
| spec | `features/<id>/spec.md` | brainstorming |
| plan | `features/<id>/plan.md` + `task_board.yaml` | writing-plans |
| implement | task_board + `session_log.md` | subagent-driven-development / executing-plans + test-driven-development |
| debug | `.aip/knowledge.md`（根因沉淀）+ 索引 | root-cause（AIP-native，先查后挖+证伪）；superpowers 在场时方法让位 systematic-debugging |
| bug · investigate | `features/<id>/report.md`（各节逐步落）| **root-cause**（bug 轨道 investigate 阶段强绑定，不可跳过）|
| verify | `verification.md` machine-gate table | verification-before-completion |
| review | `verification.md` Independent Review section | requesting-code-review / receiving-code-review |
| finish | `handoff.md` closeout | finishing-a-development-branch |

- **Slots belong to AIP, methods belong to superpowers**: a method's output lands in the AIP slot above, never a parallel location (no second plan under `docs/plans/...`).
- **Resume is AIP-only**: `.aip/_runtime/current_task.json` + `handoff.md` is the single resumable-state source; `executing-plans` checkpoints map onto `task_board.yaml`.
- Absent (e.g. Codex), AIP runs standalone — you just lose the method layer.

## Bug Track (analysis + fix, coherent)

`$aip bug <id>` 建轻量 bug 包（report/file_scope/verification/handoff/session_log/decisions，
无 spec/plan/task_board），`current_task.kind=bug, current_phase=investigate`。连贯流程：

1. 建包后**挂起 `root-cause` skill**：先查 knowledge_index → 复现取证 → 竞争假设 → 逐层证伪 →
   症状 vs 根因 → 触类旁通同类排查；产物逐节落 `report.md`。
2. 根因确认 → root-cause 的 Stop-and-ask：摆【根因+证据+同类波及面+修复选项】交用户拍板，写"选定方案"。
3. `current_phase=fix`：修主站点 + file_scope 内同类兄弟站点（同一变更）。
4. `current_phase=verify`：先写 `## Regression`（修前 fail/修后 pass），跑机器闸门，记 fresh-eyes review；
   真因沉淀进 `knowledge.md`（填 report `## 沉淀`：K-NNN 或 N/A+理由）→ `aip knowledge`。
5. `$aip check` → `$aip done --resolution fixed|wont_fix|by_design`。

## Enforcement (make the gate automatic)

`aip check` is a blocking gate (living docs present, ≤1 in_progress, findings classified, slot shape,
machine-gate evidence on done, and no competing AIP artifacts outside `.aip/`). To make it run without
relying on memory: `python <plugin-root>/scripts/install_hooks.py --repo-root .` installs a git pre-commit
gate (bypass once with `git commit --no-verify`).

## Completion Gate

Do not call an AIP feature complete until:

- `current_task.json` has the intended final status.
- `verification.md` has a **machine-gate table bound to real evidence** (every `config.yaml` gate run, result pass + evidence; nothing skipped silently) and a recorded **fresh-eyes review** (reviewer ≠ author).
- Every `.aip/findings.md` entry added this round is **classified** (no `待分类`).
- The active feature directory contains all required files; `handoff.md` has all required sections; `task_board.yaml` has ≤1 `in_progress` task.
- `python <plugin-root>/scripts/aip.py check --repo-root .` passes.
- Commits require explicit user authorization.
