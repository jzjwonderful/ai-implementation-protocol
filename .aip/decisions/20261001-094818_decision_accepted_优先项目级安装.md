---
title: 优先推荐项目级安装；引擎仓库自己也装一份并由检查保证跟源一致
status: accepted
---

- 背景: 全局安装一次升级会动到本机所有仓库。本机就有这样的例子：docflow 和两个 mr-review 克隆还是旧布局，tech-ai-kits 正迁移到一半，docflow 的提交前钩子还指向全局副本，一升级或卸载就会挡提交。用户要求以后各仓库逐个手动升级。
- 决策: (1) 文档和安装器都把项目级（`install_all.py --project <仓库>`）放在第一位，全局安装保留但不再推荐；全局装完多打一行提示。(2) `aip_doctor` 先认项目级安装，装了项目级就不要求全局，修复建议给 `--project`。(3) 引擎仓库自己也按项目级装一份（`.claude/skills/aip`、`.codex/skills/aip`，正常拷贝）；`aip_check` 逐个文件比对副本和 `plugins/ai-implementation-protocol/skills/aip`，不一致就报红，提交前钩子拦住，等于「源只有一份、副本必须跟上」。(4) 印给人或 AI 照着跑的命令一律用探测到的解释器（正在运行的那个），不写死 python3；会话开始看板打出钩子探测到的解释器，AI 整个会话用它。
- 理由: 项目级让技能和钩子跟着仓库走，大家拿到同一个版本；各仓库自己定什么时候升级，升级后整理（`reference/upgrade.md`）也是一个仓库一次。试过用链接指向源，放弃了：Windows 上 git 克隆默认不建符号链接（要开 `core.symlinks`），得到的是一个写着路径的普通文件，技能直接失效。解释器不写死：Linux 上 python 可能是 2.7，Windows 上常常只有 python。
- 影响: `README.md`、`docs/github-distribution.md`、`docs/adaptation.md`、插件 README、`scripts/install_all.py` 的输出、`aip_doctor.py` 的 `check_install`，`aip_check.py` 的 `check_engine_copies`，`_aip_common.py_cmd` 及各安装器、看板印出的命令；本机全局版已卸载。
