---
title: 把 AIP 装成项目级技能：用 `--project`，钩子得另外重指
status: active
category: deployment
scope: 项目级技能目录 `<repo>/.claude/skills/`（Codex 是 `<repo>/.codex/skills/`，Grok 没有这个约定）；升级到 0.3.0 的任何老仓库都要检查一遍 SessionStart 钩子和 pre-commit 的路径
last_reviewed: 2026-10-01
aliases: K-003
---

- 症状: 想让某个项目自带 aip 技能（不装到 `~/.claude/skills/`）；另外，0.3.0 之前装过 AIP 的老仓库升级后，新会话不再自动打印看板
- 根因: 装到哪只取决于落点根目录（`<根>/.claude/skills/<skill>/`）。安装器现在有正式的 `--project <仓库>`（Claude 与 Codex 都支持，install_all 也支持），会把后续步骤一并印出来；在它之前只能借 `--home <项目根>` 凑，效果相同。钩子是另一套：安装器只拷技能、不动钩子，老仓库 `.claude/settings.json` 里 SessionStart 命令还写着 `~/plugins/ai-implementation-protocol/scripts/aip_overview.py`，而 0.3.0 把引擎搬进了技能目录，该路径已不存在——钩子静默失效，没有任何报错
- 证据: `python scripts/install_claude_plugin.py --project <仓库>` 把三个技能整目录落进 `<仓库>/.claude/skills/`（首次是用 `--home` 装的 tech-ai-kits，效果相同）；该仓库 settings.json 原命令指向的 `/root/plugins/ai-implementation-protocol/scripts/aip_overview.py` 已不存在（该目录 `scripts/` 已空）；用 `install_hooks.py --repo-root . --engine-root .claude/skills/aip --session-start --force` 重指后，手跑钩子命令能正常打印看板，`aip_check` 通过
- 现状: 重装钩子会自动换掉指向旧路径的 AIP SessionStart 条目；引擎在仓库里时写成 `$CLAUDE_PROJECT_DIR` 相对路径，settings.json 进版本库也能换机器用；0.7.0 起钩子命令先找 `python3`、再找 `python`，只用 3.9 以上的。仓库已有非 AIP 的提交前钩子（如 pre-commit 框架）时用 `--no-pre-commit`，千万别用 `--force`，它会覆盖掉那个钩子
- 关联: 20260914-224845_改引擎要改仓库里的技能目录不是已安装的副本 / 20260914-224845_引擎并入技能目录单副本分发
