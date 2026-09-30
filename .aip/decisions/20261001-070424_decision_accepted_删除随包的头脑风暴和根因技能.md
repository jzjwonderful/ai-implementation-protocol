---
title: 不再随 AIP 分发头脑风暴（aip-brainstorm）和根因（root-cause）技能
status: accepted
---

- 背景：插件包原来带三个技能：aip、root-cause（查根因的方法论，最后一步把根因记成知识条目）、aip-brainstorm（多个终端的 AI 通过一份议题文档轮流讨论，靠 `aip_brainstorm.py` 维护文档状态）。后两个实际用得很少，却要跟着三端安装器、更新、卸载、诊断和测试一起维护。
- 决策：删除 root-cause、aip-brainstorm 两个技能，以及只为头脑风暴服务的 `aip_brainstorm.py` 和它的测试、协议文档里的头脑风暴一节；插件包只带 aip 一个技能（`SKILL_NAMES`）。根因技能里「把查清的根因记成知识条目」那一步是记知识的通用做法，挪进 aip 技能正文。已经装在本机或项目里的这两个技能，安装器、`/aip update` 碰到就删，卸载脚本照样删，`aip_doctor` 发现还装着会提醒（名单是 `RETIRED_SKILL_NAMES`）。版本升到 0.6.0。
- 理由：用不上，精简，少维护一块。已装副本要主动清：留着的话头脑风暴技能会去调已经删掉的脚本。放弃的：查根因的方法论（逐层找证据、区分症状和根因、同类排查）不再随 AIP 提供，需要时用别的技能。
- 影响：`_aip_common.py`、三个安装器与 `_install_source.py`、`aip_update.py`、`aip_doctor.py`、`uninstall_aip.py`、aip 技能正文与 `reference/review-checklist.md`、`docs/`、README、插件说明、相关测试；删除 `skills/root-cause/`、`skills/aip-brainstorm/`、`aip_brainstorm.py`、`tests/test_brainstorm.py`。
