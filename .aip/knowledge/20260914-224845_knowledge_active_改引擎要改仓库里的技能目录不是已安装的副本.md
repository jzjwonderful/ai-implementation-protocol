---
title: 改引擎要改仓库里的技能目录，不是已安装的副本
status: active
category: process-lifecycle
scope: 凡改 AIP 引擎本身（`plugins/ai-implementation-protocol/skills/` 下任何文件）。正确落点是仓库源；改完重跑安装器让副本更新。0.4.0 起 `/aip update`（`aip_update.py --apply`）从远端取新版也会整目录替换已装副本，副本里的手改同样会被冲掉
last_reviewed: 2026-10-01
aliases: K-002
---

- 症状: 改了 AIP 脚本/模板/技能正文，重开会话后行为没变；或者改动过一阵子"消失"了
- 根因: 改动写到了安装副本（`~/.claude/skills/aip/`、`~/plugins/ai-implementation-protocol/`、`~/.agents/skills/aip/`）。安装器是"整目录覆盖"，下一次安装会把副本打回仓库内容；而仓库里的源没改，git 里也没有痕迹
- 证据: 20260616-221449_改完scripts要先sync再安装 记录的第二次踩坑就是这样丢的改动（写进 `~/plugins/` 后被覆盖）。0.3.0 重构后安装器 `install_claude_plugin.py` 对 `~/.claude/skills/<skill>/` 先 rmtree 再 copytree（见 `tests/test_install_claude_plugin.py` 的 stale.txt 用例），任何副本内改动都会被清掉
- 现状: 本仓库 0.7.0 起不再靠全局安装，`.claude/skills/aip`、`.codex/skills/aip` 是项目级安装的拷贝，同样会被安装器整目录覆盖；`aip_check` 的 `check_engine_copies` 比对副本和源，改了源忘了重装会报红
- 关联: 20260616-221449_改完scripts要先sync再安装 / 20260914-224845_引擎并入技能目录单副本分发
