<!-- BEGIN AIP (managed) -->
<!-- AIP managed version: 5 -->
## AI Implementation Protocol
**会话开始时必须先调用 `aip` 技能，再做任何其他事（包括回答问题）。**
调完技能后看在建线和待处理问题：会话开始钩子会打印出来；没打印就自己读 `.aip/tracks/` 下的文件、列 `.aip/inbox/` 下文件名带 `_open_` 的。
条目一条一个文件，文件名是 `时间戳_类型_状态_简述.md`：`.aip/knowledge/` 验证过的坑和根因、`decisions/` 架构决策、`inbox/` 旁路问题、`tracks/` 在建线（做完就删）、`reuse/` 可复用实现。先按文件名或 `aip_item.py list --grep` 找相关的，再打开读，不要通读整个目录；新建、改状态走 `aip_item.py`，引用别的条目写完整的「时间戳_简述」。
动手前读 `.aip/conventions.md`（只有跨模块的铁律）；`.aip/reference/` 下的主题文件按看板上的「什么时候读」挑相关的读；改代码前跑 `aip_lookup.py relevant <要改的文件>` 看相关的主题和条目。
会越写越大的内容拆开写：一条条追加的记录一条一个文件，整篇说明按主题拆成多个文件。
编码任务开始前先读懂项目验证机制，并建立“plan/需求 → 实现位置 → 行为证据”的验收矩阵；完成前逐项核对。
不能只凭 build/lint 通过宣布功能完成，也不得通过删除、跳过或削弱测试绕过约束；未闭环时必须说明未验证项和风险。
语言一律大白话，禁止黑话。
<!-- END AIP (managed) -->
