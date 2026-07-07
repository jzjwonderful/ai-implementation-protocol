# 总览（OVERVIEW）· 活文档 · 开始/接手任务前读这页

> 顶部「在建」是手写源（AI 收尾时改）；下面「自动摘要」由 `aip overview` 派生、勿手改。
> 只装往前看 + 易腐的状态；不装 git 能派生的（改了哪些文件、流水账）。每块封顶几行；线 done 立即移出。

## 在建（多线看板）
▶[active] issue#4 增强实施：README 纠偏 → SKILL/协议纪律修订 → init 测试 → VERSION+doctor → 安装/sync 修正
  - must_read: docs/protocol.md, plugins/ai-implementation-protocol/skills/aip/SKILL.md
  - 下一步: 按 issue#4 的任务 0~7 顺序逐个提交；全部完成后移出本线

## 已知缺口 / 旁路待办
1. `gates.lint_or_drift` 未声明：根/插件副本一致性靠 sync_plugin.py + pre-commit hook 兜底，但未在 config.yaml 显式声明检查命令

<!-- AIP:AUTO-DIGEST:BEGIN (勿手改) -->
### 自动摘要（派生，勿手改）
**知识（1 条）**
- K-001 改完 scripts/ 必须先跑 sync_plugin.py，再跑 install_claude_plugin.py [draft]

**近期决策**
- ADR-1：本仓库自举——从旧 `project_docs/` 迁入 `.aip/`
- ADR-2：协议文档从 per-feature/bug 轨道模型迁到扁平活文档模型

**核心概念**
- （空）
<!-- AIP:AUTO-DIGEST:END -->
