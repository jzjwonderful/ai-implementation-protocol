---
title: 引擎并入 `aip` 技能目录，单副本分发；技能正文拆成核心 + 按需参考
status: accepted
aliases: ADR-4
---

- 日期 / 状态（迁移前）: 2026-09-14 / 采纳（取代 20260708-001549_捕获纪律从draft等人确认改为自主修改事后审计 里"插件副本经 sync_plugin 再生"的分发方式）
- 背景：仓库里 `scripts/`、`templates/`、`docs/`、`VERSION` 各有两份（顶层 + `plugins/` 副本），靠 `sync_plugin.py` 手动同步；20260616-221449_改完scripts要先sync再安装 记的坑就是忘同步。Claude Code 安装器只拷 SKILL.md 一个文件，脚本另放 `~/plugins/`，技能里得专门解释"路径要写全"。同时 Claude Code 技能规范已支持技能目录内带 `scripts/` 和参考文件、按需加载，也有了个人级跨会话记忆、子代理、worktree、上下文压缩等机制，技能正文没覆盖这些。
- 决策：(1) 引擎（8 个 CLI 脚本 + 模板 + VERSION）只保留一份，放在 `plugins/ai-implementation-protocol/skills/aip/` 下；顶层 `scripts/` 只留安装/卸载器；删 `sync_plugin.py`、顶层 `templates/`、插件内 `docs/` 副本和插件内 `VERSION`。两个安装器都整目录拷技能。`aip check` 的双副本比对改为"两份 plugin.json 的 version 与 skills/aip/VERSION 一致"。(2) SKILL.md 只留时机与去向，review 清单、完成检查、init 阶段 B 拆到 `reference/` 按需读；捕获回扫的逐项 yes/no 只对改代码/文档结构的任务做。(3) 技能新增三条规则：AIP 文档与 AI 个人记忆的边界、多代理只有主代理写 `.aip/`、worktree 并行线用 `tracks/<id>.md`。(4) SessionStart 钩子换成 `aip_session_start.py`，识别 `source == compact` 时加一句"以看板为准、没写回的先补"。(5) 命令写法 Claude 用 `/aip`，Codex 用 `$aip`，文档两种都写。版本升到 0.3.0。
- 理由：单副本消灭一整类"忘同步"的坑，也让技能里的路径说明变成一句话。压缩前的钩子输出到不了模型，所以补救只能放压缩后的 SessionStart，这是能做到的最接近"压缩前提醒"的方案。技能正文缩短是为了每次会话的固定开销；强度降一档是因为当前模型跟指令很紧，满篇"禁止跳过"会让小任务也走全套。放弃的：`~/plugins/` 不再是 Claude 的安装位（Codex 仍用）；插件包不再自带协议英文文档（README 指向仓库）。
- 影响：仓库布局（见 README「Repository Layout」）、两个安装器、`aip_check`/`aip_doctor`/`install_hooks`、全部测试的导入路径、`docs/protocol.md` 新增"记忆边界""多代理"两节、`.aip/config.yaml` 铁律与 gates、20260616-221449_改完scripts要先sync再安装 标 superseded。老用户重跑安装器后需在各项目 `/aip init` 一次刷新钩子路径。
