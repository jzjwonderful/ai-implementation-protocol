---
title: 本仓库自举——从旧 `project_docs/` 迁入 `.aip/`
status: accepted
aliases: ADR-1
---

- 日期 / 状态（迁移前）: 2026-06-23 / 采纳
- 背景：AIP 自身的开发状态长期停留在旧布局 `project_docs/`（`.aip/` 之前的位置），且 `_runtime/current_task.json` 冻结在 4 月已完成的 feature，6 月的开发改用 `docs/superpowers/` 记录。结果是"主打防漂移的工具，自己漂出了协议"——`aip check --repo-root .` 直接报 `Missing AIP directory`。
- 决策：跑 `aip init` 建 `.aip/`；把 `project_docs/features/` 下 5 个历史 feature 包迁入 `.aip/features/` 保留开发史；删除遗留 `project_docs/`（仅含 7 行 README、冻结旧指针、92 行陈旧协议副本，无实质活文档）；填 `.aip/config.yaml`（真源=协议文档、唯一机器检查=unittest、process_skills=superpowers）。当前不建新工作包，`current_task.feature_id` 留空（check 跳过活动包校验，可当纯提交检查）。
- 理由：保留历史优于清空（4 月 bootstrap 的 spec/plan 是真实开发记录）；删 `project_docs/` 而非加入扫描豁免，是因为豁免等于承认协议外并行状态长期存在，治标不治本。代价：`.aip/features/` 多 5 个已完成的休眠旧包（不被 check 校验，无害）。
- 影响：删除 `project_docs/`（顶层布局变化，README 已与 `.aip/` 描述一致）；`docs/superpowers/` 仍是 superpowers 方法层产物，按协议属 spec/plan 槽的方法侧，后续新特性应落 `.aip/features/<id>/`。
  （注：本条末句的「后续落 `.aip/features/<id>/`」前瞻指引已被 20260626-123342_协议从按需求分轨改为扁平活文档 取代——新模型无 per-feature 工作包。）
