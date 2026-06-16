# AIP 上手体验 v2（对话式 / 自引导 / 双端平价）设计 spec

日期：2026-06-16
状态：approved（待实现）

## 目标（Goal）

把 AIP 从"懂协议的人手敲带参命令"改造成**对话式、自引导、对后续 AI 自我暴露**的上手体验，并补齐一批协议完整性/健壮性缺口。全部改动在 **Claude Code 与 Codex 双端**都生效或优雅降级。

## 范围（Scope）

保持**全局安装**（仓库级 vendor 本轮不做）。包含：

- M1 命令可见性层（commands 层，不拆 skill）+ 补路由 `$aip knowledge`/`$aip done` + resume 友好化
- M2 引导式 init（AI 主导访谈填 `config.yaml`）
- M3 对话式 start（头脑风暴→任务，自动生成 id/title/spec 初稿）
- M4 superpowers 兼容 + AIP 原生回退（贯穿 M2/M3）
- M5 发现机制：init 向 `CLAUDE.md` 与 `AGENTS.md` 写托管引导块
- M6 完整性：`aip check` 真正读取 `config.yaml` gates 并交叉核对 verification
- M7 健壮性修复：must_read 回归、competing_artifacts 误报、schemas 处置

**不在范围**：仓库级 vendor 安装；语义检索；改既有 feature 工作包结构。

## 设计原则

- **DRY**：所有命令最终调用单一 `aip.py`；commands/ 与 skill 都是薄路由，不复制逻辑。
- **双端平价**：Claude 专属能力（commands 命名空间、CLAUDE.md、superpowers）都要有 Codex 等价物（skill 描述/`$aip help`、AGENTS.md、AIP 原生回退）。
- **standalone 铁律**：无 superpowers 时 AIP 必须完整可用。

---

## M1 · 命令可见性层 + 路由补全

**形态（已定）**：保留单一 `aip` 路由 skill 作跨工具内核；Claude 侧新增 `commands/` 薄命令层给出 `/aip:*` 列表可见性，每个 `.md` 带 `description`，体内只调用 `aip.py <cmd>`。

**新增 commands（plugin `commands/`）**：`init / start / resume / check / knowledge / done`，各带一句 description（用户在 `/aip:` 补全里看到用途）。

**命名空间注记**：当前插件名 `ai-implementation-protocol` → 命令会呈现为 `/ai-implementation-protocol:init`。是否为 `/aip:` 短命名空间而把插件改名 `aip`（牵动安装器/marketplace/目录），作为实现期一个待决细节；默认**不改名**，先接受长命名空间，后续可单独处理。

**补全 skill 路由（修复 A）**：`aip` SKILL.md 的 Supported forms / Routing Rules / 示例补 `$aip knowledge`（重建索引）与 `$aip done`（见下）。

**新增 `$aip done`（修复 E）**：新增 `aip_done.py`：把 `current_task.json.status` 置 `done`、`last_updated` 刷新，然后调用 `aip_check`；check 不过则回滚 status 并打印失败项。消灭"手改 JSON 设 done"。`aip.py` 加 `done` 子命令；commands/ 与 skill 路由同步。

**resume 友好化（修复 D）**：`aip_resume.py` 在 `current_task.json` 缺失时不抛 traceback，改为打印"AIP 未初始化，请先 `$aip init`"并返回非零。

**Codex 平价**：commands 是 Claude 特性；Codex 侧靠 `$aip help` 输出完整命令清单 + 每条 skill description 写全达到等价可见性。`$aip knowledge`/`$aip done` 经由同一 SKILL.md 路由，Codex 自动获得。

---

## M2 · 引导式 init（AI 主导填 config.yaml）

**现状**：`aip init` 生成带注释占位的 `config.yaml`，留给用户手填——关键适配步骤无人引导，常被留空，导致 M6 的证据闸门形同虚设。

**设计**：`aip init` 仍负责**脚手架**（创建文件，确定性、幂等）。填 `config.yaml` 改为 **skill 引导的访谈流程**（写在 `aip` skill 的 init 流程说明里，非脚本）：

init 脚手架完成后，AI 主动逐项访谈并写回 `config.yaml`：
1. **真理源**：扫描仓库（README/docs/约定文件）提出候选，问用户确认 `truth_sources`。
2. **机器闸门**：探测技术栈（package.json/pyproject/*.sln 等）建议 `gates.tests/build/lint_or_drift/e2e` 的真实命令，逐条确认。
3. **lenses**：按改动域建议（前端/客户端…），可选。
4. **iron_rules**：问项目硬约束（编码要求、契约重生成、未授权不提交等）。
5. **process_skills**：检测到 superpowers 则建议设 `superpowers`，否则留空。

每项 **Stop-and-ask**，不替用户臆断。完成后跑一次 `aip check` 自检。

**Codex 平价**：访谈是纯 skill 指令 + `aip.py` 写文件，无 superpowers 依赖，Codex 同样可执行。检测命令用跨平台 Python 探测，不绑 bash。

---

## M3 · 对话式 start（头脑风暴→任务）

**现状**：`$aip start 2026-06-16-x --title "..."` 要用户先自造 id/title 才能谈需求。

**设计**：用户**直接口述需求**即可触发 start 流程（skill 说明里规定）：

1. **方法层对话**：`process_skills: superpowers` 时**让位 superpowers brainstorming**把需求探清并形成设计；否则走 **AIP 原生轻量访谈**（目的/范围/验收/约束几问）。
2. **AI 自动产出**：从对话收敛出 `feature_id = YYYY-MM-DD-<slug>`（日期由系统注入、slug 由标题派生）、`title`、以及 `spec.md` 初稿（Goal/Scope/Acceptance Criteria 用对话内容预填）。
3. **脚手架**：调用 `aip.py start <生成的id> --title <生成的title>` 建工作包，再把 spec 初稿写入 `spec.md`。用户全程不手敲 id/`--title`。

**must_read 修复（修复 B）**：`aip_start_feature.py` 写的 `current_task.must_read` 补 `.aip/knowledge_index.md`（与 init 对齐），保证实现/调试阶段召回钩子不掉线。

**Codex 平价**：无 superpowers 时的 AIP 原生访谈即 Codex 主路径；id/slug 生成是纯 Python，双端一致。`aip.py` 已有 `start` 子命令，复用。

---

## M4 · superpowers 兼容 + AIP 原生回退（贯穿）

- `aip` skill 的阶段→方法映射表保持单一来源；M2/M3 的"方法让位"统一指向该表。
- 每个让位点都要有 **AIP 原生回退**（init 访谈、start 轻量访谈），保证 standalone 与 Codex 路径完整。
- 映射表 debug 行已接 root-cause（上一版完成）。

---

## M5 · 发现机制：CLAUDE.md + AGENTS.md 双写

**设计**：`aip init` 在脚手架阶段向仓库根写**带标记的托管引导块**：

```
<!-- BEGIN AIP (managed) -->
## AI Implementation Protocol
本仓库用 AIP 管理实现工作。后续 AI 会话请先读：
- `.aip/STATUS.md` 现状真理源
- `.aip/_runtime/current_task.json` 当前任务指针 + must_read
- `.aip/knowledge_index.md` 已沉淀真因索引（遇问题先查）
命令：`$aip resume` 续作 / `$aip check` 校验 / 详见 `.aip/protocols/`。
<!-- END AIP (managed) -->
```

- **双写**：`CLAUDE.md`（Claude 自动加载）与 `AGENTS.md`（Codex/通用 agent 读）各写一份相同托管块。
- **幂等安全**：文件不存在则创建；存在则**只替换 BEGIN/END 之间**，绝不动用户其它内容；无标记则在文件末尾追加托管块。
- 编码遵循仓库：新建 UTF-8 无 BOM；改既有文件保持原编码与换行。

**实现**：新增 `aip_discovery.py`（或并入 init）提供 `upsert_managed_block(path, block)`，init 调用两次（CLAUDE.md / AGENTS.md）。

---

## M6 · 完整性：check 真正核对 config.yaml gates（修复 C）

**现状**：`aip_check.py` 全程不打开 `config.yaml`；done 闸门只看 `verification.md` 有 `## Machine Gates` 表、无 `| fail |`、无占位行——声明的 gates 与 verification 表之间**无交叉核对**，gates 留空也能过。

**设计**（残留物校验 + 覆盖核对，不替用户跑命令）：
- `aip check` 读取 `.aip/config.yaml` 的 `gates`，取出**已声明 cmd 的闸门名**集合。
- done 闸门时，校验 `verification.md` 的 Machine Gates 表**逐一覆盖**这些闸门名；缺任一 → 失败（提示"verification 未覆盖 config 声明的 gate: <name>"）。
- 若 `config.yaml` 所有 gate 都为空：打印**告警**"未声明任何机器闸门，证据绑定弱"，不阻断（允许文档型项目，但显式提示）。
- 解析容错：config.yaml 用最小 YAML 读取（标准库无 yaml，用既有解析方式或轻量行解析，仅取 `gates.<name>.cmd` 是否非空）。

**Codex 平价**：纯 Python 校验，双端一致。

---

## M7 · 健壮性修复

- **competing_artifacts 误报（修复 F）**：当前对全仓扫描槽位文件名易误伤正常文件。改为**仅当该文件看起来是 AIP 槽位**才报（例如 `current_task.json` 含 AIP 字段、`handoff.md` 含 AIP 必备小节），或限定扫描可疑位置；降低误报。最小实现：对 `*.md`/`*.yaml` 命中项做一次内容指纹判断，非 AIP 形状则跳过。
- **schemas 处置（修复 G）**：二选一并在 spec 定稿——(a) 在 check 里用标准库做轻量结构校验（不引第三方 jsonschema），或 (b) 在文档明确 schemas 仅为参考、check 不依赖。**默认取 (b)**：标注为参考，避免引依赖；后续需要再升级。

---

## 错误处理 / 边界

- init 重复运行：脚手架幂等；CLAUDE.md/AGENTS.md 托管块幂等替换；config 访谈对已填项询问是否覆盖。
- 无 superpowers：M2/M3 走 AIP 原生回退，全流程不缺角。
- `$aip done` 在 check 失败时回滚 status，不留半收尾状态。
- config.yaml 缺失或畸形：check 打印告警而非崩溃。
- 托管块写入不破坏用户既有 CLAUDE.md/AGENTS.md 内容（仅标记区内替换）。

## 验收标准（Acceptance Criteria）

1. Claude `/aip:` 补全列出 init/start/resume/check/knowledge/done，各有 description；`$aip knowledge` 与 `$aip done` 经 skill 路由可用（修复 A）。
2. `$aip done` 置 done→跑 check；不过则回滚 status 并报失败项。
3. `$aip resume` 未初始化时打印友好提示而非 traceback（修复 D）。
4. `aip init` 后由 AI 引导访谈，写回非空的 `config.yaml`（truth_sources/gates/iron_rules 至少被逐项问询）；无 superpowers 也能走完（M2/M4）。
5. 用户仅口述需求即可 start：AI 生成 `YYYY-MM-DD-slug` id + title + spec 初稿并建工作包，用户不手敲 id/`--title`；`start` 写的 must_read 含 `knowledge_index.md`（M3 + 修复 B）。
6. `aip init` 在 `CLAUDE.md` 与 `AGENTS.md` 各写入幂等的 BEGIN/END 托管引导块，重跑不重复、不破坏用户内容（M5）。
7. `aip check` 读取 `config.yaml` gates：done 时 verification 未覆盖已声明 gate → 失败；全空 gates → 告警不阻断（修复 C）。
8. competing_artifacts 对非 AIP 形状的同名文件不再误报（修复 F）。
9. 上述全部在 plugin 副本存在等价实现，`sync_plugin.py` 跑通；安装器把全部 skill+commands 装到 Claude(`~/.claude`) 与 Codex(`~/.agents`)。
10. AIP 在无 superpowers、无 Codex 专属设施时仍能 init/start/resume/check/done 全流程跑通（standalone）。

## 待实现期决定的细节

- 是否为 `/aip:` 短命名空间改插件名（默认不改）。
- config.yaml 的 YAML 解析方式（标准库轻量解析 vs 既有方式）。
- M7 schemas 取 (b) 标注参考（默认）。
