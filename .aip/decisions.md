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

## ADR-3：捕获纪律从「draft 等人确认」改为「自主修改 + 事后审计」
- 日期 / 状态：2026-07-07 / 采纳
- 背景：issue #4 讨论定的共识（仓库主人 + GPT-5.5 + Grok + Claude）：实际使用中人没精力逐条确认 draft，文档维护主力必然是 AI；但完全放开又可能失控、质量滑坡。
- 决策：AI 写活文档前逐条过 review 自检清单，通过后可直接写（含直接标 active），但必须当场知会用户 + 随本次工作同一次 git 提交留痕；推翻决策/规约只许追加取代（注明「取代 ADR-N」），删除/合并只认「已被证明错误」「与另一条重复」两个理由。配套：`aip review` 软质量自检（不卡 CI）、`aip doctor` 安装健康检查、`aip init` 两阶段（脚本建骨架 + AI 只填模板原样/空的文件）。
- 理由：把事前闸门换成事后可审计——git diff 就是审计日志，坏改动可回滚、可抽查，而流程不再阻塞；「充分 review」落成可执行清单而非「质量优先」这类口号，避免不同 AI 各自理解。放弃了「人逐条确认」的强保证，代价是坏改动要靠事后抽查发现。
- 影响：SKILL.md（捕获纪律 / review 清单 / 完成检查 / init 两阶段）与 `docs/protocol.md` 同步改写；knowledge 模板的状态语义更新（active=已按清单核过）；新增 `aip_doctor.py` 与 `VERSION`；`sync_plugin.py --check` 改真实比对且比对逻辑单源化进 `sync_plugin.drift`。
