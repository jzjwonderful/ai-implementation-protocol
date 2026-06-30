# 项目规约 · 活文档

> 这工程「怎么干」的常驻规则。从空白靠捕获长大——被纠正一次就记一条。机器能强制的（linter/formatter/CI）指向它，文档只记需人/AI 判断的。

## 代码风格
- <暂无>
## 注释风格
- <暂无>
## 设计风格
- 凡是后缀为 `.md` 的生成/派生件（如 `knowledge_index.md`、OVERVIEW 自动摘要块），输出必须是合法 Markdown（GFM）：用真表格（带 `|---|` 分隔行、行首尾带 `|`）而非裸竖线行；不用 `#` 当行注释（Markdown 里 `#` 是标题），要注释用 `<!-- -->`。新增任何 `.md` 生成器都照此办，并加测试守住格式。
## 构建 / 调试 / 验收固定流程
- 构建：`python -m unittest discover -s tests` ｜ 测试：`python -m unittest discover -s tests` ｜ 验收通用标准：<暂无>
