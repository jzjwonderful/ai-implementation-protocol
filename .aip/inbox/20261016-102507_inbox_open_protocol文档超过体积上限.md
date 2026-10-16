---
title: docs/protocol.md 超过 3 万字且有 1568 字的长行，按 0.8.0 的规则该按主题拆
status: open
---

- 发现于: 做 0.8.0「会膨胀的文件按主题拆分」时量的
- 影响范围: `docs/protocol.md`（英文协议说明，AI 按铁律「协议是真源」改行为时要同步改它）
- 症状 / 证据: 2026-10-16 量得 31106 字，最长一行 1568 字；本仓库没开 `size_check_paths`，所以 aip_check 不报
- 去向: 待定。可以按章节拆成 docs/protocol/ 下几个文件，再把 `docs/*.md` 加进 `size_check_paths`
