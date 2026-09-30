---
title: 捕获纪律从「draft 等人确认」改为「自主修改 + 事后审计」
status: accepted
aliases: ADR-3
---

- 日期 / 状态（迁移前）: 2026-07-07 / 采纳
- 背景：issue #4 讨论定的共识（仓库主人 + GPT-5.5 + Grok + Claude）：实际使用中人没精力逐条确认 draft，文档维护主力必然是 AI；但完全放开又可能失控、质量滑坡。
- 决策：AI 写活文档前逐条过 review 自检清单，通过后可直接写（含直接标 active），但必须当场知会用户 + 随本次工作同一次 git 提交留痕；推翻决策/规约只许追加取代（注明「取代 ADR-N」），删除/合并只认「已被证明错误」「与另一条重复」两个理由。配套：`aip review` 软质量自检（不卡 CI）、`aip doctor` 安装健康检查、`aip init` 两阶段（脚本建骨架 + AI 只填模板原样/空的文件）。
- 理由：把事前闸门换成事后可审计——git diff 就是审计日志，坏改动可回滚、可抽查，而流程不再阻塞；「充分 review」落成可执行清单而非「质量优先」这类口号，避免不同 AI 各自理解。放弃了「人逐条确认」的强保证，代价是坏改动要靠事后抽查发现。
- 影响：SKILL.md（捕获纪律 / review 清单 / 完成检查 / init 两阶段）与 `docs/protocol.md` 同步改写；knowledge 模板的状态语义更新（active=已按清单核过）；新增 `aip_doctor.py` 与 `VERSION`；`sync_plugin.py --check` 改真实比对且比对逻辑单源化进 `sync_plugin.drift`。
