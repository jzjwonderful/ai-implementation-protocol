# 现状（STATUS）· 活文档 · 新会话先读这页

> **用途**：站在哪——实现到哪了、在建什么、已知缺口、部署在哪。是项目级**现状真理源**，新会话/接手者第一读物。
> **维护铁律**：行为/架构变更 → **同次**更新本页（与 feature 的 verification/handoff 不同：那是任务态，这是项目现状）。

## 能力现状
图例：✅ 已实现并验证 · 🔶 部分/有缺口 · ⏳ 计划中

| 模块/能力 | 状态 | 说明 |
|---|---|---|
| AIP 引擎（init/start/bug/resume/check/knowledge/done） | ✅ | 纯标准库 CLI，`scripts/aip.py` 路由；28 个 unittest 全绿 |
| 阻断闸门 `aip check` | ✅ | 活文档/槽位/findings 分类/机器闸门绑证据/无并行产物/知识索引一致；失败退出码 1 |
| git pre-commit hook | ✅ | `install_hooks.py` 把 check 挂成提交闸门（本仓库尚未安装，见已知缺口） |
| bug 轨道（轻量轨） | ✅ | `feat/aip-bug-track` 分支：report.md + 完整性闸门 + 回归闸门 + resolution 收尾 |
| 知识沉淀（root-cause + knowledge.md） | ✅ | 先查后挖、真因 append-only 沉淀、`aip knowledge` 重建索引 |
| 双副本同步（顶层真源 → plugins/ 副本） | ✅ | `sync_plugin.py` 再生；当前根/插件副本逐字节一致 |
| 自举（本仓库用 AIP 管自己） | ✅ | 已从旧 `project_docs/` 迁入 `.aip/`，aip check 通过 |

## 当前焦点 / 在建
- 分支：`feat/aip-bug-track`（已 rebase 到最新 origin/master，含 PR#3 输出语言风格）
- 刚完成：用 AIP 接管本工程自身（旧 `project_docs/` → `.aip/`，填 config，check 通过）
- 在建：无活动工作包（`current_task.feature_id` 为空）；bug 轨道待并入 master

## 已知缺口 / 技术债（按优先级）
1. 本仓库未安装 pre-commit hook（`python scripts/install_hooks.py --repo-root .` 一行装上，使 check 自动化）
2. `gates.lint_or_drift` 未声明：根/插件副本一致性目前靠 iron_rules 人工纪律，无机器闸门兜底（`sync_plugin.py --check` 只列不挡）

## 真理源地图（去哪找什么）
| 想知道… | 看哪 |
|---|---|
| 现状/缺口/部署 | 本页 `STATUS.md` |
| 某架构**为什么这么定** | `decisions.md`（ADR-lite） |
| 有哪些**正典构件可复用** | `canonical-assets.md` |
| 开发时撞见的**无关问题**往哪放 | `findings.md`（侧发现收件箱） |
| 当前在做什么任务/怎么续作 | `_runtime/current_task.json` + `features/<id>/handoff.md` |
| 本项目适配配置（闸门/lens/真理源） | `config.yaml` |
| <项目特定：完整需求/契约/UI 准则…> | <填项目自己的 spec/PRD/conventions 路径> |

## 部署 / 访问速查
- <环境、地址、凭据指针（凭据不入库，指向密钥管理）>
