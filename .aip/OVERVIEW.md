# 总览（OVERVIEW）· 活文档 · 开始/接手任务前读这页

> 顶部「在建」是手写源（AI 收尾时改）；下面「自动摘要」由 `aip overview` 派生、勿手改。
> 只装往前看 + 易腐的状态；不装 git 能派生的（改了哪些文件、流水账）。每块封顶几行；线 done 立即移出。

## 在建（多线看板）
（当前无活跃线）

## 已知缺口 / 旁路待办
（当前无）

<!-- AIP:AUTO-DIGEST:BEGIN (勿手改) -->
### 自动摘要（派生，勿手改）
**知识（4 条）**
- K-001 改完 scripts/ 必须先跑 sync_plugin.py，再跑 install_claude_plugin.py [superseded(by K-002)]
- K-002 改引擎要改仓库里的技能目录，不是已安装的副本 [active]
- K-003 把 AIP 装成项目级技能：`--home` 指项目根，钩子得另外重指 [active]
- K-004 引擎搬家后合并旧分支，危险的不是 git 冲突而是没冲突的路径假设 [active]

**近期决策**
- ADR-1：本仓库自举——从旧 `project_docs/` 迁入 `.aip/`
- ADR-2：协议文档从 per-feature/bug 轨道模型迁到扁平活文档模型
- ADR-3：捕获纪律从「draft 等人确认」改为「自主修改 + 事后审计」
- ADR-4：引擎并入 `aip` 技能目录，单副本分发；技能正文拆成核心 + 按需参考

**核心概念**
- （空）
<!-- AIP:AUTO-DIGEST:END -->
