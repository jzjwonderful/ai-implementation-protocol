# 知识索引（自动生成，勿手改；运行 `aip knowledge` 重建）

| ID | 分类 | 状态 | 适用范围 | 标题 | 最后复核 |
| --- | --- | --- | --- | --- | --- |
| K-001 | process-lifecycle | superseded(by K-002) | 凡改动 `scripts/`、`docs/`、`templates/`、`schemas/` 任意文件后想让安装生效，均需此顺序；AI 辅助改动时须确认落点是 repo root `scripts/`，不是 `~/plugins/` | 改完 scripts/ 必须先跑 sync_plugin.py，再跑 install_claude_plugin.py | 2026-06-27 |
| K-002 | process-lifecycle | active | 凡改 AIP 引擎本身（`plugins/ai-implementation-protocol/skills/` 下任何文件）。正确落点是仓库源；改完重跑安装器让副本更新 | 改引擎要改仓库里的技能目录，不是已安装的副本 | 2026-09-14 |
