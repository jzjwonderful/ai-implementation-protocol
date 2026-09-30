---
title: 活文档靠「用到即核 + 到期提醒」保持跟现状一致
status: accepted
aliases: ADR-5
---

- 日期 / 状态（迁移前）: 2026-09-27 / 采纳
- 背景：在一个业务仓库（Gandalf）里盘点发现，活文档写进去之后几乎没人回头核：knowledge 里 7 条最后复核停在三个多月前，其中 5 条的缺陷早已修好却还标 active；reference 摘要因为模板用表格、摘要只数三级标题，永远显示「（空）」；状态字段里混着「fixed（已修…）」「active（代码已修…）」这类自由写法；「距上次 review 超过一个月」这个触发条件没有任何东西去算。项目技能、说明文件也同样漂移。协议只管「写的时候」，没管「用的时候」和「放久了」。
- 决策：(1) SKILL.md 新增「用到即核」：读到的 `.aip/` 条目、规约、项目技能、说明文件和现状对不上，当场改并同次提交；root-cause 命中旧条目重验后更新「最后复核」；完成检查的捕获回扫加一项「用过的文档」。(2) 新增 `aip_upkeep.py`：列出超过 90 天没复核的 active 知识、draft 条目、逾期 30 天的整份 review（`config.yaml` 的 `review_last_full`，新建项目由 init 记为当天）；SessionStart 钩子在新会话 / 恢复会话时打印，压缩后不打印；`aip check` 在结论后打印。只提醒，不挡提交。(3) knowledge 状态定为 active / draft / fixed / superseded 四个词开头，「最后复核」必须是日期，`aip check` 硬查。(4) OVERVIEW 摘要的参照部分改为按二级节数条目（表格行、列表项、三级标题）。(5) doctor 的过期阈值与提醒共用一处，只催 active。(6) 钩子安装器重装时换掉指向旧路径的 AIP SessionStart 条目；引擎装在仓库里时写 `$CLAUDE_PROJECT_DIR` 相对路径；新增 `--no-pre-commit`，项目级安装的提示不再建议会覆盖别人钩子的 `--force`。版本升到 0.3.1。
- 理由：文档腐烂的原因不是没人写，而是没有东西逼人回头核；把「核」挂在「用」和「到期」两个时机上，成本最低。提醒不挡提交，是因为日子到了不是错误，挡住会逼人为了过闸门随手改日期。状态词硬查，是因为提醒靠它判断谁该被催。放弃的：不做自动判定条目是否过时（要读代码，引擎做不到），不把提醒做成阻断。
- 影响：SKILL.md、`reference/closure.md`、`reference/review-checklist.md`、root-cause 技能、knowledge 与 config 模板、`aip_check` / `aip_session_start` / `aip_init` / `aip_overview` / `aip_doctor`、新增 `aip_upkeep.py` 与 `tests/test_upkeep.py`、`docs/protocol.md`、README。老项目升级后在 `config.yaml` 补 `review_last_full`，并把状态写法不合规的 knowledge 条目改正，否则 `aip check` 会红。
