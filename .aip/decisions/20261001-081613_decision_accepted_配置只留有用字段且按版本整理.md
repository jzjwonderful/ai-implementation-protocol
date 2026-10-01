---
title: config.yaml 只留用得上的字段，铁律进 conventions；升级靠 aip_version 加 upgrade.md 指导整理
status: accepted
---

- 背景: `config.yaml` 模板里真理源、反堆积、专家视角、索引工具、铁律、验证规范、方法层这些字段，没有脚本读，SKILL.md 也没让 AI 读；本仓库 9 条铁律写了等于没写，注释里还有三处说的不是事实。升级 AIP 后，已有仓库的 `.aip/` 不会自己跟着新模板变，用户级安装一次升级影响本机所有仓库。
- 决策: (1) `config.yaml` 只留 `gates`、`review_last_full`、`aip_version`、`aip_remote`、`aip_remote_branch`；铁律进 `conventions.md` 开头的「铁律」一节，说明文件托管块要求动手前读 conventions。(2) 每个仓库在 `aip_version` 记着按哪一版模板整理过；技能的 `reference/upgrade.md` 按版本号分节写怎么调整；会话开始发现有更新版本的节没做就提醒，AI 跟用户说过后照做，做完改 `aip_version`。只改脚本、不用动仓库的版本不加节。
- 理由: 写进文件却没人读的配置比没写更糟，会让人以为有约束。提醒挂在会话开始而不是升级那一刻：执行 `/aip update` 的是旧版脚本，而且用户级升级后各仓库要在自己的会话里各整理一次。
- 影响: 模板 `config-template.yaml`、`conventions-template.md`，`aip_upkeep.py`（升级整理提醒）、`aip_init.py`（新仓库写当前版本），新增 `reference/upgrade.md`。
