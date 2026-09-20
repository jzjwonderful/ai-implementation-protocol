# 旁路问题收件箱 · 活文档

> 干 A 时撞见的、与 A 无关的问题。投递前先在 knowledge.md + 本表检索：已有类似（解决方案/旧讨论）就复用并加关联，确认是新问题才整理后登记。**不无脑 append**。
> 琐碎且同文件 → 顺手修不登记。出口：立项为新线 / 进 decisions / 进 OVERVIEW 旁路待办 / 关闭。

## 条目
- 已关闭：命令不写死解释器名。gate/文档统一写 `python` 并注明「解释器名按本机、需 Python 3.9+」；强制闸门（pre-commit）本就烧 install_hooks 装钩子时的 `sys.executable` 绝对路径，不受名字影响。（早先"统一成 python3"的结论作废——Windows 上常只有 `python`、没有 `python3`，反而跑不起来。）
- 待处理：`install_hooks.py` 把 Claude SessionStart/Stop 钩子写进项目的 `.claude/settings.json`，命令里烧了本机 Python 和技能目录的绝对路径。这个文件通常会进 git，换机器或换人就失效。候选做法：改写到 `.claude/settings.local.json`（不进 git，每台机器各自 `aip init`），或命令里用 `$HOME`/`%USERPROFILE%` 相对写法。本次重构没动这一点，只把脚本名换了。
- 待处理：`agent/engine-into-skill-0.3.0` 与 `origin/master` 已分叉。0.3.0 把引擎搬进 `plugins/.../skills/aip/`，清空了 `plugins/.../scripts/` 和根 `templates/`；master 之后在这些被清空的位置新增了 `aip_brainstorm.py`、`install_all.py`、`install_grok_plugin.py` 和 aip-brainstorm 技能。git 合并时「删目录内已有文件」对上「新增文件」不算冲突，会静默合出一个跑不起来的树（grok 安装器自检 `<plugin>/scripts/aip_init.py`、brainstorm 技能引用 `<engine>/scripts/aip_brainstorm.py`，两个路径合并后都不存在）。合之前要先把这三个脚本按 0.3.0 的布局搬位置、改路径。
