"""0.8.3：按 tech-ai-kits 的真实规模（227 条知识、回放 60 个提交）量出来的三处改法。

- 到期提醒里不再报「代码改过」，改到那个文件时由反查就地提示（测在 test_upkeep_git / test_fix082）。
- 反查按轻重排、每类限量、整体封顶，标题截断。
- 按关键词查连正文一起查，正文命中单独列、带上命中那句。
"""
import subprocess, sys, unittest
from pathlib import Path
from _engine import SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_item as it, aip_lookup as lk
from test_fix081 import knowledge, make_repo, topic


def run(d: Path, *args: str) -> str:
    r = subprocess.run([sys.executable, str(SCRIPTS / "aip_lookup.py"), "--repo-root", str(d), "relevant", *args],
                       capture_output=True, text=True, encoding="utf-8", check=True)
    return r.stdout


def item(d: Path, type_name: str, title: str, paths: str, stamp: str, status: str | None = None) -> it.Item:
    meta = {"paths": paths}
    if type_name == "knowledge":
        meta.update(category="c", scope="s")
        status = status or "active"
    return it.new_item(d, type_name, title, status, stamp=stamp, meta=meta)


class Order(unittest.TestCase):
    """主题资料 → 改动处的锚点 → 验证过的坑 → 钦定实现 → 决策 → 旁路问题。"""

    def repo(self) -> Path:
        d = make_repo()
        (d / "src").mkdir()
        (d / "src" / "a.py").write_text("# 见 .aip/knowledge/20260901-100000_锚点指的坑\n", encoding="utf-8")
        topic(d, "后端", "## 规约\n- x\n", paths="src/")
        knowledge(d, "锚点指的坑", stamp="20260901-100000")
        item(d, "knowledge", "按路径命中的坑", "src/a.py", "20260902-100000")
        item(d, "reuse", "钦定的 HTTP 客户端", "src/a.py", "20260903-100000")
        item(d, "decision", "为什么这么定", "src/a.py", "20260904-100000")
        item(d, "inbox", "顺手记的旁路问题", "src/a.py", "20260905-100000")
        return d

    def test_ranks_in_order(self):
        hits = lk.relevant(self.repo(), ["src/a.py"])[0]
        self.assertEqual([h.rank for h in hits], sorted(h.rank for h in hits))
        order = [Path(h.target).name for h in hits]
        self.assertTrue(order[0].startswith("后端"), order)
        self.assertIn("锚点指的坑", order[1])
        self.assertIn("按路径命中的坑", order[2])
        self.assertIn("钦定的", order[3])
        self.assertIn("为什么这么定", order[4])
        self.assertIn("顺手记的旁路问题", order[5])


class Cap(unittest.TestCase):
    def repo(self, n: int, type_name: str = "knowledge") -> Path:
        d = make_repo()
        (d / "src").mkdir()
        (d / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        for i in range(n):
            item(d, type_name, f"第 {i} 条", "src/a.py", f"20260901-1000{i:02d}")
        return d

    def test_one_class_alone_still_fills_the_budget(self):
        """只有一类相关时，名额不能白留着。"""
        d = self.repo(20)
        self.assertEqual(len(lk.pick(lk.relevant(d, ["src/a.py"])[0])), lk.RELEVANT_LIMIT)

    def test_only_the_top_ones_are_listed(self):
        d = self.repo(20)
        hits = lk.relevant(d, ["src/a.py"])[0]
        self.assertEqual(len(hits), 20)                      # 反查本身照常全算
        out = run(d, "src/a.py")
        self.assertEqual(out.count(".aip/knowledge/"), lk.RELEVANT_LIMIT)  # 只列最要紧的几条
        self.assertIn("还有", out)

    def test_all_prints_everything(self):
        d = self.repo(20)
        out = run(d, "src/a.py", "--all")
        self.assertEqual(out.count(".aip/knowledge/"), 20)
        self.assertNotIn("还有", out)

    def test_one_class_cannot_eat_the_whole_budget(self):
        """一个文件上光 active 知识就能命中十几条时，也要给主题和别的类留名额。"""
        d = self.repo(20)
        topic(d, "后端", "## 规约\n- x\n", paths="src/")
        item(d, "reuse", "钦定实现", "src/a.py", "20261001-100000")
        shown = lk.pick(lk.relevant(d, ["src/a.py"])[0])
        kinds = [h.rank for h in shown]
        self.assertEqual(len(shown), lk.RELEVANT_LIMIT)
        self.assertIn(lk.RANK_TOPIC, kinds)                      # 主题资料没被挤掉
        self.assertIn(lk.RANK["reuse", "active"], kinds)          # 钦定实现也没被挤掉
        self.assertGreaterEqual(kinds.count(lk.RANK["knowledge", "active"]),
                                lk.CLASS_LIMIT[lk.RANK["knowledge", "active"]])

    def test_long_title_is_cut_but_all_keeps_it(self):
        long = "标" * (lk.TITLE_LIMIT + 10)
        h = lk.Hit("x.md", long, "涉及 a.py")
        self.assertIn("…", h.line())
        self.assertLess(len(h.line(full=False)), len(h.line(full=True)))
        self.assertIn(long, h.line(full=True))


class StaleOnlyForActive(unittest.TestCase):
    def test_fixed_knowledge_gets_no_review_note(self):
        d = make_repo()
        (d / "src").mkdir()
        (d / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        k = item(d, "knowledge", "已修的坑", "src/a.py", "20260901-100000")
        it.set_status(d, k.id, "fixed")
        self.assertFalse(any("改过" in h.reason for h in lk.relevant(d, ["src/a.py"])[0]))


class Grep(unittest.TestCase):
    def repo(self) -> Path:
        d = make_repo()
        knowledge(d, "标题里就有超时", stamp="20260901-100000")
        knowledge(d, "标题里没有", body="- 症状: 读盘超时会重试\n- 根因: y\n", stamp="20260902-100000")
        knowledge(d, "毫不相关", stamp="20260903-100000")
        return d

    def test_body_hits_are_separate_and_carry_the_line(self):
        d = self.repo()
        head, body = it.search(it.list_items(d, "knowledge"), "超时")
        self.assertEqual([h.slug for h in head], ["标题里就有超时"])
        self.assertEqual([i.slug for i, _ in body], ["标题里没有"])
        self.assertIn("超时", body[0][1])

    def test_case_insensitive_and_no_duplicates(self):
        d = make_repo()
        knowledge(d, "Kite 的坑", body="- 症状: kite 挂了\n- 根因: y\n", stamp="20260901-100000")
        head, body = it.search(it.list_items(d, "knowledge"), "KITE")
        self.assertEqual(len(head), 1)
        self.assertEqual(body, [])

    def test_cli_lists_body_hits_under_a_header(self):
        d = self.repo()
        r = subprocess.run([sys.executable, str(SCRIPTS / "aip_item.py"), "--repo-root", str(d), "list",
                            "--type", "knowledge", "--grep", "超时"],
                           capture_output=True, text=True, encoding="utf-8", check=True)
        self.assertIn("只在正文里提到", r.stdout)
        self.assertIn("标题里没有", r.stdout)


if __name__ == "__main__":
    unittest.main()
