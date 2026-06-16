# 根因导向调查 + 知识沉淀机制 设计（spec）

日期：2026-06-16
状态：approved（待实现）

## 目标（Goal）

让任何使用 AIP 的仓库在解决问题时**不停留在问题表面**，而是主动挖掘真正的根因再交用户判断；并把验证过的真因**随时沉淀**为可复用、可复核、不腐烂的知识，下次自动被调用。

最大化发挥 AI 的专业性：遇到问题不打补丁，先 recall 已知真因、再 investigate 未知根因、全程保持证伪、最后由用户决策。

## 范围（Scope）

新增两件可移植、随 AIP 分发到任意仓库的东西，并接入现有 `aip init` / `aip check` / 插件分发链路：

1. **根因调查 skill**（方法层，AI 可主动加载）
2. **知识库 `.aip/knowledge.md` + 索引 `.aip/knowledge_index.md`**（产物层，append-only + 防腐 + 主动调用）

设计沿用 AIP 既有哲学：**方法用 skill、产物落 `.aip/` slot、`aip check` 校验产物残留物**。AIP 原生、可独立运行（无 superpowers / 无 Codex 也能用）。

**不在范围**：不改既有 spec/plan/handoff 流程；不引入外部服务；不做语义检索（索引为关键词+类目级，够用即可）。

## 模块 A：根因调查 skill（`skills/root-cause/SKILL.md`）

**触发**：description 写成在 bug / 报错 / "为什么会这样" / 意外行为 / 排查类任务时自动加载；与现有 **Stop-and-ask** 衔接。

**核心循环（强制顺序，反"打补丁"）**：

0. **先查后挖（recall 优先）**：拿当前症状/类目命中 `.aip/knowledge_index.md`。
   - 命中条目当作**先验假设，不是结论**：①用当前证据重新确认是否仍成立（结合"最后复核"日期，过期项尤其重验）；②照样列出其它竞争假设，主动问"还有没有别的可能"。
   - 只有证据把旧条目重新坐实才采用；若旧结论已不成立 → 标 `superseded` 并写新条目。
   - 原则一句话：**"先验加速调查，但不豁免证伪。"**
1. **禁止直接给修复**——先精确复述可观察症状。
2. **取证复现**——拿真实证据（命令输出 / 日志 / 代码引用），不靠脑补。
3. **列 2–3 个竞争假设**——不认定第一个。
4. **证据判别**——用最便宜的探针逐层下沉，定位真正断裂的那一层。
5. **区分症状 vs 根因**——挖到"能在代码/配置/环境里指出来的具体东西"为止。
6. **交用户判断**——摆出【根因 + 证据 + 修复选项 + 各自取舍】，由用户决策（接 Stop-and-ask），不擅自实施深层改动。
7. **沉淀**——验证过的真因写入 `knowledge.md` 并重建索引；属决策的进 `decisions.md`；属无关侧发现的进 `findings.md`。

**与 superpowers 的关系**：AIP 原生、可独立运行；当 superpowers 存在时，方法深度让位给 `systematic-debugging`，但 AIP 残留物（knowledge 条目 + 交用户判断）由本 skill 拥有。在 `aip` skill 的 process-skill 映射表 `debug` 行补一条 AIP-native fallback 说明。

## 模块 B：知识库 `.aip/knowledge.md`

**顶部 `## 类目` 区**（taxonomy 与数据同文件，随时可演进）。初始类目集：
`process-lifecycle / concurrency / build / config / ui / data / deployment / domain / other`

**条目结构（ADR 式、append-only、带分类与防腐字段）**：

```markdown
## K-001: 标题（一句话）
- 分类: process-lifecycle
- 状态: active            # active | superseded(by K-00X)
- 症状: <可观察表象>
- 根因: <已验证的真正原因>
- 证据: <命令输出 / 代码引用 / 复现步骤>
- 适用范围: <在什么条件下成立>
- 最后复核: 2026-06-16
- 关联: ADR-3 / findings#2 / feature-id
```

**防腐机制（绑特性收尾 + 轻量检查）**：

- append-only，过时不删：旧结论标 `superseded(by K-00X)`，保留可追溯。
- **完整性硬闸门**：`aip check` 在 `status==done` 完成闸门时，硬校验知识条目字段完整（分类非空且 ∈ `## 类目` 声明集、有状态、有"最后复核"日期），缺则不让过。
- **过期软告警**：`active` 且"最后复核"超过 **180 天**的条目，`aip check` 打印告警但**不阻断**。

## 模块 D：索引 + 主动调用（recall 侧）

- `.aip/knowledge.md`：全量条目，真理源，append-only。
- `.aip/knowledge_index.md`：**自动生成**的一行一条目录，轻量便宜加载：
  ```
  K-001 | process-lifecycle | active | 状态判定误用进程名匹配→杀进程后仍 running | 2026-06-16
  ```
- **单一来源、零漂移**：索引由 `knowledge.md` 条目头派生生成，不手写。
- 新增命令 `aip.py knowledge`（重建索引），幂等、随时可跑。
- `aip check` 校验索引与条目一致；不一致**失败并提示重建**（check 保持只读，沿用"查询前先刷新手工索引"纪律）。

**引导 AI 主动探查的两个挂钩**：

1. **被动加载**：`knowledge_index.md` 进 `current_task.json` 的 `must_read`——每次 resume/新会话都读到目录，AI 天然知道已沉淀哪些真因。
2. **主动前置**：模块 A 第 0 步"先查后挖"。

## 模块 C：接线与可移植

- `_aip_common.py`：`PROJECT_LIVING_FILES` 增 `knowledge.md`、`knowledge_index.md`。
- `aip_init.py`：`LIVING_TEMPLATE_MAP` 增映射；`must_read` 默认增 `knowledge_index.md`；README 文案补行。
- 新增模板 `templates/knowledge-template.md`、`templates/knowledge-index-template.md`。
- `aip_check.py`：新增知识库校验（完整性硬闸门 + 过期软告警 + 索引一致性）。
- `aip.py`：新增 `knowledge` 子命令 → 调用索引重建。
- 顶层 `docs/protocol.md`：安全机制清单加第 9 条"根因优先调查 + 知识沉淀"。
- **同步到 plugin 副本**（`plugins/ai-implementation-protocol/...`）并跑 `sync_plugin.py`——这是"其他仓库使用这套机制"的分发路径。

## 数据流（闭环）

> 遇到问题 → 查索引 recall → 命中也证伪、未中则挖根因 → 全程列竞争假设、保持警惕 → 真因交用户判断 decide → 沉淀 knowledge + 重建索引 deposit → 下次自动 recall

## 错误处理 / 边界

- `knowledge.md` 不存在或为空：check 跳过条目校验（仅校验存在性，与现有 living docs 一致）。
- 索引重建对空知识库产生空索引（仅表头），不报错。
- 类目改名导致旧条目失配：check flag 出来，人工修；不自动改写历史条目。
- 过期告警不影响 exit code，避免每次提交被旧知识卡住。
- 无 active feature 时，完整性硬闸门不触发（沿用现有 check 行为）。

## 验收标准（Acceptance Criteria）

1. `aip init` 后 `.aip/` 出现 `knowledge.md`（含 `## 类目`）与 `knowledge_index.md`，且 `current_task.json.must_read` 含 `knowledge_index.md`。
2. `skills/root-cause/SKILL.md` 存在，description 能在问题类任务触发，循环含"先查后挖 + 命中证伪 + 交用户判断 + 沉淀"。
3. `aip.py knowledge` 能由 `knowledge.md` 条目幂等重建 `knowledge_index.md`。
4. `aip check`：知识条目缺字段/非法类目 → done 闸门失败；索引与条目不一致 → 失败并提示重建；过期条目 → 打印告警但 exit 0。
5. 上述全部在 plugin 副本中存在等价实现，`sync_plugin.py` 跑通无漂移。
6. 顶层 `docs/protocol.md` 含第 9 条机制；`aip` skill 映射表 `debug` 行含 AIP-native fallback。
7. AIP 在无 superpowers / 无知识条目时仍可正常 init/check（不破坏既有行为）。

## 锁定默认值

- 过期阈值 180 天（软告警）
- skill 命名 `root-cause`
- 初始类目集见模块 B（顶部 `## 类目` 区，随时可改）
