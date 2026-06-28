---
name: aip
description: Use when the user invokes `$aip` 或要应用 AI Implementation Protocol。Skill 为主的引擎：AIP 行为由 AI 按时机自主触发，人日常只敲 `$aip init`。机器活只调 aip_check.py / aip_knowledge.py / aip_overview.py。
---

# AIP 引擎（技能为主，AI 自主驱动）

AIP 用七类活文档管项目级状态，零依赖、随处可用。命令收敛为 AI 自主行为；人只在装 AIP 时敲 `$aip init`。每次用到 AIP **必须立刻知会用户**（记了什么、参考了哪条、跑了什么检查），**禁止省略**，这是 AIP 可观测的基础。

> **脚本在哪**：下文 `<engine>` 指 AIP 引擎根（带 `scripts/`、`templates/` 的那个目录），标准安装位置是 `~/plugins/ai-implementation-protocol`。脚本随引擎走、**不拷进目标项目**，所以路径要写全（裸 `scripts/aip_init.py` 在项目里找不到）。若不在标准位置，就定位含 `scripts/aip_init.py` 的目录当 `<engine>`。脚本自带模板解析，只用 `--repo-root` 指目标项目即可。

## 七类活文档（去哪找什么）
- `.aip/OVERVIEW.md` — 多线看板（手写顶部）+ 自动摘要。开始/接手任务前**必须先读，禁止跳过**。
- `.aip/decisions.md` — 架构/方向级决策（非任务级需求）。
- `.aip/knowledge.md`(+`_index`) — 验证过的技术坑/根因。
- `.aip/reference.md` — 领域概念/术语、核心铁律、可复用实现（裁决）。
- `.aip/inbox.md` — 旁路问题收件箱。
- `.aip/conventions.md` — 项目规约。
- `.aip/config.yaml` — 工程配置（构建/测试命令等）。零配置起步，不在 init 时问，用到再填。

## 通用开发纪律（随 AIP 分发，可增补）
> 这一节是 AIP 随插件分发、对所有项目生效的纪律清单的唯一来源。以后增补规则/技巧只往这里加。
1. **禁止说黑话**：所有文档/注释/会话大白话，禁止晦涩比喻和生造术语（"scales to zero"/"footgun"/"毕业"等），公认技术名词除外。
2. **注释不引外部编号**：代码注释禁止引用 plan/需求/任务/issue 编号或外部文档名（会漂移、改名即误导）；注释只说代码本身的意图/约束，简洁自足，能不写就不写。

## AI 自主行为（按时机触发，不用人敲；下列每条均为强制，禁止跳过）
- **接手/新会话**：**必须**读 OVERVIEW 的 `▶[active]` 线 + 它的 must_read，从下一步接着干；**禁止**回放历史。
- **开一条线**：**必须**在 OVERVIEW 看板加一块（大线外挂 `tracks/<id>.md`）。
- **造新前先查**：**必须**按退化链先查——有 LSP 用 findReferences；查同义实现用 grep+读候选+查 reference；大工程用 nexus-query/CodeGraph（若装）。命中**必须**复用；确需造新且该成权威件 → **必须**记 reference，**禁止**跳过。
- **改接口前先查引用**：**必须**先查 LSP findReferences/incomingCalls，否则 grep；**禁止**盲改。
- **撞见无关问题**：**必须**先在 knowledge+inbox 检索，没有再整理投 inbox；**禁止**无脑 append。
- **验证出根因**：**必须**用 root-cause 沉淀进 knowledge（先写 draft，**禁止**直接 active）。

## 捕获纪律（所有沉淀通用）
拟草稿 → 读目标文档比对去重（像就并/加关联，不像才新增）→ 写 `状态: draft` → 知会用户。draft 直到人确认才 active；从不擅自当权威、不静默改旧内容。只收**已验证**的进 knowledge；琐碎且同文件的顺手修、不登记。

## 完成检查（一条线做完时，每步均为强制，禁止跳过任何一步）
1. **必须**跑 `python <engine>/scripts/aip_check.py --repo-root .`；红了**必须挡住**逐条修，**禁止**绕过继续。
2. 范围内纠偏：只整理本次碰过的条目及其直接关联（draft/diff，**禁止**静默改旧内容）。
3. 捕获回扫（每类**必须**逐项给 yes/no，**禁止**整体跳过；OVERVIEW **不替代**这些文档）：
   - **knowledge**：验证出可复现的坑或根因？→ yes 写 draft；no 一句说为什么没有
   - **reference**：产出可复用实现或需要定锚的概念？→ yes 写 draft；no 一句说为什么没有
   - **conventions**：发现新规约或现有规约需要修正？→ yes 写 draft；no 一句说为什么没有
   - **inbox**：撞见尚未处理的旁路问题？→ yes 投 inbox；no 一句说为什么没有
   - **config**：有新的构建/测试命令需要记录？→ yes 更新 config.yaml；no 一句说为什么没有
4. 改完 knowledge **必须**跑 `python <engine>/scripts/aip_knowledge.py --repo-root .`；**必须**刷新总览 `python <engine>/scripts/aip_overview.py --repo-root .`。
5. **必须**把该线移出看板，**禁止**线完成后继续挂在看板上。

## $aip init（唯一人敲的命令）
`python <engine>/scripts/aip_init.py --repo-root .` —— 零配置：建 `.aip/` 骨架、写引导块、装钩子；**不问工程任何事**，工程信息（构建/测试命令、规约、概念）用到时自动捕获。

## 不做
- 不探查/记录本机装了哪些外部工具（平台每会话已给可用清单，用时现场挑）。
- 不为搜索加后端（破坏零依赖）。
