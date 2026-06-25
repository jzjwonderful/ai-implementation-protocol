# AI Implementation Protocol

## 目标

AIP 定义了一套最小必要记录规则，让任何 AI 在接手任务时都能准确续作，不丢需求、不夹假设、不降质量。

## 产出位置

所有 AIP 产出落在目标仓库的 `.aip/` 目录下（类似 `.git/`），不散落到项目根目录。

## 六类活文档

项目级活文档（跨任务线、长期存在）全部放在 `.aip/` 下：

- `OVERVIEW.md` — 多线看板（手写顶部）+ 自动摘要。开始或接手任何任务前先读这里。
- `decisions.md` — 架构/方向级决策记录（非任务级细节，append-only）。
- `knowledge.md`（+ `knowledge_index.md`）— 验证过的技术坑和根因。
- `reference.md` — 领域概念/术语口径、核心铁律、可复用实现（裁决）。
- `inbox.md` — 旁路问题收件箱（干 A 时撞见的、与 A 无关的问题）。
- `conventions.md` — 项目规约（怎么干的常驻规则）。

没有 per-feature 工作包目录。任务状态通过 OVERVIEW 看板的活跃线条管理。

## 接管（接手或新会话时）

1. 读 `OVERVIEW.md` 找 `▶[active]` 线，看「下一步」和 `must_read`。
2. 按 `must_read` 列出的文件逐一读完（包括 `decisions.md` 和 `knowledge_index.md`）。
3. 读完再动手，不回放历史流水账。

## 自动捕获 + 完成闸门

### 两路捕获

- **主路**：做任务时撞见的技术坑/根因 → 先用 root-cause 技能确认 → 写入 `knowledge.md`（先写 `状态: draft`，经人确认后改 `active`）。
- **旁路**：干 A 时撞见的、与 A 无关的问题 → 先在 `knowledge.md` + `inbox.md` 检索是否已有 → 整理后投 `inbox.md`（不无脑追加）。

### 写入纪律（所有沉淀通用）

拟草稿 → 读目标文档比对去重（像就合并/加关联，不像才新增）→ 写 `状态: draft` → 向用户吭一声（报：记了什么、参考了哪条、跑了什么闸门）。draft 直到人确认才变 active；AI 从不擅自升 active、不静默改旧内容。只收**已验证**的进 knowledge；琐碎且同文件的顺手修、不登记。

### 完成闸门（一条任务线做完时）

**第一档（每次任务线收尾必跑）：**
1. 跑 `python scripts/aip_check.py --repo-root .`（红了挡住，逐条修）。
2. 范围内纠偏：只整理本次碰过的条目及其直接关联（draft/diff，不静默改其他内容）。
3. 捕获回扫：列本次具体学到/碰到的候选——进 knowledge/inbox/reference/conventions/config？
4. 改完 knowledge 跑 `python scripts/aip_knowledge.py --repo-root .`；刷新总览 `python scripts/aip_overview.py --repo-root .`。
5. 把该线从 OVERVIEW 看板移出。

**第二档（架构/取舍决策时追加）：**
在 `decisions.md` append 一条 ADR-lite 记录（背景、决策、理由、影响），防止后续多轮接手时反复重争同一个问题。

## 外部工具退化链

**能力意图**：查引用、找同义实现、搜索索引时，按以下退化链选工具，用能力匹配的最简工具：
1. 有 LSP → 用 `findReferences`/`incomingCalls`（准）。
2. 无 LSP → 用 grep + 读候选 + 查 `reference.md`（够用）。
3. 大工程 → 用 nexus-query/CodeGraph（若已装）。

**不内置、不探查**：AIP 不记录本机装了哪些外部工具（平台每次会话已给可用清单，用时现场挑，不提前探查）。

**产物与 `.aip/` 解耦**：外部工具的输出（如 nexus 索引、CI 记录）可作为增强输入，但 AIP 本身不依赖它们，协议在没有这些工具时仍完整可用。

## 通用开发纪律

通用开发纪律（禁止说黑话、注释不引外部编号等）的完整清单只在已安装的 `aip` 技能中维护，不在此处复制（防漂移）。规则随 AIP 插件分发自动生效；要增补规则，直接改 `aip` 技能里的「通用开发纪律」节，不改这里。

## `aip check` 职责

`aip check`（即 `python scripts/aip_check.py --repo-root .`）是唯一的机器闸门，检查：

1. **活文档存在**：活文档与配置/派生件（`OVERVIEW.md`、`decisions.md`、`knowledge.md`、`knowledge_index.md`、`reference.md`、`inbox.md`、`conventions.md`、`config.yaml` 共 8 个）都在 `.aip/` 下。
2. **知识索引一致**：`knowledge_index.md` 与 `knowledge.md` 当前内容一致（不一致就跑 `aip_knowledge.py` 重建）。
3. **知识条目字段完整**：`knowledge.md` 每条目的必填字段（分类、状态、症状、根因、适用范围、最后复核）都不为空。
4. **无旧机制残留**：仓库内不出现被禁止的旧文件名（旧 per-feature 接管文件、已被取代的旧文档名）。
5. **双副本同步**：顶层 `scripts/` 和 `templates/` 与 `plugins/ai-implementation-protocol/` 下的对应副本逐字节一致（不一致就跑 `sync_plugin.py` 重建）。

check 退出码 0 = 通过，非 0 = 有违规，违规列表打到标准输出。

## 命令（AI 自主，人只敲 init）

所有日常命令（捕获、闸门、刷新索引、刷新总览）由 AI 按时机自主触发，不需要人手动敲。人只在新仓库装 AIP 时执行一次：

```
python scripts/aip_init.py --repo-root .
```

**可靠性三层：**
- **钩子**：`install_hooks.py` 装 git pre-commit 钩子，提交前自动跑 `aip check`，忘了跑也会被挡住。
- **完成闸门**：任务线收尾前跑 check，逐条修到绿。
- **开场引导**：每次接手时读 OVERVIEW active 线，不用人提示。

具体命令行和阶段→技能映射，以已安装的 `aip` 技能为唯一来源，不在此处重复（防漂移）。

## Schema 仅供参考

`schemas/*.json` 描述 `config.yaml` 等文件的结构，供人和工具参考。`aip check` 不对它们做格式校验（无第三方依赖）。

## 可选知识来源

以下来源若存在，可作为增强输入使用：

- `.nexus-map/`
- git 历史
- CI 记录

它们是可选的。AIP 本身在没有这些工具时仍完整可用。
