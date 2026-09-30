---
name: aip
description: Use when the user runs `/aip` (Claude Code) or `$aip` (Codex), or whenever AI Implementation Protocol applies — project state lives in `.aip/` living docs, the AI keeps them current and resumes from the OVERVIEW board. Human only types `/aip init` once per repo.
argument-hint: "[init | review | update | migrate]"
---

# AIP 引擎（技能为主，AI 自主驱动）

AIP 用 `.aip/` 下的活文档管项目级状态，零依赖、随处可用。人只在装 AIP 时敲一次 `/aip init`（Codex 里是 `$aip init`），其余动作由 AI 按时机自己触发。每次用到 AIP 要**当场知会用户**（记了什么、参考了哪条、跑了什么检查）——这是人事后抽查的唯一依据，不能省。

## 脚本在哪
脚本和模板随本技能走，都在 **本 SKILL.md 所在目录** 下：`scripts/` 与 `templates/`。下文 `<skill>` 指这个目录（Claude Code 调技能时会给出它的路径；Codex 下就是本文件所在目录）。命令一律写全路径，例如：

```
python <skill>/scripts/aip_check.py --repo-root .
```

改引擎请改 AIP 仓库里的 `plugins/ai-implementation-protocol/skills/aip/`，别改这份已安装的副本；改完重跑安装器。

## 活文档（去哪找什么）
**条目：一条一个文件。** 知识、决策、旁路问题、在建线各放一个目录，文件名 `<时间戳>_<类型>_<状态>_<简述>.md`，比如 `20260928-153012_knowledge_active_gbrain健康分是扣分制.md`：
- `.aip/knowledge/` — 验证过的技术坑/根因（状态 active / draft / fixed / superseded）。
- `.aip/decisions/` — 架构/方向级决策，不是任务级需求（accepted / superseded）。
- `.aip/inbox/` — 旁路问题收件箱（open / closed）。
- `.aip/tracks/` — 在建线，看板就从这里生成（active / blocked / paused / done）。

时间戳是创建时间（精确到秒）。简述由你起：8–24 字、说清这条是什么的短名字（「会话里重启Kite会带走会话环境」），不是把标题截半句；标题超过 24 字时 `new` 必须给 `--slug`，不给会报错并附一个按分句截的参考。简述定了就不改（改了标识就变了）。条目的标识是「时间戳_简述」：引用别的条目、代码注释锚点一律写完整标识（`.aip/knowledge/20260928-153012_gbrain健康分是扣分制`），不只写时间戳，也不带状态（状态会变）。状态在文件名和文件头里各有一份，改状态必须走脚本，两处一起改。并行分支各自新增是不同的文件，不会撞号、合并不冲突。

**整篇文档：**
- `.aip/OVERVIEW.md` — 看板，**现场生成、不进仓库**：在建线全文、待处理旁路问题、知识概况、近期决策。开始/接手任务前先读；没有或不新就跑 `aip_overview.py`。
- `.aip/reference.md` — 领域概念/术语、核心铁律、可复用实现（裁决）。
- `.aip/conventions.md` — 项目规约。
- `.aip/config.yaml` — 工程配置（构建/测试命令等）。零配置起步，用到再填。

**条目脚本 `aip_item.py`**（`<skill>/scripts/` 下，都带 `--repo-root .`）：
- 找：`list --type knowledge --status active`；`show <标识 / 文件名 / 迁移前的旧编号>`。先按文件名和 `list` 找相关的再打开读，不要通读整个目录。
- 建：`new --type knowledge --title "一句话标题" [--slug 简述（标题超过 24 字时必填）] [--status draft] [--category ..] [--scope ..]`，打印文件路径；正文按模板生成，之后直接编辑文件补内容。
- 改状态：`status <标识> <新状态> [--by <取代它的条目标识，或一句话>]`。别手动改文件名。
- 重验过：`reviewed <标识>`（知识条目「最后复核」改成今天）。

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
- **接手/新会话**：读看板上 ▶ 进行中的线和它的「先读」，从「下一步」接着干，不回放历史。上下文被压缩后 SessionStart 钩子会把看板重新打进来，以它为准。钩子报「检出落后远端」或「.aip/ 有没提交的改动」时，先告诉用户，同步或提交后再写 `.aip/`。
- **开一条线**：`aip_item.py new --type track`，写目标、卡在哪、下一步、先读四项。长任务在阶段性节点就把进展写回这个文件，别等收尾——上下文随时可能被压缩。只写往前看的内容，过程和结论进 git 提交或知识条目；超过 12 行会被提醒压缩。做完改 `done`。
- **造新前先查**：有 LSP 用 findReferences；否则 grep + 读候选 + 查 reference；大工程用 nexus-query/CodeGraph（若装）。命中就复用；确需造新且该成权威件的，记进 reference。
- **改接口前先查引用**：LSP findReferences/incomingCalls，否则 grep；不盲改。
- **用到即核**：读到的 `.aip/` 条目、项目规约、项目技能、说明文件（`CLAUDE.md` / `AGENTS.md`）和代码或现状对不上，当场改：knowledge 重验后 `aip_item.py reviewed`，不再成立的改 `fixed` 或 `superseded`；规约、技能、说明文件改正文；要人拍板的投 inbox。随本次工作同一次提交并知会。知道错了不改，比没写更糟。
- **到期提醒**：会话开始和 `aip_check` 列出该处理的事（脚本 `aip_upkeep.py`，只提醒不挡提交），按轻重排好、只列前 5 项，其余给总数，完整清单用 `aip_upkeep.py --all`：说明文件里写的 AIP 脚本路径已失效；active 知识引用的文件或代码名字复核那天还在、现在没了；引用的代码在「最后复核」之后改过（reference 同样按上次整份 review 查）；逾期的整份 review；draft 条目；写太长的在建线；没写代码位置的条目满 90 天、写了但代码一直没动的满一年。每条只归一类。用到这些条目时顺手复核，或在当前任务收尾时处理；要延后就跟用户说一声。
- **有更新先说**：会话开始会查一次 AIP 引擎有没有新版本（查不了就不出声）。打出「AIP 有更新」时，先告诉用户，用户同意再跑 `/aip update`，然后继续当前任务。
- **撞见无关问题**：先在 knowledge/ 和 inbox/ 里按文件名检索，没有再 `aip_item.py new --type inbox`；不无脑新建。
- **验证出根因**：记成知识条目。先在 knowledge/ 按文件名检索去重，像的就补进那一条或在 `related` 加关联，不像才新建：`aip_item.py new --type knowledge --title "一句话" --slug <简述> --category <分类> --scope <适用范围> --status <active|draft>`，再编辑生成的文件填症状、根因、证据。按捕获纪律定 draft/active。
- **多代理/子代理**：只有**主代理**写 `.aip/`；子代理只汇报发现，不落盘。派活时把相关的 knowledge/reference 条目喂给子代理，别让它重新踩坑。
- **worktree / 分支并行**：每条线一个 `tracks/` 文件，各分支新增的条目都是新文件，合并不冲突。两边改了同一条的状态时 git 会报改名冲突，留一个、`aip_check` 查重复标识。合并后跑一次 `aip_check`。

## 捕获纪律（所有沉淀通用）
动笔前过一遍 review 自检清单（见 `reference/review-checklist.md`）→ 通过才写 → 当场知会用户（改了哪些文档、每处一句话理由）→ 随本次工作同一次 git 提交留痕。
- 知识条目：`draft` = 证据不足、自己拿不准；`active` = 已按自检清单核过；`fixed` = 缺陷已修、教训仍有用；`superseded` = 被取代（文件头 `superseded_by` 写取代它的条目标识，被某个机制取代就写一句话）。AI 可以直接写 active，但要在知会里给依据。文件名、文件头状态一致、必填字段、`last_reviewed` 是日期、引用的条目存在、标识不重复，`aip_check` 都会查。
- 只收**已验证**的进 knowledge；推测投 inbox。琐碎且同文件的顺手修、不登记。
- 知识条目里把相关代码的文件路径和类名、函数名用反引号写出来（如 `src/foo.py`、`FooService.Load`）：到期提醒靠它们判断代码改没改、名字还在不在；没写的只能按时间提醒。
- **推翻决策/规约**：新建一条决策，正文写「取代 <旧条目标识> + 理由」，旧条目 `aip_item.py status <旧> superseded --by <新>`；不原地改写或删除。
- **删除/合并**：只认两个理由——已被证明错误、或与另一条重复。知会里写明删了什么、依据是什么。

**整份 `.aip/` 的 review**（满足任一就做，做法见 `reference/review-checklist.md`）：本次改动含删除或合并；单次改动条目数 ≥ 3；距上次 review 超过一个月（看 `config.yaml` 的 `review_last_full`，逾期会被提醒）；用户敲 `/aip review`。做完把 `review_last_full` 改成当天。

## 完成检查（一条线做完时）
按 `reference/closure.md` 走：约束对照 → 验证闭环 → 跑 `aip_check` → 捕获回扫 → 重建派生件 → 把线移出看板。捕获回扫的逐项 yes/no 只对**改了代码或文档结构**的任务做；纯问答、一行注释这类小改动不必走完整回扫，但 `aip_check` 照跑。

## `/aip init`（唯一人敲的命令，两阶段）
阶段 A 跑脚本 `python <skill>/scripts/aip_init.py --repo-root .`（建骨架、装钩子、刷新引导块，幂等不覆盖）；阶段 B 由 AI 自己看项目填空白文件，不向用户提问。细节见 `reference/init.md`。

## `/aip update`（更新已装的 AIP 技能）
查：`python <skill>/scripts/aip_update.py --repo-root .`。更新：加 `--apply`，从远端浅克隆最新版、核对齐全后原地替换本机装的 aip 技能，顺手删掉以前随包分发、0.6.0 起不再提供的 root-cause、aip-brainstorm（项目级安装时 `.claude/skills` 和 `.codex/skills` 两份一起换），失败会换回原样；不需要本机有 AIP 仓库，也不走安装器。远端地址默认取安装时记下的（技能目录里的 `SOURCE.json`），项目 `config.yaml` 写了 `aip_remote` / `aip_remote_branch` 就用它们。项目级安装更新完要把技能目录的变化提交进仓库。

## `/aip migrate`（0.5.0 之前的旧布局迁成一条一个文件）
旧布局是 `knowledge.md` / `decisions.md` / `inbox.md` 各一个大文件、看板手写。会话开始报「还是旧格式」、`aip_check` 报红时，先跟用户说，同意后按 `reference/migrate.md` 走：预览 → 执行 → 收尾（撞号、代码注释锚点、说明文件、旧看板遗留内容）→ 一次提交。

## 不做
- 不探查/记录本机装了哪些外部工具（平台每会话已给可用清单）。
- 不为搜索加后端（破坏零依赖）。
