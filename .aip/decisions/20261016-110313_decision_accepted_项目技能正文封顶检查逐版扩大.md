---
title: 项目自己的技能正文也封顶，体积和引用检查按 aip_version 逐版扩大
status: accepted
related: 20261016-102351_会膨胀的文件按主题拆分
---

- 背景: tech-ai-kits、docflow-agent 两个仓库按 0.8.0 整理后反馈：项目技能 kit-dev 的正文有 1.35 万字，每次调用都整篇进上下文，0.8.0 只查引擎自己的 SKILL.md；引用检查漏了 `specs/`、项目技能、`docs/`，拆分后的旧引用要人手 grep；「本文「某节」」这类文件内指针拆分后失效、查不出；旁路问题记录「哪里还指着旧文件」反被报红；只超 113 字也是红，到提交时才发现要再拆。
- 决策: (1) 0.8.1 起项目自己的技能正文（`.claude/skills/*/SKILL.md`、`.codex/skills/*/SKILL.md`、`.agents/skills/*/SKILL.md`，装进来的 aip 不算）不超过 8000 字。(2) 0.8.1 起引用检查加上 `.aip/` 下条目以外的文档、`size_check_paths` 的文档、项目技能，并查「本文「某节」」；旁路问题不再查。(3) 这两项和 0.8.0 的检查一样按 `aip_version` 生效（`WIDER_CHECK_VERSION`）。(4) 超限报红写明超了多少；到上限九成时进到期提醒，不报红。上限数值单独放 `aip_size.py`，检查和提醒共用。
- 理由: 新检查一上来就对已整理过的仓库报红，会挡住所有提交，所以每扩大一次检查范围，就跟一个版本号、在 upgrade.md 写一节，各仓库整理完再改版本号。项目技能用和引擎技能同一个上限：都是调用时整篇读。旁路问题本来就是在记「哪里还指着旧东西」，查它只能逼人改措辞绕开。
- 影响: 新增 `aip_size.py`（从 `aip_check.py` 挪出体积部分）；改 `aip_check.py`、`aip_upkeep.py`、`_aip_common.py`；`reference/upgrade.md` 加 0.8.1 一节。
