# 决策记录（ADR-lite，只追加）

> **ADR** = Architecture Decision Record（架构决策记录）；本表每条编号 `ADR-N`（如 ADR-1、ADR-2），ADR-lite 指其轻量版——一条几行即可，重在**理由**。
> **用途**：记录架构/取舍**决策连同理由**，防止多人/多轮接手时被反复重新争论。
> **维护铁律**：做出架构/取舍决策的**同次**追加一条（只追加，不删历史；被推翻就新追加一条标注"取代 ADR-N"）。
> 注：feature 工作包内的 `decisions.md` 记**该 feature 局部**的决策；本项目级表记**跨 feature、长期**的架构决策。代码注释只可引用不可变锚点 `ADR-N`，不引易漂移的章节号/计划行号。

## 格式
```
## ADR-N：<标题>
- 日期 / 状态：YYYY-MM-DD / 采纳 | 已被 ADR-M 取代
- 背景：要解决什么、约束是什么
- 决策：选了什么
- 理由：为什么这样选、放弃了什么、代价是什么
- 影响：波及哪些模块/真理源章节
```

---

<!-- 在此之下追加 ADR 条目。 -->

## ADR-1：本仓库自举——从旧 `project_docs/` 迁入 `.aip/`
- 日期 / 状态：2026-06-23 / 采纳
- 背景：AIP 自身的开发状态长期停留在旧布局 `project_docs/`（`.aip/` 之前的位置），且 `_runtime/current_task.json` 冻结在 4 月已完成的 feature，6 月的开发改用 `docs/superpowers/` 记录。结果是"主打防漂移的工具，自己漂出了协议"——`aip check --repo-root .` 直接报 `Missing AIP directory`。
- 决策：跑 `aip init` 建 `.aip/`；把 `project_docs/features/` 下 5 个历史 feature 包迁入 `.aip/features/` 保留开发史；删除遗留 `project_docs/`（仅含 7 行 README、冻结旧指针、92 行陈旧协议副本，无实质活文档）；填 `.aip/config.yaml`（真源=协议文档、唯一机器检查=unittest、process_skills=superpowers）。当前不建新工作包，`current_task.feature_id` 留空（check 跳过活动包校验，可当纯提交检查）。
- 理由：保留历史优于清空（4 月 bootstrap 的 spec/plan 是真实开发记录）；删 `project_docs/` 而非加入扫描豁免，是因为豁免等于承认协议外并行状态长期存在，治标不治本。代价：`.aip/features/` 多 5 个已完成的休眠旧包（不被 check 校验，无害）。
- 影响：删除 `project_docs/`（顶层布局变化，README 已与 `.aip/` 描述一致）；`docs/superpowers/` 仍是 superpowers 方法层产物，按协议属 spec/plan 槽的方法侧，后续新特性应落 `.aip/features/<id>/`。
  （注：本条末句的「后续落 `.aip/features/<id>/`」前瞻指引已被 ADR-2 取代——新模型无 per-feature 工作包。）

## ADR-2：协议文档从 per-feature/bug 轨道模型迁到扁平活文档模型
- 日期 / 状态：2026-06-26 / 采纳（取代 ADR-1 的前瞻部分）
- 背景：引擎代码（`_aip_common` 的 `PROJECT_LIVING_FILES`/`FORBIDDEN_SLOT_FILENAMES`、`aip_init`、`aip_check`）早已落到「8 个活文档 + `OVERVIEW.md` 看板管任务线」的扁平模型，但 `docs/protocol.md`、`docs/architecture|adaptation|examples.md`、`root-cause` 技能、`.aip/README.md` 仍描述旧模型（`STATUS.md`/`canonical-assets.md`/`findings.md`、per-feature 工作包、`_runtime/current_task.json`、`task_board`/`handoff`/`verification`、bug 轨道/`report.md`）。文档与代码对不上，会误导接手者。
- 决策：把上述文档全部改写到现行模型；旧槽位名作为迁移守卫列入「不得再出现」（已在 `_aip_common.FORBIDDEN_SLOT_FILENAMES`）。角色搬迁：现状真理源 `STATUS.md`→`OVERVIEW.md`，侧发现 `findings.md`→`inbox.md`，复用登记 `canonical-assets.md`→`reference.md`。删掉已不存在的 `schemas/*.json` 相关描述。
- 理由：代码是事实源，文档必须跟齐；保留旧描述等于把废弃模型当权威，正是 AIP 要防的漂移。
- 影响：`docs/protocol.md` 重写；`docs/architecture|adaptation|examples.md`、`root-cause` 技能、`.aip/README.md` 改写；`.aip/config.yaml` 的 `STATUS.md` 铁律改为 `OVERVIEW.md`；插件副本经 `sync_plugin.py` 再生。锚点沿用英文（ADR/K/I），仅在各活文档首次出现处加中英对照说明。
