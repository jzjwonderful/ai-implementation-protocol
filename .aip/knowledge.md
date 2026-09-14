# 知识库（验证过的根因 / 坎 / 领域事实）

条目编号 `K-NNN`（K = Knowledge，知识库条目；如 K-001、K-002）。只追加，过时条目不删，标 `状态: superseded(by K-00X)`。
改完跑 `aip knowledge` 重建 `knowledge_index.md`。

## 类目
process-lifecycle | concurrency | build | config | ui | data | deployment | domain | other

<!--
新增条目复制下面骨架，ID 递增；标题一句话：
证据不足先写 `状态: draft`；按 review 自检清单核过可直接写 `active`，但必须当场知会用户。

## K-NNN: 标题
- 分类: process-lifecycle
- 状态: active
  # active=已按自检清单核过 | draft=证据不足待复核 | superseded(by K-00X)
- 症状: <可观察表象>
- 根因: <已验证的真正原因>
- 证据: <命令输出 / 代码引用 / 复现步骤>
- 适用范围: <在什么条件下成立>
- 最后复核: 2026-06-16
- 关联: ADR-N / K-NNN / feature-id
-->

## K-001: 改完 scripts/ 必须先跑 sync_plugin.py，再跑 install_claude_plugin.py
- 分类: process-lifecycle
- 状态: superseded(by K-002)
- 症状: 改了 root `scripts/` 下的文件，执行 `install_claude_plugin.py --force` 后到其他仓库跑 `aip init`，CLAUDE.md 没有更新，仍是旧内容
- 根因: `install_claude_plugin.py` 复制的是 `plugins/ai-implementation-protocol/scripts/`（plugin 副本），不是 root `scripts/`。root `scripts/` 是唯一真源，必须先用 `sync_plugin.py` 把改动同步到 plugin 副本，再安装
- 证据: 改了 `scripts/aip_discovery.py` 后直接跑 install，发现 `plugins/ai-implementation-protocol/scripts/aip_discovery.py` 仍是旧内容；跑 `sync_plugin.py` 后两边一致。二次踩坑：AI 把改动写进了 `~/plugins/`（已安装路径），sync 时反被 repo root 旧内容覆盖，改动消失
- 适用范围: 凡改动 `scripts/`、`docs/`、`templates/`、`schemas/` 任意文件后想让安装生效，均需此顺序；AI 辅助改动时须确认落点是 repo root `scripts/`，不是 `~/plugins/`
- 最后复核: 2026-06-27
- 关联:
- 关联: ADR-4（0.3.0 起引擎只有一份，sync_plugin.py 已删，此坑不再存在）

## K-002: 改引擎要改仓库里的技能目录，不是已安装的副本
- 分类: process-lifecycle
- 状态: active
- 症状: 改了 AIP 脚本/模板/技能正文，重开会话后行为没变；或者改动过一阵子"消失"了
- 根因: 改动写到了安装副本（`~/.claude/skills/aip/`、`~/plugins/ai-implementation-protocol/`、`~/.agents/skills/aip/`）。安装器是"整目录覆盖"，下一次安装会把副本打回仓库内容；而仓库里的源没改，git 里也没有痕迹
- 证据: K-001 记录的第二次踩坑就是这样丢的改动（写进 `~/plugins/` 后被覆盖）。0.3.0 重构后安装器 `install_claude_plugin.py` 对 `~/.claude/skills/<skill>/` 先 rmtree 再 copytree（见 `tests/test_install_claude_plugin.py` 的 stale.txt 用例），任何副本内改动都会被清掉
- 适用范围: 凡改 AIP 引擎本身（`plugins/ai-implementation-protocol/skills/` 下任何文件）。正确落点是仓库源；改完重跑安装器让副本更新
- 最后复核: 2026-09-14
- 关联: K-001 / ADR-4
