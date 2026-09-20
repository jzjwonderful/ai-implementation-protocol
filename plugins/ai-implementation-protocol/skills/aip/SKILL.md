---
name: aip
description: Use when the user runs `/aip` (Claude Code) or `$aip` (Codex), or whenever AI Implementation Protocol applies — project state lives in `.aip/` living docs, the AI keeps them current and resumes from the OVERVIEW board. Human only types `/aip init` once per repo.
argument-hint: "[init | review]"
---

# AIP 引擎（技能为主，AI 自主驱动）

AIP 用七类活文档管项目级状态，零依赖、随处可用。人只在装 AIP 时敲一次 `/aip init`（Codex 里是 `$aip init`），其余动作由 AI 按时机自己触发。每次用到 AIP 要**当场知会用户**（记了什么、参考了哪条、跑了什么检查）——这是人事后抽查的唯一依据，不能省。

## 脚本在哪
脚本和模板随本技能走，都在 **本 SKILL.md 所在目录** 下：`scripts/` 与 `templates/`。下文 `<skill>` 指这个目录（Claude Code 调技能时会给出它的路径；Codex 下就是本文件所在目录）。命令一律写全路径，例如：

```
python <skill>/scripts/aip_check.py --repo-root .
```

改引擎请改 AIP 仓库里的 `plugins/ai-implementation-protocol/skills/aip/`，别改这份已安装的副本；改完重跑安装器。

## 七类活文档（去哪找什么）
- `.aip/OVERVIEW.md` — 多线看板（手写顶部）+ 自动摘要。开始/接手任务前先读。
- `.aip/decisions.md` — 架构/方向级决策（不是任务级需求）。
- `.aip/knowledge.md`(+`_index`) — 验证过的技术坑/根因。
- `.aip/reference.md` — 领域概念/术语、核心铁律、可复用实现（裁决）。
- `.aip/inbox.md` — 旁路问题收件箱。
- `.aip/conventions.md` — 项目规约。
- `.aip/config.yaml` — 工程配置（构建/测试命令等）。零配置起步，用到再填。

## 和 AI 自带记忆的边界
Claude Code 等工具有自己的跨会话记忆（个人级、存在本机、只有这个 AI 看得到）。AIP 文档是**项目级**的：进仓库、随代码走、给所有人和所有工具看。分工：
- 关于**这个项目**的事实、决策、坑、规约 → 只记 AIP 文档，不要在个人记忆里再存一份。
- 关于**用户本人**的偏好和工作习惯 → 归工具自己的记忆，不进 `.aip/`。
- 个人记忆里若有项目事实，以 `.aip/` 为准；发现冲突就修 `.aip/`，别两边各写各的。

## 通用开发纪律（随 AIP 分发，对所有项目生效）
1. **不说黑话**：文档/注释/会话用大白话，不用晦涩比喻和生造词；公认技术名词除外。
2. **注释不引外部编号**：代码注释不引 plan/需求/任务/issue 编号或外部文档名（会漂移、改名即误导）；只说代码本身的意图和约束，能不写就不写。
3. **编码交付要闭环验证**：凡会改代码的工作，动手前读懂项目的验证机制（相关 plan/需求、现有测试、构建/lint 命令、CI 配置）；动手后逐项对照并执行验证。验证结果与目标一致才能说"完成"。

## AI 自主行为（按时机触发）
- **接手/新会话**：读 OVERVIEW 的 `▶[active]` 线和它的 must_read，从"下一步"接着干，不回放历史。上下文被压缩后 SessionStart 钩子会把看板重新打进来，以它为准。
- **开一条线**：在 OVERVIEW 看板加一块（大线外挂 `tracks/<id>.md`）。长任务在阶段性节点就把进展写回看板，别等收尾——上下文随时可能被压缩。
- **造新前先查**：有 LSP 用 findReferences；否则 grep + 读候选 + 查 reference；大工程用 nexus-query/CodeGraph（若装）。命中就复用；确需造新且该成权威件的，记进 reference。
- **改接口前先查引用**：LSP findReferences/incomingCalls，否则 grep；不盲改。
- **撞见无关问题**：先在 knowledge + inbox 检索，没有再整理投 inbox；不无脑 append。
- **验证出根因**：用 root-cause 技能沉淀进 knowledge，按捕获纪律定 draft/active。
- **多代理/子代理**：只有**主代理**写 `.aip/`；子代理只汇报发现，不落盘。派活时把相关的 knowledge/reference 条目喂给子代理，别让它重新踩坑。
- **worktree / 分支并行**：看板只在主分支维护；并行线各用一个 `tracks/<id>.md`，合并时看板只留一行指向它，减少冲突。分支上产生的 knowledge/decisions 条目随分支合并，合并后跑一次 `aip_check`。

## 捕获纪律（所有沉淀通用）
动笔前过一遍 review 自检清单（见 `reference/review-checklist.md`）→ 通过才写 → 当场知会用户（改了哪些文档、每处一句话理由）→ 随本次工作同一次 git 提交留痕。
- `状态: draft` = 证据不足、自己拿不准；`active` = 已按自检清单核过。AI 可以直接写 active，但要在知会里给依据。
- 只收**已验证**的进 knowledge；推测投 inbox。琐碎且同文件的顺手修、不登记。
- **推翻决策/规约**：追加新条目并注明「取代 ADR-N + 理由」，旧条目标记已取代；不原地改写或删除。
- **删除/合并**：只认两个理由——已被证明错误、或与另一条重复。知会里写明删了什么、依据是什么。

**整份 `.aip/` 的 review**（满足任一就做，做法见 `reference/review-checklist.md`）：本次改动含删除或合并；单次改动条目数 ≥ 3；距上次 review 超过一个月；用户敲 `/aip review`。

## 完成检查（一条线做完时）
按 `reference/closure.md` 走：约束对照 → 验证闭环 → 跑 `aip_check` → 捕获回扫 → 重建派生件 → 把线移出看板。捕获回扫的逐项 yes/no 只对**改了代码或文档结构**的任务做；纯问答、一行注释这类小改动不必走完整回扫，但 `aip_check` 照跑。

## `/aip init`（唯一人敲的命令，两阶段）
阶段 A 跑脚本 `python <skill>/scripts/aip_init.py --repo-root .`（建骨架、装钩子、刷新引导块，幂等不覆盖）；阶段 B 由 AI 自己看项目填空白文件，不向用户提问。细节见 `reference/init.md`。

## 不做
- 不探查/记录本机装了哪些外部工具（平台每会话已给可用清单）。
- 不为搜索加后端（破坏零依赖）。
