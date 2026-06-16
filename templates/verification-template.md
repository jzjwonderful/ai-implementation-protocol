# Verification

> 验收硬绑**真实证据**，不靠"我觉得好了"。每个 config.yaml 声明的 gate 都要在下表给出
> 真跑结果（pass/fail）与证据；有未跑的进 "Not Run" 如实记，不静默略过。

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
<!-- 本轮撞见的无关问题是否都登记进 findings.md 并标了去向；有没有被侧发现带偏混入无关改动。 -->
