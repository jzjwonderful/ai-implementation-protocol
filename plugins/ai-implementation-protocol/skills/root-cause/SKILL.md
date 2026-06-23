---
name: root-cause
description: Use when facing any bug, error, crash, unexpected behavior, "why does this happen", or a debugging/investigation request — before proposing any fix. Drives root-cause investigation (recall known causes, falsify, dig past the symptom) and deposits verified causes into the AIP knowledge base.
---

# 根因导向调查

遇到问题**先别打补丁**。表面修复只搬走症状，真正的价值在挖到能在代码/配置/环境里指出来的**根因**，再把判断交给用户。

## 核心循环（强制顺序）

0. **先查后挖（recall 优先）**
   - 读 `.aip/knowledge_index.md`，用当前症状/类目命中已知真因。
   - 命中条目是**先验假设，不是结论**：①用当前证据重新确认是否仍成立（看"最后复核"日期，过期项尤其重验）；②照样列出别的竞争假设，主动问"还有没有别的可能"。
   - 旧结论被证伪 → 在 `.aip/knowledge.md` 标 `状态: superseded(by K-00X)` 并写新条目。
   - 原则：**先验加速调查，但不豁免证伪。**
1. **禁止直接给修复** —— 先精确复述可观察症状。
2. **取证复现** —— 命令输出/日志/代码引用，不靠脑补。
3. **列 2–3 个竞争假设** —— 不认定第一个。
4. **证据判别** —— 用最便宜的探针逐层下沉，定位真正断裂那一层。
5. **区分症状 vs 根因** —— 挖到具体可指之物为止。
6. **触类旁通（同类排查）** —— 根因一旦确认，**按其机理把它当成一类缺陷而非一处**：在当前变更范围（`file_scope`）内横扫所有共享该根因的兄弟站点，连同主站点一并修复，别只堵眼前这一个。范围之外的同类登记进 `findings.md`，绝不默默漏过。
   - **边界**：同一根因的兄弟站点属 **in-scope**，不是侧发现——必须扫、必须处理；侧发现协议只收**无关**问题（capture, don't chase）。别拿"别追侧发现"当借口跳过同类排查。
7. **交用户判断** —— 摆出【根因 + 证据 + **同类波及面（已扫范围 + 命中站点）** + 修复选项 + 各自取舍】，由用户决策（接 AIP Stop-and-ask），不擅自实施深层改动。
8. **沉淀** —— 验证过的真因写入 `.aip/knowledge.md`（按顶部 `## 类目` 选分类，填全字段），然后跑 `aip knowledge` 重建索引；属决策的进 `decisions.md`，无关侧发现进 `findings.md`。

> 在 AIP **bug 轨道**（`current_task.kind=bug`）下，调查产物落该 bug 包 `report.md` 的对应节
> （症状/复现、竞争假设、根因、证据、触类旁通·同类波及面、修复选项、选定方案、沉淀），
> 不另起平行位置；`aip check` 会校验这些节非空与回归证据。

## 时刻保持

- **警惕与证伪**：任何假设（含索引命中的旧条目）都要试图推翻，证据不足不下结论。
- **知识库正确可用**：沉淀后立即重建索引；过期/失配条目复核或标 superseded，不留腐烂。

## 输出语言风格（怎么对用户说话）

面向用户的回答与说明（不含代码、命令、文件内容）遵守：

1. **用中文**，专业技术名词可保留英文。
2. **说大白话，不用黑话**；不生造词、不堆抽象比喻。必须用专业术语时第一次出现先一句话解释，不直接甩术语。
3. **专业、客观，以事实和结果为准**；不恭维、不自夸、不填充。结论先行再给依据；不确定就直说。
4. **第一性原理思考**；先拆到最基本的事实和约束再推导，不照搬惯例。

## 与 superpowers 的关系

若仓库 `process_skills: superpowers`，方法深度让位给 `systematic-debugging`；但本 skill 的 AIP 残留物（knowledge 条目 + 交用户判断）仍由它拥有，落 `.aip/` slot，不另起平行位置。无 superpowers 时本 skill 独立完整运行。
