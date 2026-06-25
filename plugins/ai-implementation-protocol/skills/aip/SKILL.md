---
name: aip
description: Use when the user invokes `$aip` 或要应用 AI Implementation Protocol。Skill 为主的引擎：AIP 行为由 AI 按时机自主触发，人日常只敲 `$aip init`。机器活只调 aip_check.py / aip_knowledge.py / aip_overview.py。
---

# AIP 引擎（技能为主，AI 自主驱动）

AIP 用六类活文档管项目级状态，零依赖、随处可用。命令塌缩为 AI 自主行为；人只在装 AIP 时敲 `$aip init`。每次用到 AIP 都**吭一声**报给人（记了什么、参考了哪条、跑了什么闸门），方便人观测效果。

## 六类活文档（去哪找什么）
- `.aip/OVERVIEW.md` — 多线看板（手写顶部）+ 自动摘要。开始/接手任务前读它。
- `.aip/decisions.md` — 架构/方向级决策（非任务级需求）。
- `.aip/knowledge.md`(+`_index`) — 验证过的技术坑/根因。
- `.aip/reference.md` — 领域概念/术语、核心铁律、可复用实现（裁决）。
- `.aip/inbox.md` — 旁路问题收件箱。
- `.aip/conventions.md` — 项目规约。

## 通用开发纪律（随 AIP 分发，可增补）
> 这一节是 AIP 随插件分发、对所有项目生效的纪律清单的唯一来源。以后增补规则/技巧只往这里加。
1. **禁止说黑话**：所有文档/注释/会话大白话，禁止晦涩比喻和生造术语（"scales to zero"/"footgun"/"毕业"等），公认技术名词除外。
2. **注释不引外部编号**：代码注释禁止引用 plan/需求/任务/issue 编号或外部文档名（会漂移、改名即误导）；注释只说代码本身的意图/约束，简洁自足，能不写就不写。

## AI 自主行为（按时机触发，不用人敲）
- **接手/新会话**：读 OVERVIEW 的 `▶[active]` 线 + 它的 must_read，从下一步接着干；不回放历史。
- **开一条线**：在 OVERVIEW 看板加一块（大线外挂 `tracks/<id>.md`）。
- **造新前先查**：按退化链——有 LSP 用 findReferences；查同义实现用 grep+读候选+查 reference；大工程用 nexus-query/CodeGraph（若装）。命中复用；确需造新且该成权威件 → 记 reference。
- **改接口前先查引用**：有 LSP 用 findReferences/incomingCalls，否则 grep。
- **撞见无关问题**：先在 knowledge+inbox 检索，没有再整理投 inbox（不无脑 append）。
- **验证出根因**：用 root-cause 沉淀进 knowledge（先写 draft）。

## 捕获纪律（所有沉淀通用）
拟草稿 → 读目标文档比对去重（像就并/加关联，不像才新增）→ 写 `状态: draft` → 吭一声。draft 直到人确认才 active；从不擅自当权威、不静默改旧内容。只收**已验证**的进 knowledge；trivial 且同文件的顺手修、不登记。

## 完成闸门（一条线做完时）
1. 跑 `python scripts/aip_check.py --repo-root .`（红了挡住，逐条修）。
2. 范围内纠偏：只整理本次碰过的条目及其直接关联（draft/diff，不静默改）。
3. 捕获回扫：列本次具体学到/碰到的候选——进 knowledge/inbox/reference/conventions/config？
4. 改完 knowledge 跑 `python scripts/aip_knowledge.py --repo-root .`；刷新总览 `python scripts/aip_overview.py --repo-root .`。
5. 把该线移出看板。

## $aip init（唯一人敲的命令）
`python scripts/aip_init.py --repo-root .` —— 零配置：建 `.aip/` 骨架、写引导块、装钩子；**不问工程任何事**，工程信息（构建/测试命令、规约、概念）用到时自动捕获。

## 不做
- 不探查/记录本机装了哪些外部工具（平台每会话已给可用清单，用时现场挑）。
- 不为搜索加后端（破坏零依赖）。
