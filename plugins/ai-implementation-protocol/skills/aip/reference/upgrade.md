# 升级后整理：把仓库里已有的 `.aip/` 调到新模板

`<skill>` 指本技能目录（SKILL.md 所在目录）。

新版 AIP 改了模板或规矩时，已有仓库里的 `.aip/` 不会自己变，要 AI 按这里调整。每个仓库在 `.aip/config.yaml` 的 `aip_version` 里记着按哪一版整理过（没有这个字段的是 0.7.0 之前建的）。会话开始发现下面有比它新的版本，就会提醒「还没按新模板整理」。

## 怎么做
1. 先跟用户说：要整理哪几个版本的调整、大概动哪些文件。同意了再做。
2. 起点干净：`.aip/` 没有没提交的改动；有的话先问用户怎么处理。
3. 从 `aip_version` 之后的版本开始，按版本从旧到新逐节做。每节里拿不准的（比如一条旧铁律还算不算数）问用户，不要自己删。
4. 做完把 `config.yaml` 的 `aip_version` 改成做到的最新版本号（没有这个字段就加上），跑 `python3 <skill>/scripts/aip_check.py --repo-root .`，红了改掉。
5. 整理放在一个提交里，提交说明写「.aip 按 AIP <版本> 模板整理」，并逐项知会用户改了什么。

还是 0.5.0 之前的旧布局（`knowledge.md` 等大文件）的，先按 `reference/migrate.md` 迁移，再回来做这里。

每节标题是版本号，会话开始的提醒靠这些标题判断还有没有没做的调整：新增一节就是要求所有仓库调整一次。只改脚本、不用动仓库的版本不要加节。

## 0.7.0

看板不再存文件，在建线做完就删，`config.yaml` 只留用得上的字段，项目铁律搬进 `conventions.md`。

1. **刷新说明文件和钩子**：跑 `python3 <skill>/scripts/aip_init.py --repo-root .`。它会刷新 `CLAUDE.md` / `AGENTS.md` 里的 AIP 托管块，重装会话开始钩子（项目级安装的钩子命令改成先找 `python3`、再找 `python`，只用 3.9 以上的），删掉生成的 `.aip/OVERVIEW.md`。已有内容不覆盖。仓库原来就没装钩子、用户也不想装的，加 `--no-hooks`。
2. **旧看板**：`.aip/.gitignore` 里删掉 `OVERVIEW.md` 那一行，只剩这一行就把 `.gitignore` 整个删掉。`OVERVIEW.md` 要是没被自动删掉（开头不是「# 总览（自动生成，勿手改）」，说明有人手写过），把里面还有用的内容搬进在建线或旁路问题，再删掉它。
3. **在建线**：`tracks/` 下文件名带 `_done_` 的直接删掉（`aip_check` 会报红）。还是 active 但其实已经做完的、剩下的事都不在本仓库的，也删掉，剩下的事投 inbox。留下的线对照模板压成目标、卡在哪、下一步、先读四项（旧的「卡哪」「must_read」改成新叫法）。
4. **`config.yaml`**：只留 `gates`、`review_last_full`、`aip_version`、`aip_remote`、`aip_remote_branch`，其余字段引擎不读、AI 也不会去看，写了等于没写：
   - `iron_rules` 有内容的，搬进 `conventions.md` 开头的「## 铁律」一节（没有这一节就按 `<skill>/templates/conventions-template.md` 加上）。和 `conventions.md` 里已有的话重复的合并成一条，和知识条目重复的只留一处。
   - `truth_sources` 有内容的，改写成一条铁律（「行为变更同次更新 <这些文档>」），或者写进 `reference.md`。
   - `lenses`、`indexes`、`anti_accretion`、`verification_notes`、`process_skills` 有内容的，还有用就改写成 `conventions.md` 里的规约，没用就删。
   - 删掉这些字段和它们的注释；按 `<skill>/templates/config-template.yaml` 补上 `aip_version` 的注释。
5. **`conventions.md`**：「构建 / 调试 / 验收固定流程」里如果写着 `python -m unittest discover -s tests`，这是旧模板写死的，不是你这个项目的命令：改成项目真实的命令或删掉，命令以 `config.yaml` 的 `gates` 为准。
6. **其余提到旧看板的地方**：说明文件托管块以外、项目技能、`.aip/README.md` 里写着「读 `.aip/OVERVIEW.md`」「跑 `aip_overview.py`」「做完把线改 done」的，改成新说法：看板由会话开始钩子打印，没有钩子就看 `tracks/` 和 `inbox/` 下带 `_open_` 的文件名；线做完就删，随这条线最后一个 MR 提交。
7. `aip_version` 改成 `0.7.0`。
