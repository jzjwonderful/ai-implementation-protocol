# 旁路问题收件箱 · 活文档

> 干 A 时撞见的、与 A 无关的问题。投递前先在 knowledge.md + 本表检索：已有类似（解决方案/旧讨论）就复用并加关联，确认是新问题才整理后登记。**不无脑 append**。
> 琐碎且同文件 → 顺手修不登记。出口：立项为新线 / 进 decisions / 进 OVERVIEW 旁路待办 / 关闭。

## 条目
- `.aip/config.yaml` 的 `gates.tests.cmd` 与 conventions 都写 `python -m unittest ...`，但脚本用了 `from __future__ import annotations` + `list[dict]`（需 Python 3.9+）。若机器上 `python` 指向 Python 2，gate 直接报错跑不起来。撞见场景：本会话里 `python` = 2.7，必须改用 `python3` 才能跑测试/脚本。出口待定：是否把命令统一成 `python3`，或在文档注明依赖 Python 3.9+。
