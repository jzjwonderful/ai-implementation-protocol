# `/aip init`（Codex 里是 `$aip init`）

唯一由人敲的命令，两阶段。`<skill>` 指本技能目录（SKILL.md 所在目录）。

## 阶段 A（脚本，确定性）

```
python3 <skill>/scripts/aip_init.py --repo-root .
```

建 `.aip/` 骨架（reference / conventions / config 三份文档，knowledge / decisions / inbox / tracks 四个条目目录；新建的 config.yaml 把 `aip_version` 记成当前版本）、升级 `AGENTS.md`/`CLAUDE.md` 中的 AIP 托管引导块、装 git pre-commit 钩子和 Claude Code SessionStart 钩子、删掉以前版本生成的 `OVERVIEW.md`。幂等：已有活文档和用户内容一律不覆盖；只有带 AIP managed 标记的区域会按新版本刷新。`.aip/` 还是旧布局（knowledge.md 等大文件）时 init 不动手，先按 `/aip migrate` 迁移。

SessionStart 钩子在新会话、恢复会话、以及上下文被压缩之后按目录打印看板（在建线全文、待处理旁路问题的文件名）；压缩后会多提醒一句"以在建线为准"。项目级安装时钩子命令先找 `python3`、再找 `python`，只用 3.9 以上的，找不到就打一句提示、不执行。压缩前的钩子输出到不了模型，所以补救放在压缩后。

## 阶段 B（AI 分析填充，阶段 A 跑完立即做）

1. 自己看项目获取信息，**不向用户提问**（零配置指不问人，不是不了解项目）：读 README、构建/依赖清单（package.json / pyproject.toml / go.mod / Cargo.toml 等）、测试目录、CI 配置、目录结构。
2. 据此判断技术栈、构建命令、测试命令、目录职责、有无测试。
3. 填充规则（升级安全的核心）：**只往「还是模板原样或空」的文件里写**；文件已有用户内容的一律不碰，确有缺口就按捕获纪律追加条目、不覆盖。构建/测试命令进 config.yaml 的 gates；核心概念与目录职责进 reference；铁律和已成文的做法进 conventions。
4. 无测试/legacy 项目：不硬编 gates.tests；记一条旁路问题「无测试，建议从表征测试起步」，不自作主张生成测试。
5. 结束时输出初始化总结：识别到什么 / 逐文件列出填了什么 / 哪些拿不准 / 建议用户确认什么。
