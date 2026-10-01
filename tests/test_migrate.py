"""旧布局（一类一个大文件）→ 一条一个文件。"""
import os, subprocess, sys, tempfile, unittest
from pathlib import Path
from _engine import SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_migrate as mig, aip_check as chk, aip_item as it

KNOWLEDGE = """# 知识库

## 类目
other

<!--
## K-NNN: 模板示例，不是条目
-->

## K-001: 老办法会卡住
- rule_id: general_old_way_hangs
- 分类: other
- 状态: superseded(by K-002)
- 症状: 卡住
- 根因: 锁没放
- 适用范围: 某模块
- 最后复核: 2026-06-01

## K-002: 新办法不卡
- 分类: other
- 状态: fixed（已修，2026-06-28）
- 症状: 不卡
- 根因: 换了锁
- 适用范围: 某模块（K-001 的后继）
- 最后复核: 2026-06-28
- 关联: K-001 / ADR-2 / I-2

**规则**：正文后面的段落也要带上。

## K-003: 被新机制取代了
- 分类: other
- 状态: superseded
- 症状: x
- 根因: y
- 适用范围: z
- 最后复核: 2026-06-28
"""

DECISIONS = """# 决策记录

## 格式
```
## ADR-N：<标题>
- 日期 / 状态：YYYY-MM-DD / 采纳 | 已被 ADR-M 取代
```

## ADR-1：先用大文件
- 日期 / 状态：2026-04-01 / 已被 ADR-2 取代
- 决策：一类一个文件

## ADR-2：改成一条一个文件
- 日期 / 状态：2026-10-01 / 采纳（取代 ADR-1）
- 决策：一条一个文件
"""

INBOX = """# 旁路问题收件箱

## 条目

## I-1：还没处理的问题
- 发现 / 状态：2026-09-01 / 待处理

## I-2：处理完的问题
- 发现 / 状态：2026-09-02 / **已关闭（2026-09-03）**

### I-2：撞号的另一条
- 发现 / 状态：2026-09-04 / 待处理
"""

OVERVIEW = """# 总览
> 顶部说明，不搬

## 在建（多线看板）
### ▶[active] 新布局（2026-10-01 开工）
- 下一步：写迁移

### [done] 上线完的线
- 已上线

### 收口备忘（接手前看一眼）
- 某条线做完了，还没部署

## 已知缺口 / 旁路待办
（当前无）

<!-- AIP:AUTO-DIGEST:BEGIN (勿手改) -->
- K-001 老办法
<!-- AIP:AUTO-DIGEST:END -->
"""


def git(repo: Path, *args: str, when: str = "2026-06-15T12:00:00") -> None:
    env = {**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=repo, env=env,
                   check=True, capture_output=True)


def old_repo() -> Path:
    d = Path(tempfile.mkdtemp())
    a = d/".aip"; a.mkdir()
    for name, text in [("knowledge.md", KNOWLEDGE), ("decisions.md", DECISIONS), ("inbox.md", INBOX),
                       ("OVERVIEW.md", OVERVIEW), ("knowledge_index.md", "# 索引\n"),
                       ("reference.md", "# 参照\n- 锁的坑见 K-002\n"), ("conventions.md", "# 规约\n"),
                       ("config.yaml", 'review_last_full: "2026-09-30"\niron_rules:\n  - "锁要放 (.aip/knowledge.md::K-002)"\n')]:
        (a/name).write_text(text, encoding="utf-8")
    (a/"specs").mkdir()
    (a/"specs"/"lock.md").write_text("# 锁的设计\n依据 ADR-2\n", encoding="utf-8")
    (d/"src").mkdir()
    (d/"src"/"lock.py").write_text("# 见 .aip/knowledge.md::general_old_way_hangs 和 .aip/knowledge.md::K-002\n"
                                   "# 以及 .aip/knowledge.md::no_such_rule\n", encoding="utf-8")
    git(d, "init", "-q", "-b", "master"); git(d, "add", "."); git(d, "commit", "-q", "-m", "old")
    return d


def by_alias(items, alias):
    return next(i for i in items if alias in i.values("aliases"))


class Plan(unittest.TestCase):
    def setUp(self):
        self.d = old_repo()
        self.plan = mig.build_plan(self.d)
        self.items = self.plan.items

    def test_counts_and_template_examples_skipped(self):
        kinds = [i.type for i in self.items]
        self.assertEqual(kinds.count("knowledge"), 3)
        self.assertEqual(kinds.count("decision"), 2)          # 格式节里的 ADR-N 不算
        self.assertEqual(kinds.count("track"), 1)
        self.assertEqual(kinds.count("inbox"), 4)             # 3 条 + 看板遗留内容 1 条

    def test_knowledge_fields_move_to_head_and_status_note_kept(self):
        k2 = by_alias(self.items, "K-002")
        self.assertEqual(k2.status, "fixed")
        self.assertEqual(k2.meta["category"], "other")
        self.assertEqual(k2.meta["last_reviewed"], "2026-06-28")
        self.assertIn("状态说明（迁移前）: fixed（已修，2026-06-28）", k2.body)
        self.assertIn("**规则**：正文后面的段落也要带上。", k2.body)
        self.assertNotIn("- 分类:", k2.body)                  # 挪进文件头的字段不在正文重复
        k1 = by_alias(self.items, "K-001")
        self.assertEqual(k1.meta["rule_id"], "general_old_way_hangs")
        self.assertEqual(k1.meta["superseded_by"], k2.id)

    def test_old_ids_in_body_become_full_ids_twins_stay(self):
        k2 = by_alias(self.items, "K-002")
        full = f"{by_alias(self.items, 'K-001').id} / {by_alias(self.items, 'ADR-2').id} / I-2"
        self.assertIn(f"- 关联: {full}", k2.body)
        self.assertIn(by_alias(self.items, "K-002").id, by_alias(self.items, "K-001").body)  # 状态说明里的 K-002 也换了
        self.assertTrue(any("I-2" in n and "原样留着" in n for n in self.plan.notes))
        self.assertEqual(k2.meta["scope"], f"某模块（{by_alias(self.items, 'K-001').id} 的后继）")

    def test_superseded_without_target_is_flagged(self):
        k3 = by_alias(self.items, "K-003")
        self.assertEqual(k3.status, "superseded")
        self.assertTrue(k3.meta["superseded_by"])
        self.assertTrue(any("K-003" in n for n in self.plan.notes))

    def test_decisions_status(self):
        a1, a2 = by_alias(self.items, "ADR-1"), by_alias(self.items, "ADR-2")
        self.assertEqual((a1.status, a2.status), ("superseded", "accepted"))  # 「取代 ADR-1」不等于自己被取代
        self.assertEqual(a1.meta["superseded_by"], a2.id)

    def test_stamps_are_git_times_not_dates_written_in_the_entry(self):
        self.assertEqual(by_alias(self.items, "ADR-1").stamp, "20260615-120000")   # 正文写的 2026-04-01 不用
        self.assertTrue(all(i.stamp == "20260615-120000" for i in self.items if i.values("aliases")))

    def test_inbox_status_and_duplicate_old_id(self):
        self.assertEqual(by_alias(self.items, "I-1").status, "open")
        twins = [i for i in self.items if "I-2" in i.values("aliases")]
        self.assertEqual(sorted(i.status for i in twins), ["closed", "open"])
        self.assertTrue(any("I-2" in n and "撞号" in n for n in self.plan.notes))

    def test_board_track_and_leftovers(self):
        track = next(i for i in self.items if i.type == "track")
        self.assertEqual((track.status, track.title), ("active", "新布局（2026-10-01 开工）"))
        self.assertIn("下一步：写迁移", track.body)
        left = next(i for i in self.items if i.type == "inbox" and "看板" in i.title)
        self.assertIn("某条线做完了，还没部署", left.body)
        self.assertNotIn("顶部说明", left.body)
        self.assertNotIn("K-001 老办法", left.body)              # 自动摘要不搬

    def test_ids_unique(self):
        ids = [i.id for i in self.items]
        self.assertEqual(len(ids), len(set(ids)))

    def test_preview_writes_nothing(self):
        subprocess.run([sys.executable, str(SCRIPTS/"aip_migrate.py"), "--repo-root", str(self.d)],
                       check=True, capture_output=True)
        self.assertTrue((self.d/".aip"/"knowledge.md").exists())
        self.assertFalse((self.d/".aip"/"knowledge").exists())


class FirstSeen(unittest.TestCase):
    def test_edited_heading_and_moved_file_keep_the_first_time(self):
        d = old_repo()
        git(d, "mv", ".aip/inbox.md", "inbox-moved.md")
        git(d, "commit", "-q", "-m", "move", when="2026-06-20T08:00:00")
        git(d, "mv", "inbox-moved.md", ".aip/inbox.md")
        inbox = d/".aip"/"inbox.md"
        inbox.write_text(read(inbox).replace("## I-1：还没处理的问题", "## I-1：~~还没处理的问题~~")
                         + "\n## I-3：后来加的\n- 发现 / 状态：2026-07-01 / 待处理\n", encoding="utf-8")
        git(d, "commit", "-q", "-am", "edit", when="2026-07-01T09:30:05")
        items = mig.build_plan(d).items
        self.assertEqual(by_alias(items, "I-1").stamp, "20260615-120000")   # blame 会给 07-01
        self.assertEqual(by_alias(items, "I-3").stamp, "20260701-093005")


class Names(unittest.TestCase):
    LONG = "旧编号撞号的那条后来查清楚了，其实是两个完全不同的问题"

    def test_export_fill_and_read_back(self):
        d = old_repo()
        inbox = d/".aip"/"inbox.md"
        inbox.write_text(read(inbox) + f"\n## I-9：{self.LONG}\n- 发现 / 状态：2026-09-06 / 待处理\n", encoding="utf-8")
        # 提交进 git：没提交的条目时间戳取「现在」，导出和读回跨过一秒标识就对不上
        git(d, "commit", "-qam", "I-9")
        table = d/"names.tsv"
        r = subprocess.run([sys.executable, str(SCRIPTS/"aip_migrate.py"), "--repo-root", str(d), "--names-out", str(table)],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout)
        rows = [l.split("\t") for l in read(table).splitlines() if not l.startswith("#")]
        self.assertEqual([row[1] for row in rows], [self.LONG])
        table.write_text(read(table).replace(f"\t{rows[0][2]}\n", "\t撞号那条是两个问题\n"), encoding="utf-8")
        plan = mig.build_plan(d, mig.read_names(table))
        self.assertEqual(by_alias(plan.items, "I-9").slug, "撞号那条是两个问题")
        self.assertEqual(plan.unnamed, [])

    def test_bad_names_are_reported_not_used(self):
        d = old_repo()
        plan = mig.build_plan(d, {"20990101-000000_没有": "x", mig.build_plan(d).items[0].id: ""})
        self.assertEqual(sum("没用上" in n for n in plan.notes), 2)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


class Apply(unittest.TestCase):
    def run_migrate(self, d: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPTS/"aip_migrate.py"), "--repo-root", str(d), *extra],
                              capture_output=True, text=True, encoding="utf-8")

    def test_apply_passes_check_and_rewrites_anchors(self):
        d = old_repo()
        r = self.run_migrate(d, "--apply", "--rewrite-anchors")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for n in ("knowledge.md", "decisions.md", "inbox.md", "knowledge_index.md"):
            self.assertFalse((d/".aip"/n).exists(), n)
        self.assertEqual(chk.run_all(d), [])
        items = it.list_items(d)
        code = (d/"src"/"lock.py").read_text(encoding="utf-8")
        self.assertIn(f".aip/knowledge/{by_alias(items, 'K-001').id}", code)
        self.assertIn(f".aip/knowledge/{by_alias(items, 'K-002').id}", code)
        self.assertIn(".aip/knowledge.md::no_such_rule", code)   # 认不出的原样留着
        ref = (d/".aip"/"reference.md").read_text(encoding="utf-8")
        self.assertIn(f"锁的坑见 {by_alias(items, 'K-002').id}", ref)
        cfg = (d/".aip"/"config.yaml").read_text(encoding="utf-8")
        self.assertIn(f"锁要放 (.aip/knowledge/{by_alias(items, 'K-002').id})", cfg)   # 锚点整体换，不只换编号
        spec = (d/".aip"/"specs"/"lock.md").read_text(encoding="utf-8")
        self.assertIn(f"依据 {by_alias(items, 'ADR-2').id}", spec)
        self.assertIn("no_such_rule", r.stdout)
        tracked = subprocess.run(["git", "ls-files", ".aip/OVERVIEW.md"], cwd=d, capture_output=True, text=True).stdout
        self.assertEqual(tracked.strip(), "")                     # 旧看板连版本库记录一起删
        self.assertFalse((d/".aip"/"OVERVIEW.md").exists())

    def test_without_rewrite_flag_code_is_untouched(self):
        d = old_repo()
        self.run_migrate(d, "--apply")
        self.assertIn(".aip/knowledge.md::general_old_way_hangs", (d/"src"/"lock.py").read_text(encoding="utf-8"))

    def test_dirty_aip_refused_unless_allowed(self):
        d = old_repo()
        (d/".aip"/"inbox.md").write_text(INBOX + "\n## I-3：没提交的\n- 发现 / 状态：2026-09-05 / 待处理\n",
                                         encoding="utf-8")
        self.assertEqual(self.run_migrate(d, "--apply").returncode, 1)
        self.assertEqual(self.run_migrate(d, "--apply", "--allow-dirty").returncode, 0)
        self.assertTrue(any("I-3" in i.values("aliases") for i in it.list_items(d)))

    def test_half_migrated_refused(self):
        d = old_repo()
        it.new_item(d, "inbox", "已经有的条目", stamp="20261001-100000")
        r = self.run_migrate(d)
        self.assertEqual(r.returncode, 1)
        self.assertIn("迁过一半", r.stdout)

    def test_nothing_to_migrate(self):
        d = Path(tempfile.mkdtemp()); (d/".aip").mkdir()
        r = self.run_migrate(d, "--apply")
        self.assertEqual(r.returncode, 0)
        self.assertIn("不用迁移", r.stdout)


if __name__ == "__main__":
    unittest.main()
