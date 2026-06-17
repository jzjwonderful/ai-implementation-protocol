# Verification

> 修复硬绑**真实证据**：先证明 bug 真被复现并修掉（Regression），再过机器闸门与独立复核。

## Regression
<!-- 能复现该 bug 的测试/探针：修复前失败、修复后通过。给命令 + 前后结果。 -->

| repro | command | before | after | evidence |
|-------|---------|--------|-------|----------|
| <一句话复现项> | <cmd> | fail | pass | <输出摘要 / 测试路径> |

## Machine Gates
<!-- 每个 config.yaml gates 里声明的闸门一行；result 取 pass/fail；evidence 给命令输出摘要或报告路径。 -->

| gate | command | result | evidence |
|------|---------|--------|----------|
| <tests> | <cmd> | pass\|fail | <输出摘要 / 报告路径> |

## Independent Review (fresh-eyes)
<!-- 评审者 ≠ 实现者；带证伪视角。结论 + 处置。 -->
- 结论：<✅可信 / ⚠️有缺口已处置 / ❌需改>
- 处置：<退回改了什么 / 已知局限如实记>

## Not Run
<!-- 该跑没跑的（环境/时间所限），如实列，不静默略过。 -->

## Known Risks
<!-- 残留风险与边界。 -->

## Side-Findings This Round
<!-- 本轮撞见的无关问题是否都登记进 findings.md 并标了去向。 -->
