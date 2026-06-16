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
6. **交用户判断** —— 摆出【根因 + 证据 + 修复选项 + 各自取舍】，由用户决策（接 AIP Stop-and-ask），不擅自实施深层改动。
7. **沉淀** —— 验证过的真因写入 `.aip/knowledge.md`（按顶部 `## 类目` 选分类，填全字段），然后跑 `aip knowledge` 重建索引；属决策的进 `decisions.md`，无关侧发现进 `findings.md`。

## 时刻保持

- **警惕与证伪**：任何假设（含索引命中的旧条目）都要试图推翻，证据不足不下结论。
- **知识库正确可用**：沉淀后立即重建索引；过期/失配条目复核或标 superseded，不留腐烂。

## 与 superpowers 的关系

若仓库 `process_skills: superpowers`，方法深度让位给 `systematic-debugging`；但本 skill 的 AIP 残留物（knowledge 条目 + 交用户判断）仍由它拥有，落 `.aip/` slot，不另起平行位置。无 superpowers 时本 skill 独立完整运行。
