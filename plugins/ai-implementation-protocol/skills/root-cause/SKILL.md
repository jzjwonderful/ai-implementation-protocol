---
name: root-cause
description: Use when facing any bug, error, crash, unexpected behavior, "why does this happen", or a debugging/investigation request — before proposing any fix. Drives root-cause investigation (recall known causes, falsify, dig past the symptom) and deposits verified causes into the AIP knowledge base.
---

# 根因导向调查

遇到问题**先别打补丁**。表面修复只搬走症状，真正的价值在挖到能在代码/配置/环境里指出来的**根因**，再把判断交给用户。

## 核心循环（强制顺序）

0. **先查后挖（recall 优先）**
   - 在 `.aip/knowledge/` 按文件名里的简述找，或跑 `python <aip 技能目录>/scripts/aip_item.py --repo-root . list --type knowledge`（aip 技能目录是本技能的同级目录 `../aip/`），用当前症状命中已知真因，命中的打开全文读。
   - 命中条目是**先验假设，不是结论**：①用当前证据重新确认是否仍成立（看文件头 `last_reviewed`，过期项尤其重验），确认后 `aip_item.py reviewed <标识>`；②照样列出别的竞争假设，主动问"还有没有别的可能"。
   - 旧结论被证伪 → 先写新条目，再 `aip_item.py status <旧标识> superseded --by <新标识>`。
   - 原则：**先验加速调查，但不豁免证伪。**
1. **禁止直接给修复** —— 先精确复述可观察症状。
2. **取证复现** —— 命令输出/日志/代码引用，不靠脑补。
3. **列 2–3 个竞争假设** —— 不认定第一个。
4. **证据判别** —— 用最便宜的探针逐层下沉，定位真正断裂那一层。
5. **区分症状 vs 根因** —— 挖到具体可指之物为止。
6. **触类旁通（同类排查）** —— 根因一旦确认，**按其机理把它当成一类缺陷而非一处**：在当前变更范围内横扫所有共享该根因的兄弟站点，连同主站点一并修复，别只堵眼前这一个。范围之外的同类登记成旁路问题（`aip_item.py new --type inbox`），绝不默默漏过。
   - **边界**：同一根因的兄弟站点属 **in-scope**，不是侧发现——必须扫、必须处理；侧发现协议只收**无关**问题（capture, don't chase）。别拿"别追侧发现"当借口跳过同类排查。
7. **交用户判断** —— 摆出【根因 + 证据 + **同类波及面（已扫范围 + 命中站点）** + 修复选项 + 各自取舍】，由用户决策（接 AIP Stop-and-ask），不擅自实施深层改动。
8. **沉淀** —— 验证过的真因建成知识条目：先检索去重（像就并/在 `related` 加关联，不像才新增）；`aip_item.py new --type knowledge --title "一句话" --category <分类> --scope <适用范围> --status <active|draft>`，再编辑生成的文件填症状、根因、证据（相关代码的文件路径和函数名用反引号写出来）；按捕获纪律定状态——过 review 自检清单可直接标 `active` 并在知会里给依据，证据不足才先写 `draft`。属决策的建 `--type decision`，无关侧发现建 `--type inbox`。

> 调查产物一律落 AIP 活文档，不另起平行位置：验证过的真因进 `.aip/knowledge/`（按捕获纪律定 draft/active），
> 属架构决策的进 `.aip/decisions/`，无关侧发现进 `.aip/inbox/`；工作线状态记在 `.aip/tracks/`，看板由它生成。

## 时刻保持

- **警惕与证伪**：任何假设（含索引命中的旧条目）都要试图推翻，证据不足不下结论。
- **知识库正确可用**：沉淀后跑 `aip_check`；过期/失配条目复核或改 superseded，不留腐烂。

## 输出语言风格（怎么对用户说话）

面向用户的回答与说明（不含代码、命令、文件内容）遵守：

1. **用中文**，专业技术名词可保留英文。
2. **说大白话，不用黑话**；不生造词、不堆抽象比喻。必须用专业术语时第一次出现先一句话解释，不直接甩术语。
3. **专业、客观，以事实和结果为准**；不恭维、不自夸、不填充。结论先行再给依据；不确定就直说。
4. **第一性原理思考**；先拆到最基本的事实和约束再推导，不照搬惯例。

## 与 superpowers 的关系

若仓库 `process_skills: superpowers`，方法深度让位给 `systematic-debugging`；但本 skill 的 AIP 残留物（knowledge 条目 + 交用户判断）仍由它拥有，落 `.aip/` slot，不另起平行位置。无 superpowers 时本 skill 独立完整运行。
