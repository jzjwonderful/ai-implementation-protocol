---
title: 协议文档从 per-feature/bug 轨道模型迁到扁平活文档模型
status: accepted
aliases: ADR-2
---

- 日期 / 状态（迁移前）: 2026-06-26 / 采纳（取代 20260623-230835_本仓库自举从旧project-docs迁入aip 的前瞻部分）
- 背景：引擎代码（`_aip_common` 的 `PROJECT_LIVING_FILES`/`FORBIDDEN_SLOT_FILENAMES`、`aip_init`、`aip_check`）早已落到「8 个活文档 + `OVERVIEW.md` 看板管任务线」的扁平模型，但 `docs/protocol.md`、`docs/architecture|adaptation|examples.md`、`root-cause` 技能、`.aip/README.md` 仍描述旧模型（`STATUS.md`/`canonical-assets.md`/`findings.md`、per-feature 工作包、`_runtime/current_task.json`、`task_board`/`handoff`/`verification`、bug 轨道/`report.md`）。文档与代码对不上，会误导接手者。
- 决策：把上述文档全部改写到现行模型；旧槽位名作为迁移守卫列入「不得再出现」（已在 `_aip_common.FORBIDDEN_SLOT_FILENAMES`）。角色搬迁：现状真理源 `STATUS.md`→`OVERVIEW.md`，侧发现 `findings.md`→`inbox.md`，复用登记 `canonical-assets.md`→`reference.md`。删掉已不存在的 `schemas/*.json` 相关描述。
- 理由：代码是事实源，文档必须跟齐；保留旧描述等于把废弃模型当权威，正是 AIP 要防的漂移。
- 影响：`docs/protocol.md` 重写；`docs/architecture|adaptation|examples.md`、`root-cause` 技能、`.aip/README.md` 改写；`.aip/config.yaml` 的 `STATUS.md` 铁律改为 `OVERVIEW.md`；插件副本经 `sync_plugin.py` 再生。锚点沿用英文（ADR/K/I），仅在各活文档首次出现处加中英对照说明。
