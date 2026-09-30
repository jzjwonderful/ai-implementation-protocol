---
title: 知识、决策、旁路问题、在建线改成一条一个文件；看板现场生成；附迁移工具
status: accepted
---

- 背景：0.4.x 之前一类条目挤在一个大文件里（knowledge.md、decisions.md、inbox.md），编号靠手发（K-185、ADR-3、I-14）。在 ai-kits 仓库里，分支和工作树并行加条目时撞号（I-14、I-25 各有两条），大文件合并常冲突；OVERVIEW 手写看板越写越长，会话开始打出 47KB、耗时 9–11 秒；到期提醒一次列几十条，没人看。
- 决策：(1) 四类条目一条一个文件，放 `.aip/knowledge/`、`decisions/`、`inbox/`、`tracks/`，文件名 `时间戳_类型_状态_简述.md`，时间戳精确到秒；条目标识是「时间戳_简述」，引用必须写全，只写时间戳不算。简述由 AI 起：8–24 字、说清这条是什么的短名字，标题超过 24 字时必须给，按分句截只作兜底。状态同时写在文件名和文件头（`status:`），检查两处一致；改状态用 `aip_item.py status` 改名。(2) `OVERVIEW.md` 由脚本现场生成、不进仓库；`knowledge_index.md` 取消。(3) 到期提醒分优先级，每条只归一类，默认只列前 5 条加一行总数（`--all` 看全部）；会话开始另报「检出落后上游」和「.aip 有没提交的改动」。(4) 新增 `aip_migrate.py` 与 `/aip migrate`：旧编号写进 `aliases`，正文里的旧编号换成完整标识，代码注释锚点可选改写；迁移出来的条目时间戳取标题第一次进 git 的那次提交的时间；标题太长的由 AI 在对照表里起简述。版本升到 0.5.0。
- 理由：文件名靠时间戳加简述天然不撞，并行分支各加各的文件，合并不冲突；状态在文件名里，`ls` 就能按类型、新旧、状态筛。考虑过 SQLite：状态好管，但不是明文、git 里看不出改了什么、工作树之间合并更难，放弃。时间戳不用毫秒，因为简述已经能区分同一秒的两条。简述不从标题硬截：ai-kits 的 268 条标题里 216 条超过 24 字，硬截多半断在半句。迁移时间取「标题第一次进 git」而不是 git blame：blame 给的是最后一次改标题的时间，旁路问题关闭时加删除线就变成了关闭那天。代价是一次提交带进来的条目同一秒（ai-kits 有一次合并提交带进 89 条），靠简述区分。考虑过取条目里写的日期，放弃：没有时分秒，正文里的日期也常是例子或别的事件的日期。代价：老仓库要跑一次迁移，旧编号的引用要靠 `aliases` 兜底。
- 影响：新增 `aip_item.py`、`aip_migrate.py`、四个条目模板与 `reference/migrate.md`；重写 `aip_check.py`、`aip_upkeep.py`、`aip_overview.py`；`aip_session_start.py`、`aip_init.py`、`aip_doctor.py`、`aip_discovery.py`（托管块第 3 版）、`install_hooks.py` 跟着改；删除 `aip_knowledge.py` 和旧的四个大文件模板；SKILL.md、reference/、docs/、README 同步。本仓库 `.aip/` 已按此迁移。
