---
title: 改完 scripts/ 必须先跑 sync_plugin.py，再跑 install_claude_plugin.py
status: superseded
category: process-lifecycle
scope: 凡改动 `scripts/`、`docs/`、`templates/`、`schemas/` 任意文件后想让安装生效，均需此顺序；AI 辅助改动时须确认落点是 repo root `scripts/`，不是 `~/plugins/`
last_reviewed: 2026-06-27
superseded_by: 20260914-224845_改引擎要改仓库里的技能目录不是已安装的副本
aliases: K-001
---

- 状态说明（迁移前）: superseded(by 20260914-224845_改引擎要改仓库里的技能目录不是已安装的副本)
- 症状: 改了 root `scripts/` 下的文件，执行 `install_claude_plugin.py --force` 后到其他仓库跑 `aip init`，CLAUDE.md 没有更新，仍是旧内容
- 根因: `install_claude_plugin.py` 复制的是 `plugins/ai-implementation-protocol/scripts/`（plugin 副本），不是 root `scripts/`。root `scripts/` 是唯一真源，必须先用 `sync_plugin.py` 把改动同步到 plugin 副本，再安装
- 证据: 改了 `scripts/aip_discovery.py` 后直接跑 install，发现 `plugins/ai-implementation-protocol/scripts/aip_discovery.py` 仍是旧内容；跑 `sync_plugin.py` 后两边一致。二次踩坑：AI 把改动写进了 `~/plugins/`（已安装路径），sync 时反被 repo root 旧内容覆盖，改动消失
- 关联:
- 关联: 20260914-224845_引擎并入技能目录单副本分发（0.3.0 起引擎只有一份，sync_plugin.py 已删，此坑不再存在）
