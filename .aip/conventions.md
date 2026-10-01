# 项目规约 · 活文档

> 这工程「怎么干」的常驻规则。从空白靠捕获长大——被纠正一次就记一条。机器能强制的（linter/formatter/CI）指向它，文档只记需人/AI 判断的。

## 铁律（违反就出事的硬约束）
- 未授权不提交：git add/commit/push 需用户明确指示。
- 新建文件 UTF-8 无 BOM；编辑既有文件保持原编码不变。
- 引擎只有一份：`plugins/ai-implementation-protocol/skills/aip/` 下的 `scripts/` 与 `templates/`；改动落这里，不改别处的安装副本（关联: 20260914-224845_改引擎要改仓库里的技能目录不是已安装的副本）。本仓库自己的 `.claude/skills/aip`、`.codex/skills/aip` 是项目级安装的拷贝（不用链接，Windows 上 git 链接要额外设置）：改完源要重跑 `scripts/install_all.py --project .`，`aip_check` 发现两边不一致会报红。
- 协议是真源：行为/规则变更同次更新 `docs/protocol.md`、`docs/architecture.md`、`README.md` 与技能正文（`SKILL.md` / `reference/`）。
- 版本只有一处：`skills/aip/VERSION`；改版本同次改三份 `plugin.json`（`.claude-plugin` / `.codex-plugin` / `.grok-plugin`）的 version。
- 改了既有仓库要跟着调整的模板或规矩（删字段、搬内容、删旧文件），同次在技能的 `reference/upgrade.md` 加一节新版本，写清怎么调整。
- 重新执行 aip init 必须升级 `AGENTS.md`/`CLAUDE.md` 中带 AIP managed 标记的规则块；不得覆盖已有活文档或项目自有内容。
## 代码风格
- <暂无>
## 注释风格
- <暂无>
## 设计风格
- 凡是后缀为 `.md` 的生成/派生件，输出必须是合法 Markdown（GFM）：用真表格（带 `|---|` 分隔行、行首尾带 `|`）而非裸竖线行；不用 `#` 当行注释（Markdown 里 `#` 是标题），要注释用 `<!-- -->`。新增任何 `.md` 生成器都照此办，并加测试守住格式。
## 构建 / 调试 / 验收固定流程
- 构建：无独立构建步骤 ｜ 测试：`python3 -m unittest discover -s tests -p "test_*.py"` ｜ 硬闸门：`python3 plugins/ai-implementation-protocol/skills/aip/scripts/aip_check.py --repo-root .`（需 Python 3.9+：先用 python3，没有再用 python 并确认版本，是 2 就别跑） ｜ 验收通用标准：编码任务必须完成适用约束的对照和验证闭环；每条 plan/需求必须有实现位置和行为证据；不能完整闭环时至少执行相关 lint/build，并明确说明未验证项和风险；不得通过删除、跳过或削弱测试绕过约束。
