# 知识库（验证过的根因 / 坎 / 领域事实）

条目编号 `K-NNN`（K = Knowledge，知识库条目；如 K-001、K-002）。只追加，过时条目不删，标 `状态: superseded(by K-00X)`。
改完跑 `aip knowledge` 重建 `knowledge_index.md`。

## 类目
process-lifecycle | concurrency | build | config | ui | data | deployment | domain | other

<!--
新增条目复制下面骨架，ID 递增；标题一句话：
AI 新沉淀一律先写 `状态: draft`，经人确认后改 `active`。

## K-NNN: 标题
- 分类: process-lifecycle
- 状态: active
  # active=已人工确认 | draft=AI 待确认 | superseded(by K-00X)
- 症状: <可观察表象>
- 根因: <已验证的真正原因>
- 证据: <命令输出 / 代码引用 / 复现步骤>
- 适用范围: <在什么条件下成立>
- 最后复核: 2026-06-16
- 关联: ADR-N / K-NNN / feature-id
-->

## K-001: 改完 scripts/ 必须先跑 sync_plugin.py，再跑 install_claude_plugin.py
- 分类: process-lifecycle
- 状态: draft
- 症状: 改了 root `scripts/` 下的文件，执行 `install_claude_plugin.py --force` 后到其他仓库跑 `aip init`，CLAUDE.md 没有更新，仍是旧内容
- 根因: `install_claude_plugin.py` 复制的是 `plugins/ai-implementation-protocol/scripts/`（plugin 副本），不是 root `scripts/`。root `scripts/` 是唯一真源，必须先用 `sync_plugin.py` 把改动同步到 plugin 副本，再安装
- 证据: 改了 `scripts/aip_discovery.py` 后直接跑 install，发现 `plugins/ai-implementation-protocol/scripts/aip_discovery.py` 仍是旧内容；跑 `sync_plugin.py` 后两边一致。二次踩坑：AI 把改动写进了 `~/plugins/`（已安装路径），sync 时反被 repo root 旧内容覆盖，改动消失
- 适用范围: 凡改动 `scripts/`、`docs/`、`templates/`、`schemas/` 任意文件后想让安装生效，均需此顺序；AI 辅助改动时须确认落点是 repo root `scripts/`，不是 `~/plugins/`
- 最后复核: 2026-06-27
- 关联:
