---
description: 开始一个 bug 修复工作单元（轻量 bug 轨道：建包 → root-cause 调查 → fix → verify → done）
---
不要让用户手敲 bug-id/--title。与用户确认 bug 的一句话描述，派生 `bug_id = <今天日期>-<描述派生的 kebab slug>`，再调用：

`python <plugin-root>/scripts/aip.py bug <bug-id> --title "<title>" --repo-root .`

建包后**立即挂起 `root-cause` skill** 驱动调查；产物逐节落 `features/<bug-id>/report.md`。

## 参数

- `<bug-id>`（必填）：格式 `YYYY-MM-DD-short-slug`，由对话自动生成，不要求用户手填。
- `--title "..."`（可选）：人类可读标题，从对话描述派生。

## 建包内容

`$aip bug` 在 `.aip/features/<bug-id>/` 下创建：

- `report.md` — 主调查文档（症状/复现 → 竞争假设 → 根因 → 证据 → 触类旁通·同类波及面 → 修复选项 → 选定方案 → 沉淀）
- `file_scope.yaml` — 变更范围声明（用于同类兄弟站点扫描）
- `verification.md` — 验证文档，含 `## Regression`（修前 fail / 修后 pass）、`## Machine Gates`、`## Independent Review`
- `handoff.md` — 接力文档
- `session_log.md` — 会话追加日志
- `decisions.md` — 决策记录

**不**创建 `spec.md` / `plan.md` / `task_board.yaml`（bug 轨道轻量包）。

`current_task.json` 字段：`kind=bug`，`current_phase=investigate`，`resolution=null`。

## 连贯流程

1. **investigate**（root-cause skill 驱动）：先查 knowledge_index → 复现取证 → 竞争假设 →
   逐层证伪 → 区分症状 vs 根因 → 触类旁通同类排查。产物逐节落 `report.md`。
2. **Stop-and-ask**：根因确认后摆【根因 + 证据 + 同类波及面 + 修复选项】交用户拍板，写 `## 选定方案`。
3. **fix**（`current_phase=fix`）：修主站点 + `file_scope` 内同类兄弟站点（同一变更）。
4. **verify**（`current_phase=verify`）：先写 `## Regression`（修前 fail / 修后 pass），
   跑机器闸门，记 fresh-eyes review；真因沉淀进 `knowledge.md`（填 `## 沉淀`：K-NNN 或 N/A+理由）→ `$aip knowledge`。
5. `$aip check` → `$aip done --resolution fixed|wont_fix|by_design`（resolution **必填**）。

## 与 root-cause 的关系

bug 轨道 investigate 阶段**强绑定 `root-cause` skill**。root-cause 的所有调查产物（症状/复现、
竞争假设、根因、证据、触类旁通·同类波及面、修复选项、选定方案、沉淀）落 `report.md` 对应节，
不另起平行位置。

## done 收尾

`$aip done` 收尾 bug 必须带 `--resolution`：

```bash
python <plugin-root>/scripts/aip.py done --resolution fixed --repo-root .
# 或 --resolution wont_fix | by_design
```

`resolution=fixed` 时 `aip check` 要求 `verification.md ## Regression` 节存在且含 `after=pass` 行。
`wont_fix` / `by_design` 无回归门槛，但仍需 `## 根因` 非空。
