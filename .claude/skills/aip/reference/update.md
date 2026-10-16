# `/aip update`：更新已装的 AIP 技能

`<skill>` 指本技能目录（SKILL.md 所在目录）。

- 查有没有新版：`python3 <skill>/scripts/aip_update.py --repo-root .`。
- 更新：加 `--apply`。从远端浅克隆最新版，核对齐全后原地替换本机装的 aip 技能，顺手删掉以前随包分发、0.6.0 起不再提供的 root-cause、aip-brainstorm（项目级安装时 `.claude/skills` 和 `.codex/skills` 两份一起换）；失败会换回原样。不需要本机有 AIP 仓库，也不走安装器。
- 远端地址默认取安装时记下的（技能目录里的 `SOURCE.json`）；项目 `config.yaml` 写了 `aip_remote` / `aip_remote_branch` 就用它们。
- 项目级安装更新完，要把技能目录的变化提交进仓库。

## 升级后整理

新版可能要求调整仓库里已有的 `.aip/`（删字段、搬内容、删旧文件）。每个仓库在 `config.yaml` 的 `aip_version` 记着按哪一版整理过；会话开始发现 `reference/upgrade.md` 里有更新版本的调整没做，就会提醒。看到提醒先跟用户说，同意后按 `reference/upgrade.md` 从 `aip_version` 之后的版本逐节做，做完改 `aip_version`、跑 `aip_check`。用户级安装一次更新影响本机所有仓库，各仓库在自己的会话里各整理一次。
