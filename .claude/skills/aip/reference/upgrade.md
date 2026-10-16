# 升级后整理：把仓库里已有的 `.aip/` 调到新模板

`<skill>` 指本技能目录（SKILL.md 所在目录）。

新版 AIP 改了模板或规矩时，已有仓库里的 `.aip/` 不会自己变，要 AI 按这里调整。每个仓库在 `.aip/config.yaml` 的 `aip_version` 里记着按哪一版整理过（没有这个字段的是 0.7.0 之前建的）。会话开始发现下面有比它新的版本，就会提醒「还没按新模板整理」。

## 怎么做
1. 先跟用户说：要整理哪几个版本的调整、大概动哪些文件。同意了再做。
2. 起点干净：`.aip/` 没有没提交的改动；有的话先问用户怎么处理。
3. 从 `aip_version` 之后的版本开始，按版本从旧到新逐节做。每节里拿不准的（比如一条旧铁律还算不算数）问用户，不要自己删。
4. 做完把 `config.yaml` 的 `aip_version` 改成做到的最新版本号（没有这个字段就加上），跑 `python3 <skill>/scripts/aip_check.py --repo-root .`，红了改掉。
5. 整理放在一个提交里（某一版另有要求的按那一节，比如 0.8.0 的拆分要单独一个提交），提交说明写「.aip 按 AIP <版本> 模板整理」，并逐项知会用户改了什么。

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

## 0.8.0

会越写越大的文件拆开：`reference.md` 按主题拆成 `.aip/reference/<主题>.md`，可复用实现改成一条一个文件，`conventions.md` 只留跨模块的铁律并封顶。目的是省上下文：每次必读的只剩一小份，其余按「什么时候读」挑着读。`aip_version` 改成 0.8.0 之后，`aip_check` 才开始查体积和引用，所以**先拆，最后改版本号**。

1. **刷新说明文件和钩子**：跑 `python3 <skill>/scripts/aip_init.py --repo-root .`。托管块换成第 5 版，pre-commit 钩子多一步「列出这次改动相关的主题和条目」（只列不挡），并建好 `.aip/reference/`、`.aip/reuse/` 两个目录。
2. **拆 `reference.md`**（这一步单独一个提交，只搬内容、不改内容，方便审阅。动手前先看有没有正在开发、改过 `reference.md` / `conventions.md` / 规格书的分支：拆完它们变基会冲突，先跟用户排好合入顺序）：
   - 每个 `##` 小节变成 `.aip/reference/<主题>.md`，文件名就是主题、不带时间戳。文件头按 `<skill>/templates/topic-template.md` 写 `title`、`read_when`（一句话写什么时候该读，不超过 80 字）、`paths`（涉及哪些代码，路径或通配，逗号分隔；不针对具体代码就不写）。小节太大的再按子主题拆。
   - 「核心实体与关键铁律（不变量）」里不管改哪里都可能踩到的，搬进 `conventions.md` 的「## 核心不变量」；只跟某块代码有关的进对应的主题文件。
   - 「可复用实现」表每行改成一条 reuse 条目：`aip_item.py new --type reuse --title "<能力>" --paths "<实现所在的文件>"`，正文填钦定实现、边界（什么时候用、什么时候别用）。钦定实现在外部（命令行工具、别的仓库）的，`paths` 写本仓库调用它的文件；其实是操作步骤、不是代码的行，改成知识条目，不建 reuse。
   - 「见本文「某节」」这类文件内指针，拆完多半指空了：搬内容时一起改成「见 `.aip/reference/<主题>.md`「某节」」。
   - 搬完删掉 `reference.md`。
3. **瘦 `conventions.md`**：只留不管做什么任务都会踩到的铁律、核心不变量、构建验收流程；整篇不超过 8000 字、每节不超过 3000 字。判断标准是「每个任务都用得上」，不是「跨模块」：代码风格、开发流程这类虽然跨模块，但不是每次都要读，搬进主题文件，`read_when` 写「写代码时」「提交前」。拿不准的问用户。
4. **其余超大的 `.aip/` 文件**（比如 `specs/` 下的规格书）：单个超过 3 万字的按主题拆；末尾不断追加的「状态注记」「变更记录」挪进在建线或单独的条目，或拆成单独一份（比如 `<规格>-rollout.md` 放上线、迁移、待定问题），规格书正文只写现状。单行超过 1000 字的（表格格子或一条要点里塞了整段话）按句号拆成多条要点；超过 30 行的表格要么改成一条一个文件，要么按小标题拆成几张表。
5. **补 `paths`**：常用的知识条目在文件头加 `paths`（涉及的代码路径），改到这些文件时 `aip_lookup.py relevant` 和提交前钩子会把它列出来。代码里已经写了 `.aip/knowledge/<时间戳_简述>` 锚点的不用补，锚点同样会被反查。
6. **修断掉的引用**：说明文件、`conventions.md`、主题文件、在用的条目里写的「`reference.md`「某节」」改成对应的主题文件；改完版本号后 `aip_check` 会逐个列出还断着的。
7. **仓库外的提示词**：数据库、平台配置、别的仓库里存的提示词（比如代码评审说明写着「先读 reference.md」）检查不到，问用户有没有，有就投旁路问题跟进。
8. **项目自己的文档要不要查体积**（可选）：想让 `aip_check` 也查 `.aip/` 以外的文档，在 `config.yaml` 加 `size_check_paths: "docs/**/*.md"`（逗号分隔的通配，注释照 `<skill>/templates/config-template.yaml`）。
9. `aip_version` 改成 `0.8.0`，跑 `aip_check`，红了按提示改掉。第 2 步之后的调整放一个提交。

## 0.8.1

按两个仓库整理 0.8.0 的反馈做的修正。体积和引用检查查得更全，所以同样先改完、最后改版本号。

1. **刷新钩子和说明文件**：跑 `python3 <skill>/scripts/aip_init.py --repo-root .`。提交前钩子改成按当前检出的根目录找引擎（以前写死装钩子那个工作区的路径，worktree 里提交跑的是旧引擎），git worktree 里跑 init 也不再报错。`CLAUDE.md` 只有一行 `@AGENTS.md` 的，init 不再往里补托管块；以前补进去的删掉，只留 `@AGENTS.md`。
2. **项目自己的技能正文**（`.claude/skills/*/SKILL.md`、`.codex/skills/*/SKILL.md`、`.agents/skills/*/SKILL.md`，装进来的 aip 不算）：超过 8000 字的，正文只留流程，细节挪到技能目录的 `reference/` 下按需读。
3. **引用检查查得更全**：`.aip/` 下条目以外的文档（如 `specs/`）、`size_check_paths` 列的文档、项目自己的技能也查；「本文「某节」」这种文件内指针也查。旁路问题不再查（它本来就在记哪里还指着旧东西）。改完版本号后 `aip_check` 会逐个列出，改成现在的位置。
4. **reuse 条目回看一遍**：其实是操作步骤、不是代码的，改成知识条目（`aip_item.py new --type knowledge`），再删掉这条 reuse。
5. `aip_version` 改成 `0.8.1`，跑 `aip_check`，红了按提示改掉，一个提交。

