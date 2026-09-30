<!-- BEGIN AIP (managed) -->
<!-- AIP managed version: 3 -->
## AI Implementation Protocol
**会话开始时必须先调用 `aip` 技能，再做任何其他事（包括回答问题）。**
调完技能后读 `.aip/OVERVIEW.md`（自动生成的看板：在建线、待处理问题、知识概况）；没有这个文件就用技能里的 `aip_overview.py` 生成。
条目一条一个文件，文件名是 `时间戳_类型_状态_简述.md`：`.aip/knowledge/` 验证过的坑和根因、`decisions/` 架构决策、`inbox/` 旁路问题、`tracks/` 在建线。先按文件名或 `aip_item.py list` 找相关的，再打开读，不要通读整个目录；新建、改状态走 `aip_item.py`，引用别的条目写完整的「时间戳_简述」。
其余按需查：`reference.md` 核心概念+复用件 / `conventions.md` 规约。
编码任务开始前先读懂项目验证机制，并建立“plan/需求 → 实现位置 → 行为证据”的验收矩阵；完成前逐项核对。
不能只凭 build/lint 通过宣布功能完成，也不得通过删除、跳过或削弱测试绕过约束；未闭环时必须说明未验证项和风险。
语言一律大白话，禁止黑话。
<!-- END AIP (managed) -->
