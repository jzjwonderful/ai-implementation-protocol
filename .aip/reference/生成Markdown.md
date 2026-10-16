---
title: 生成Markdown
read_when: 新增或修改会输出 .md 文件的脚本时
paths: plugins/ai-implementation-protocol/skills/aip/scripts/aip_item.py, plugins/ai-implementation-protocol/skills/aip/scripts/aip_migrate.py
---

## 格式
- 凡是后缀为 `.md` 的生成/派生件，输出必须是合法 Markdown（GFM）：用真表格（带 `|---|` 分隔行、行首尾带 `|`）而非裸竖线行；不用 `#` 当行注释（Markdown 里 `#` 是标题），要注释用 `<!-- -->`。新增任何 `.md` 生成器都照此办，并加测试守住格式。
