---
title: 看板不存文件、按目录打印；在建线做完即删，随最后一个 MR 提交
status: accepted
related: 20261001-004400_条目改成一条一个文件
---

- 背景: 0.5.0 起 `OVERVIEW.md` 由脚本生成、不进仓库，但只在会话开始钩子里刷新；没装钩子的仓库（包括本仓库）读到的是过期看板，一次把「有一条在建线」读成了「没有在建线」。看板里「最近 5 条知识 / 决策」「参照条数」是随便截的一段，找知识靠的是文件名。另外线标 done 要等 MR 合入后再单独提一个 MR。
- 决策: 取代 20261001-004400_条目改成一条一个文件 的第 (2) 点（看板现场生成）：(1) 不再生成 `OVERVIEW.md`；会话开始钩子直接从目录打印在建线全文和 open 旁路问题的文件名，没有钩子就自己看目录；知识、决策、参照不上看板，用 `aip_item.py list --grep` 或文件名查。(2) 在建线只有 active / blocked / paused，做完 `aip_item.py status <线> done` 就是删文件；收线放进这条线最后一个 MR，不等合入。(3) 项目级钩子命令先找 python3、再找 python，只用 3.9 以上的。版本 0.7.0。
- 理由: 能从文件名和目录得到的不再存一份，就不会过期。收线和代码在同一个 MR：合入了线自然没了，被拒了主干上线还在，不用回滚也不用补 MR。线只写往前看的内容，做完没有可留的，过程在 git 里。没选「按分支合没合自动判定」：GitLab 压缩合并后 `git branch --merged` 认不出，本机没拉也认不出。
- 影响: `aip_session_start.py`、`aip_item.py`、`aip_check.py`、`aip_init.py`、`aip_migrate.py`、`install_hooks.py`，删 `aip_overview.py`；说明文件托管块、SKILL.md、`reference/`；既有仓库按 `reference/upgrade.md` 的 0.7.0 一节整理。
