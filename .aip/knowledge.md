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

## K-003: 把 AIP 装成项目级技能：`--home` 指项目根，钩子得另外重指
- 分类: deployment
- 状态: active
- 症状: 想让某个项目自带 aip 技能（不装到 `~/.claude/skills/`），安装器却只有一个 `--home` 参数；另外，0.3.0 之前装过 AIP 的老仓库升级后，新会话不再自动打印 OVERVIEW
- 根因: `install_claude_plugin.py` 落点固定是 `<home>/.claude/skills/<skill>/`，所以 `--home <项目根>` 直接得到项目级 `.claude/skills/aip/`（参数名叫 home 只是历史叫法，不限于家目录）。钩子是另一套：安装器只拷技能、不动钩子，老仓库 `.claude/settings.json` 里 SessionStart 命令还写着 `~/plugins/ai-implementation-protocol/scripts/aip_overview.py`，而 0.3.0 把引擎搬进了技能目录，该路径已不存在——钩子静默失效，没有任何报错
- 证据: `python scripts/install_claude_plugin.py --home /root/code/tech-ai-kits` 落出 `.claude/skills/aip` 与 `.claude/skills/root-cause`；该仓库 settings.json 原命令指向的 `/root/plugins/ai-implementation-protocol/scripts/aip_overview.py` 已不存在（该目录 `scripts/` 已空）；用 `install_hooks.py --repo-root . --engine-root .claude/skills/aip --session-start --force` 重指后，手跑钩子命令能正常打印 OVERVIEW，`aip_check` 通过
- 适用范围: Claude Code 的项目级技能目录 `<repo>/.claude/skills/`；升级到 0.3.0 的任何老仓库都要检查一遍 SessionStart 钩子和 pre-commit 的路径
- 最后复核: 2026-09-20
- 关联: K-002 / ADR-4

## K-004: 引擎搬家后合并旧分支，危险的不是 git 冲突而是没冲突的路径假设
- 分类: build
- 状态: active
- 症状: 把改布局前分叉出去的分支合回来，冲突都解完、`git status` 干净，装出来的东西却是坏的
- 根因: 布局改动（0.3.0 把引擎从 `plugins/.../scripts/` 搬进 `skills/aip/scripts/`）只改了文件位置，改不动另一侧新写的代码里对老位置的假设。git 只比对文本和路径：另一侧新增文件的位置冲突它会报，但「安装器自检 `<pkg>/scripts/aip_init.py`」「只拷 SKILL.md 不拷整个技能目录」「调用方按旧签名传参」这类假设它看不见，合完全绿
- 证据: 本次合并 git 报了 3 个 file-location 冲突（aip_brainstorm/install_all/install_grok_plugin）并自动指向新目录，但同时静默合进了四处坏掉的假设：Grok 安装器 `copy2(SKILL.md)` 导致技能正文里的 `<skill>/scripts/` 落空；grok 与 install_all 的自检仍查 `<pkg>/scripts/aip_init.py`；`install_all` 调 `claude.install_skills(pkg, home, force=True)` 而 0.3.0 的签名是 `(skills_dir, home)`；新增的 `.grok-plugin/plugin.json` 停在 0.2.1 且不在 `ENGINE_MANIFESTS` 里，版本漂移检查查不到它
- 适用范围: 任何「一侧改布局、另一侧加功能」的合并。解完冲突要额外做两件事：全库搜老路径字符串，以及把装/跑的全链路真跑一遍（本次是 install_all → aip_init → aip_check → aip_doctor）
- 最后复核: 2026-09-20
- 关联: K-002 / K-003 / ADR-4
