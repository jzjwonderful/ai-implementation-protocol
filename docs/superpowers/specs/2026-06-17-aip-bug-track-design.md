# AIP Bug 轨道（分析 + 修复连贯）设计

- 日期：2026-06-17
- 状态：草案（待用户复核 → writing-plans）

## 目标

AIP 当前唯一的工作单元是 **feature**：`$aip start` 永远拉起完整 feature 包
（spec/plan/task_board/file_scope/verification）。Bug 修复与问题分析是**不同形状**的工作，
被硬塞进 feature 生命周期时 spec/plan 过重，且"调查→修复"的连贯性、修复完整性没有专门闸门保障。

本设计新增一条 **bug 轨道**：`$aip bug <bug-id>` 把"根因分析 → 修复 → 回归验证"连贯走完，
复用现有 resume / handoff / verification / knowledge / check 全套机器，仅在槽位形状与完成闸门上
按工作单元类型分叉。配套一个**修复完整性闸门**和 **bug 版文档检查**。

方法层（`root-cause` skill）和知识沉淀（`knowledge.md`）已存在且完整；本设计补的是与之配套的
**轻量工作单元 + 槽位 + 完成闸门**。

## 非目标（YAGNI）

- 不做"纯问题分析、不产代码"的独立轨道。bug 轨道始终以修复为目标；分析后判定"不修"的，
  走 `resolution` 收尾（见边界情况），不另立第二条轨。
- 不引入 bug 优先级/严重度看板、SLA、外部 issue 同步等流程外设施。
- 不重写 resume/check/handoff/knowledge 机器（那是路线 B，已否决）。

## 架构决策（ADR-lite）

**采用路线 A：bug 是一种新的"工作单元类型（kind）"，复用 feature 机器。**

`current_task.json` 新增字段 `kind: "feature" | "bug"`（缺省 `"feature"`，向后兼容）。
resume / handoff / knowledge / 提交闸门全部复用；`aip start_feature` 与 `aip check` 按 `kind` 分叉。

否决路线 B（独立 `.aip/bugs/<id>/` 子系统）：会重复造 resume 指针、check、handoff、knowledge
绑定，两套状态易漂移，违反"复用优先、避免过度设计"。

## 工作单元模型

`.aip/_runtime/current_task.json` 同一时刻仍只指向一个活动工作单元，新增/变更字段：

| 字段 | feature | bug |
|---|---|---|
| `kind` | `"feature"` | `"bug"` |
| `feature_id` | feature id | bug id（同字段复用，避免新指针）|
| `current_phase` | spec/plan/implement/verify | `investigate` / `fix` / `verify` |
| `status` | planned/in_progress/blocked/done | 同左（复用） |
| `resolution`（bug 专用，可空） | — | `fixed` / `wont_fix` / `by_design`（done 时必填） |

`feature_id` 字段名沿用（不改 schema 指针），bug id 仍是 `<日期>-<kebab-slug>` 形式。
bug 包目录仍在 `.aip/features/<id>/`（复用 `feature_dir()`，不新增目录树）。

## Bug 工作包槽位

比 feature 轻：**砍掉 `spec.md` / `plan.md` / `task_board.yaml`**，进度由 `current_task.current_phase`
跟踪（investigate→fix→verify），换入一份 `report.md` 作为核心活文档。

| 槽位 | 作用 | 对比 feature |
|---|---|---|
| `report.md` | 核心活文档：症状/复现 → 竞争假设 → 根因+证据 → 触类旁通同类波及面 → 修复选项 | 取代 spec+plan |
| `file_scope.yaml` | 触类旁通同类排查的范围边界（root-cause skill 依赖） | 保留 |
| `verification.md` | 回归闸门 + 机器闸门 + fresh-eyes review | 保留，done-gate 形状不同 |
| `handoff.md` | resume 源 | 保留 |
| `session_log.md` / `decisions.md` | 同 feature | 保留 |
| ~~spec.md / plan.md / task_board.yaml~~ | — | 不建 |

进度不再用 task_board，因此 bug 轨道**不校验** `≤1 in_progress`（该规则作用于 task_board）；
"单一焦点"由 current_task 单指针 + phase 保证。

### `report.md` 模板（新增 `bug-report-template.md`）

固定标题（被 check 校验存在且非空）：

```markdown
# Bug Report: <title>

## 症状 / 复现
<可观察表象 + 复现步骤/命令；不靠脑补>

## 竞争假设
<2–3 个，不认定第一个>

## 根因
<挖到能在代码/配置/环境里指出来的真正断裂层>

## 证据
<命令输出 / 日志 / 代码引用，逐层证伪后的判别证据>

## 触类旁通 · 同类波及面
<已扫范围(file_scope) + 命中的兄弟站点；范围外同类已登记 findings.md>

## 修复选项
<2–3 个方案 + 各自取舍，交用户判断>

## 选定方案
<用户拍板后填；含为何选它>
```

### `verification.md`（bug 版，新增 `bug-verification-template.md`）

在 feature 版基础上**新增一节 `## Regression`**（回归验证），其余沿用：

```markdown
## Regression
<!-- 能复现该 bug 的测试/探针：修复前失败、修复后通过。给命令 + 前后结果。 -->
| repro | command | before | after | evidence |
|-------|---------|--------|-------|----------|
| <一句话复现项> | <cmd> | fail | pass | <输出摘要 / 测试路径> |
```

`## Machine Gates` / `## Independent Review` / `## Not Run` / `## Known Risks` /
`## Side-Findings This Round` 与 feature 版一致。

## 连贯流程（`aip:bug` 一条龙）

1. `$aip bug <bug-id> [--title "..."]`（或口述 bug，由 skill 收敛出 id/title）：
   - 调 `aip.py bug` 子命令 → 建 bug 包槽位 + 写 `current_task.json`（`kind=bug, status=planned,
     current_phase=investigate`），`must_read` 含 `knowledge_index.md` + 本包 `report.md` / `handoff.md`。
   - **自动挂起 `root-cause` skill** 驱动调查；其产物落进 `report.md`（先查后挖 → 复现取证 →
     竞争假设 → 逐层证伪 → 症状 vs 根因 → 触类旁通）。
2. 根因确认 → root-cause 自带的 Stop-and-ask：摆【根因 + 证据 + 同类波及面 + 修复选项】交用户拍板，
   写入 `report.md` 的"选定方案"。
3. 用户选定 → `current_phase=fix`：按根因修主站点 + `file_scope` 内同类兄弟站点（同一变更内）。
4. `current_phase=verify`：填 `verification.md`（先写回归项，跑机器闸门，记 fresh-eyes review）；
   把验证过的真因沉淀进 `knowledge.md`（root-cause skill 第 8 步）→ `aip knowledge` 重建索引。
5. `$aip check`（bug 版）→ `$aip done`（done 前设 `resolution`）。

## 修复完整性闸门（`aip check` 按 `kind=bug` 分叉）

`status==done` 且 `kind==bug` 时强制校验（这是"确保修复完整"的核心机制）：

1. `report.md` 的 **`## 根因`** 与 **`## 证据`** 节正文非空 —— 防止只贴症状就改（表面补丁）。
2. `report.md` 的 **`## 触类旁通 · 同类波及面`** 节正文非空 —— 触类旁通真扫过（呼应 Safeguard #9）。
3. `resolution==fixed` 时：`verification.md` 必须有 **`## Regression`** 节，且其表格无未填占位
   （`| <` 行），无 `before` 为空 —— 即存在"修复前失败、修复后通过"的回归证据。
4. 真因已沉淀进 `knowledge.md`（本轮 confirmed cause）；若确无可沉淀，`report.md` 须显式写
   `沉淀: N/A — <理由>`，不许默默跳过。
5. 仍叠加现有 done-gate：`## Machine Gates`（无 fail、无占位）+ `## Independent Review`。
6. **不**校验 feature 专属项：spec 的 `## Acceptance Criteria`、plan 的 `## Tasks`、
   task_board 的 `≤1 in_progress`（bug 包无这些槽位）。

`status != done` 时：始终校验项（活文档、findings 分类、无并行产物、知识索引一致性）对两种 kind 一致。

### 边界情况

- 分析判定"非 bug / 不修 / 需上层设计决策"：`resolution: wont_fix | by_design`，
  `report.md` 留下完整分析与理由，`aip done` 放行，**不强制 `## Regression`**（闸门 3 仅在
  `fixed` 时生效），但闸门 1/2（根因+证据+同类面）仍要求 —— 因为"判定不修"也需根因支撑。
- bug id 与既有 feature id 撞名：`aip bug` 复用 `feature_dir`，若目录已存在则报错退出（不覆盖）。

## 对现有代码的具体改动

| 文件 | 改动 |
|---|---|
| `scripts/aip.py` | 新增 `bug` 子命令路由 → 调用 `aip_start_bug.py`；`--help` 增列 |
| `scripts/aip_start_bug.py`（新） | 仿 `aip_start_feature.py`：建 bug 槽位（report/file_scope/verification/handoff/session_log/decisions），写 `current_task.json`（kind=bug, phase=investigate） |
| `scripts/aip_check.py` | 读 `current_task.kind` 分叉：bug 走 §"修复完整性闸门"，feature 维持现状；新增 report.md 标题/正文非空校验、Regression 节校验、resolution 校验 |
| `scripts/_aip_common.py` | 新增 bug 包必需文件常量（`REQUIRED_BUG_FILES`）；`AIP_SLOT_FILENAMES` 纳入 `report.md`（并行产物探测） |
| `scripts/aip_done.py` | done 前若 `kind==bug` 且未设 `resolution` → 提示/要求补 |
| `templates/bug-report-template.md`（新） | 见上 |
| `templates/bug-verification-template.md`（新） | feature 版 + `## Regression` 节 |
| `skills/aip/SKILL.md` | 新增 `$aip bug` 命令、路由规则、连贯流程说明；phase→skill 映射表补 bug 行（investigate→root-cause） |
| `skills/root-cause/SKILL.md` | 补一句：在 bug 轨道下，产物落 `report.md` 对应节（而非游离） |
| `docs/protocol.md` | Safeguard 区或新段落说明 bug 轨道与 feature 轨道并列；工作单元 `kind` 概念 |
| `commands/aip/bug.md`（新，Claude 插件侧） | 命令说明页，与 sync_plugin 对齐 |
| `schemas/current_task.*` | 文档化 `kind` / `resolution` 字段（参考性，非强校验） |

`plugins/ai-implementation-protocol/` 与仓库根的镜像副本需经 `sync_plugin.py` 同步保持一致。

## 向后兼容

- `current_task.json` 无 `kind` 字段 → 视为 `feature`，现有项目零改动。
- `aip check` 对既有 feature 包行为完全不变（分叉仅在 `kind==bug` 时进入新分支）。
- 新增 bug 槽位文件名（`report.md`）纳入并行产物探测，需给定内容指纹以降误报。

## 测试 / 验收

1. `aip bug <id>` 建出且仅建出 bug 槽位（无 spec/plan/task_board），current_task `kind=bug,
   phase=investigate`。
2. bug 包 `status=done, resolution=fixed`，report 缺 `## 根因`正文 → `aip check` 失败。
3. 同上但缺 `## Regression` → `aip check` 失败；补齐 → 通过。
4. `resolution=wont_fix` 且无 Regression → `aip check` 通过（闸门 3 不生效），但缺根因正文仍失败。
5. 既有 feature 包（无 kind 字段）→ `aip check` 行为与改动前逐字节一致（回归）。
6. bug id 撞已有目录 → `aip bug` 报错退出，不覆盖。
7. `sync_plugin.py` 后根目录与 plugins/ 副本一致。

## 未决项

无（边界情况与兼容性已在上文定稿）。
