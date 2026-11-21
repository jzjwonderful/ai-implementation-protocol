---
name: aip
description: Use when the user runs `/aip` (Claude Code) or `$aip` (Codex), or whenever AI Implementation Protocol applies — project state lives in `.aip/` living docs, the AI keeps them current and resumes from the work lines in `.aip/tracks/`. Human only types `/aip init` once per repo.
argument-hint: "[init | review | update | migrate]"
---

# AIP 引擎（技能为主，AI 自主驱动）

AIP 用 `.aip/` 下的活文档管项目级状态，零依赖、随处可用。人只在装 AIP 时敲一次 `/aip init`（Codex 里是 `$aip init`），其余动作由 AI 按时机自己触发。每次用到 AIP 要**当场知会用户**（记了什么、参考了哪条、跑了什么检查）——这是人事后抽查的唯一依据，不能省。

## 脚本在哪
脚本和模板都在 **本 SKILL.md 所在目录** 下的 `scripts/` 与 `templates/`。下文 `<skill>` 指这个目录，命令一律写全路径，例如 `python3 <skill>/scripts/aip_check.py --repo-root .`。

脚本要 Python 3.9 以上。命令里的 `python3` 只是示例：会话开始看板末尾会打出钩子探测到的解释器，本会话都用它；没有看板（比如 Codex）就自己探测一次（`python3 --version`，不行再 `python --version`，要 3.9 以上；只有 Python 2 就告诉用户装 Python 3）。钩子没反应或脚本报错时跑 `aip_doctor.py --repo-root .` 查安装。

## 活文档（去哪找什么）
**条目：一条一个文件。** 文件名 `<时间戳>_<类型>_<状态>_<简述>.md`，比如 `20260928-153012_knowledge_active_gbrain健康分是扣分制.md`：
- `.aip/knowledge/` — 验证过的技术坑/根因（active / draft / fixed / superseded）。
- `.aip/decisions/` — 架构/方向级决策，不是任务级需求（accepted / superseded）。
- `.aip/inbox/` — 旁路问题收件箱（open / closed / wontfix，wontfix = 看过了决定不做）。
- `.aip/tracks/` — 在建线（active / blocked / paused），做完就删文件。
- `.aip/reuse/` — 可复用实现（active / superseded）：标题写能力，正文写钦定实现和边界，文件头 `paths` 必填。

时间戳是创建时间（精确到秒）。简述由你起：8–24 字、说清这条是什么的短名字（「会话里重启Kite会带走会话环境」），不是把标题截半句；标题超过 24 字时 `new` 必须给 `--slug`。简述定了就不改（改了标识就变了）。条目的标识是「时间戳_简述」：引用别的条目、代码注释锚点一律写完整标识（`.aip/knowledge/20260928-153012_gbrain健康分是扣分制`），不只写时间戳，也不带状态。状态在文件名和文件头里各一份，改状态必须走脚本。并行分支各自新增是不同的文件，合并不冲突。

**整篇文档：**
- `.aip/conventions.md` — 每次动手前读：只放不管做什么任务都会踩到的铁律、核心不变量、构建验收流程。
- `.aip/reference/<主题>.md` — 按需读的主题资料（术语、环境变量、某个模块的做法……）。一个主题一个文件，文件头写 `title`、`read_when`（什么时候该读）、`paths`（涉及哪些代码，可选），模板 `templates/topic-template.md`。
- `.aip/specs/<名字>.md`（可选，有长需求/设计文档才建）：一篇讲一个模块或一次改造，文件头同主题文件、再加一句现在的状态（在做 / 已实现 / 被哪条取代）。在建线的「先读」指到具体章节，别让人整篇读；超过 3 万字按章节拆开。
- `.aip/config.yaml` — 验证命令（`gates`）、上次整份 review 的日期、`aip_version`、`size_check_paths`（可选）。零配置起步，用到再填。

**看板不存文件。** 会话开始钩子直接从目录读，打印在建线全文、待处理旁路问题的文件名、主题目录（主题 + 什么时候读）。没有钩子（如 Codex）就自己读 `tracks/` 下的文件、列 `inbox/` 下带 `_open_` 的文件名、跑 `aip_lookup.py index`。知识、决策、可复用实现不上看板，用到时按文件名或 `aip_item.py list --grep` 找。

**按需读，不整篇全读。** 主题文件按「什么时候读」挑相关的读。改代码前跑 `aip_lookup.py --repo-root . relevant <要改的文件>`：按文件头 `paths`、条目正文里反引号写的带目录的文件路径（只比改动的代码文件）、改动文件里的条目锚点列出相关的主题和条目（只按任务说法挑会漏）；Edit / Write 之后 PostToolUse 钩子会对刚改的文件自动跑一次（一个会话里同一个文件只提一次），提交前钩子再对暂存的改动列一次（锚点只看改动处附近），都只列不挡。命中多时按轻重排、每类限量、只列最要紧的 12 条（`--all` 全列）：主题资料 → 改动处写了锚点的 → 验证过的坑 → 钦定实现 → 决策 → 旁路问题；active 知识引用的代码在「最后复核」之后改过的，就地提一句顺手重验。

**条目脚本 `aip_item.py`**（`<skill>/scripts/` 下，都带 `--repo-root .`）：
- 找：`list --type knowledge --status active [--grep 关键词]`（关键词先查文件头，再查正文——正文命中单独列、带上命中那句，`--all` 全列）；`show <标识 / 文件名 / 迁移前的旧编号>`。先按文件名和 `list` 找相关的再打开读，不要通读整个目录。
- 建：`new --type knowledge --title "一句话标题" --category .. --scope .. [--paths 涉及的代码] [--slug 简述] [--status draft]`，知识条目必须给分类和适用范围，可复用实现必须给 `--paths`；打印文件路径，正文按模板生成，之后直接编辑文件补内容。
- 改状态：`status <标识> <新状态> [--by <取代它的条目标识，或一句话>]`。别手动改文件名。在建线改 `done` 就是删掉文件。
- 重验过：`reviewed <标识>`（知识条目「最后复核」改成今天）。

## AI 自主行为（按时机触发）
- **接手/新会话**：读看板上的在建线和它的「先读」，从「下一步」接着干，不回放历史。钩子报「检出落后远端」或「.aip/ 有没提交的改动」时，先告诉用户，同步或提交后再写 `.aip/`。
- **上下文要被压缩 / 刚被压缩**：压缩前 PreCompact 钩子把「摘要里必须留下什么」和在建线原文交给写摘要那一轮；压缩后 SessionStart 钩子重新打印看板——**以在建线文件为准**，上下文里还没写回文件的进展先补写再继续。没有这两个钩子（如 Codex）就在长任务的阶段性节点自己写回在建线。
- **开一条线**：`aip_item.py new --type track`，写目标、卡在哪、下一步、先读四项。长任务在阶段性节点就把进展写回这个文件，别等收尾。只写往前看的内容，过程和结论进 git 提交或知识条目；超过 12 行会被提醒压缩。
- **收线跟着最后一个 MR 走**：线和代码在同一个分支里提交；做完时在这条线最后一个 MR 里 `aip_item.py status <线> done`（删掉文件），不等合入。合入了主干上线就没了；没合入主干上它还在，不用回滚。线剩下的事不在本仓库（别的仓库、本机操作）就收掉，剩下的投 inbox 或去那个仓库开线。
- **造新前先查**：有 LSP 用 findReferences；否则 grep + 读候选 + `aip_item.py list --type reuse --grep 能力`。命中就复用；确需造新且该成权威件的，`aip_item.py new --type reuse` 记一条，写明为什么已有的不适用。
- **改接口前先查引用**：LSP findReferences/incomingCalls，否则 grep；不盲改。
- **用到即核**：读到的 `.aip/` 条目、项目规约、项目技能、说明文件（`CLAUDE.md` / `AGENTS.md`）和代码或现状对不上，当场改：knowledge 重验后 `aip_item.py reviewed`，不再成立的改 `fixed` 或 `superseded`；规约、技能、说明文件改正文；要人拍板的投 inbox。随本次工作同一次提交并知会。知道错了不改，比没写更糟。
- **到期提醒**：会话开始和 `aip_check` 列出该处理的事（`aip_upkeep.py`，只提醒不挡提交），按轻重排、只列前 5 项，完整清单 `aip_upkeep.py --all`。用到这些条目时顺手复核，或在当前任务收尾时处理；要延后就跟用户说一声。「引用的代码改过了」不进这份清单（活跃仓库一次能报上百条，没人看得完），改到那个文件时由反查就地提示。
- **有更新先说**：会话开始会静默查一次引擎有没有新版本。打出「AIP 有更新」时先告诉用户，同意再跑 `/aip update`，然后继续当前任务。
- **撞见无关问题**：先在 knowledge/ 和 inbox/ 里按文件名和 `list --grep` 检索，没有再 `aip_item.py new --type inbox`；不无脑新建。明确决定不做的改 `wontfix`，别留着占 open。
- **验证出根因**：记成知识条目。先检索去重，像的就补进那一条或在 `related` 加关联，不像才新建 `--type knowledge`，再编辑生成的文件填症状、根因、证据（操作步骤类的再填做法）。按捕获纪律定 draft/active。
- **多代理/子代理**：只有**主代理**写 `.aip/`；子代理只汇报发现，不落盘。派活时把相关的条目和主题文件喂给子代理，别让它重新踩坑——装了 SubagentStart 钩子的话，在建线、主题目录和这两条规矩会自动注入给它。
- **worktree / 分支并行**：每条线一个 `tracks/` 文件，各分支新增的条目都是新文件，合并不冲突。两边改了同一条的状态时 git 会报改名冲突，留一个、`aip_check` 查重复标识。合并后跑一次 `aip_check`。

## 沉淀（所有写入通用）
动笔前过一遍 `reference/review-checklist.md`（七条自检清单 + 捕获纪律：状态怎么定、代码位置要用反引号写出来、推翻决策是新建一条、删除合并只认两个理由）→ 通过才写 → 当场知会用户（改了哪些文档、每处一句话理由）→ 随本次工作同一次 git 提交留痕。只收**已验证**的进 knowledge，推测投 inbox；琐碎且同文件的顺手修、不登记。

**整份 `.aip/` 的 review**（满足任一就做，做法同上面那份清单）：本次改动含删除或合并；单次改动条目数 ≥ 3；距上次 review 超过一个月（看 `config.yaml` 的 `review_last_full`，逾期会被提醒）；用户敲 `/aip review`。做完把 `review_last_full` 改成当天。

## 完成检查（一条线做完时）
按 `reference/closure.md` 走：约束对照 → 验证闭环 → 跑 `aip_check` → 捕获回扫 → 删掉线（随最后一个 MR）。捕获回扫的逐项 yes/no 只对**改了代码或文档结构**的任务做；纯问答、一行注释这类小改动不必走完整回扫，但 `aip_check` 照跑。

## 和 AI 自带记忆的边界
AI 工具自己的跨会话记忆是个人级的（存本机、只有它自己看得到）；AIP 文档是**项目级**的（进仓库、随代码走、给所有人所有工具看）。关于这个项目的事实、决策、坑、规约只记 AIP，别在个人记忆里再存一份；关于用户本人的偏好和习惯归工具自己的记忆，不进 `.aip/`。两边冲突以 `.aip/` 为准，发现了就修 `.aip/`。

## 通用开发纪律（随 AIP 分发，对所有项目生效）
1. **不说黑话**：文档/注释/会话用大白话，不用晦涩比喻和生造词；公认技术名词除外。
2. **注释不引外部编号**：代码注释不引 plan/需求/任务/issue 编号或外部文档名（会漂移、改名即误导）；只说代码本身的意图和约束。
3. **编码交付要闭环验证**：动手前读懂项目的验证机制（相关 plan/需求、现有测试、构建/lint 命令、CI 配置），动手后逐项对照并执行。验证结果与目标一致才能说"完成"，不得靠删除、跳过、削弱测试绕过。
4. **会越写越大的内容拆开写**：一条条追加的记录一条一个文件；整篇说明按主题拆成多个文件。上限（`.aip/` 下和 `size_check_paths` 列的文档，`aip_version` 到 0.8.0 起 `aip_check` 报红，到九成时提醒）：`conventions.md` 整篇 8000 字、每节 3000 字；其余单个文件 3 万字；单行 1000 字；表格 30 行；0.8.1 起项目自己的技能正文 8000 字。中文一个字约 0.8 个 token，按这个估一次读进来要花多少。

## 命令（人敲的）
- `/aip init`（唯一必须人敲的，两阶段）：阶段 A 跑 `python3 <skill>/scripts/aip_init.py --repo-root .`（建骨架、装钩子、刷新引导块，幂等不覆盖）；阶段 B 由 AI 自己看项目填空白文件，不向用户提问。细节见 `reference/init.md`。
- `/aip update`：更新已装的 AIP 技能，见 `reference/update.md`。**升级后整理**：会话开始提醒「还没按新模板整理」时先跟用户说，同意后按 `reference/upgrade.md` 从 `aip_version` 之后的版本逐节做。
- `/aip migrate`：0.5.0 之前的旧布局（`knowledge.md` 等大文件）迁成一条一个文件，见 `reference/migrate.md`。
- `/aip review`：整份 `.aip/` 的 review，见上文。

## 不做
- 不探查/记录本机装了哪些外部工具（平台每会话已给可用清单）。
- 不为搜索加后端（破坏零依赖）。
