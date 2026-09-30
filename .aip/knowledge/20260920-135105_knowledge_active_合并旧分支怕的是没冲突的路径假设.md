---
title: 引擎搬家后合并旧分支，危险的不是 git 冲突而是没冲突的路径假设
status: active
category: build
scope: 任何「一侧改布局、另一侧加功能」的合并。解完冲突要额外做两件事：全库搜老路径字符串，以及把装/跑的全链路真跑一遍（本次是 install_all → aip_init → aip_check → aip_doctor）
last_reviewed: 2026-10-01
aliases: K-004
---

- 症状: 把改布局前分叉出去的分支合回来，冲突都解完、`git status` 干净，装出来的东西却是坏的
- 根因: 布局改动（0.3.0 把引擎从 `plugins/.../scripts/` 搬进 `skills/aip/scripts/`）只改了文件位置，改不动另一侧新写的代码里对老位置的假设。git 只比对文本和路径：另一侧新增文件的位置冲突它会报，但「安装器自检 `<pkg>/scripts/aip_init.py`」「只拷 SKILL.md 不拷整个技能目录」「调用方按旧签名传参」这类假设它看不见，合完全绿
- 证据: 本次合并 git 报了 3 个 file-location 冲突（aip_brainstorm/install_all/install_grok_plugin）并自动指向新目录，但同时静默合进了四处坏掉的假设：Grok 安装器 `copy2(SKILL.md)` 导致技能正文里的 `<skill>/scripts/` 落空；grok 与 install_all 的自检仍查 `<pkg>/scripts/aip_init.py`；`install_all` 调 `claude.install_skills(pkg, home, force=True)` 而 0.3.0 的签名是 `(skills_dir, home)`；新增的 `.grok-plugin/plugin.json` 停在 0.2.1 且不在 `ENGINE_MANIFESTS` 里，版本漂移检查查不到它
- 关联: 20260914-224845_改引擎要改仓库里的技能目录不是已安装的副本 / 20260920-134332_装成项目级技能要另指钩子 / 20260914-224845_引擎并入技能目录单副本分发
