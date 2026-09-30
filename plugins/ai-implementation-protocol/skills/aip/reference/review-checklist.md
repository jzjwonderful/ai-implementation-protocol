# review 自检清单（写活文档前逐条过）

目标永远是**文档质量**而非内容丰富度：清晰、准确、必要、最小化。**默认动作是删除或合并，不是新增**——每条新增都先过必要性关，过不了就别写。宁可少写，不要多写、错写、冗余。

1. 先查有没有同类：条目按文件名和 `aip_item.py list` 找，相近的打开全文读；整篇文档（reference / conventions）读全文。确认不与现有内容重复/冲突；相似就合并或在 `related` 里加关联，不新增。
2. 只写自己验证过的事实（跑过命令、读过代码、复现过）；拿不准的标 draft 或投 inbox。整份清单都过了才可标 active，且在知会里给依据。
3. 必要性：半年后一个新 AI 读到它，没有这条会明显增加理解成本吗？不会就删；会但表述不清就重写；重写还不清就不写。
4. 最小化：一条只说一件事；不复述 git 历史/代码本身能推出来的信息。
5. 位置正确：坑与根因→knowledge/；概念与复用件→reference；规约→conventions；旁路问题→inbox/；架构方向→decisions/。放错位置比不写危害更大。
6. 改完跑 `aip_check`，红了当场修；需要看新看板就跑 `aip_overview`。

## 整份 `.aip/` 的 review

触发条件在 SKILL.md。做法：

1. 对每个活文档过上面六条，发现的问题用「问题点 + 修改建议 + 理由 + 影响」格式列出来再改。
2. 对照现状核事实：`aip_upkeep.py --all` 列出的 knowledge 逐条重验（仍成立就 `aip_item.py reviewed`，缺陷已修改 `fixed`，被取代改 `superseded`）；reference 里的构件、路径是否还在；inbox/ 里已闭环的改 `closed`；tracks/ 里做完的改 `done`。
3. 顺带核项目技能和说明文件（`CLAUDE.md` / `AGENTS.md`、项目技能目录）里的路径、命令、叫法是否还和现状一致。
4. 做完把 `config.yaml` 的 `review_last_full` 改成当天，随本次提交。

review 只管文档质量，不做问题分析。
