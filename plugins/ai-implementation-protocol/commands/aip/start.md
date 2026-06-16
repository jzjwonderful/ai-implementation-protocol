---
description: 对话式开始一个新特性（口述需求→头脑风暴→自动生成 id/title/spec 初稿）
---
不要让用户手敲 id/--title。按 `aip` skill 的「对话式 start」与用户对话形成任务描述，再调用：
`python <plugin-root>/scripts/aip.py start <生成的id> --title "<生成的title>" --repo-root .`
