import sys, tempfile, unittest
from pathlib import Path
from _engine import ROOT, ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_overview as ov, aip_item as it


def repo() -> Path:
    d = Path(tempfile.mkdtemp()); a = d/".aip"; a.mkdir()
    (a/"reference.md").write_text("# 参照\n\n## 领域概念\n### 订单\n说明\n", encoding="utf-8")
    it.new_item(d, "track", "在做的线", body="- 下一步: 写测试\n", stamp="20261001-100000")
    it.new_item(d, "track", "等人的线", "blocked", stamp="20261001-090000")
    it.new_item(d, "track", "做完的线", "done", stamp="20260901-100000")
    it.new_item(d, "knowledge", "某坑", "active", stamp="20260901-100000",
                meta={"category": "other", "scope": "w", "last_reviewed": "2026-09-30"})
    it.new_item(d, "knowledge", "旧坑", "fixed", stamp="20260101-100000",
                meta={"category": "other", "scope": "w", "last_reviewed": "2026-01-01"})
    it.new_item(d, "decision", "选文件不选数据库", stamp="20261001-100000")
    it.new_item(d, "decision", "被取代的决策", "superseded", stamp="20260101-100000")
    it.new_item(d, "inbox", "没处理的问题", stamp="20261001-100000")
    it.new_item(d, "inbox", "关掉的问题", "closed", stamp="20261001-100000")
    return d


class Overview(unittest.TestCase):
    def test_board_is_built_from_items(self):
        t = ov.build_overview(repo())
        self.assertIn("### ▶ 在做的线", t); self.assertIn("- 下一步: 写测试", t)
        self.assertIn("### ⛔ 等人的线", t)
        self.assertLess(t.index("在做的线"), t.index("等人的线"))   # 进行中的排在前面
        self.assertNotIn("做完的线", t)
        self.assertIn("待处理的旁路问题（1 条）", t); self.assertIn("没处理的问题", t); self.assertNotIn("关掉的问题", t)
        self.assertIn("active 1 / draft 0 / fixed 1 / superseded 0", t)
        self.assertIn("20260901-100000_某坑", t); self.assertNotIn("旧坑", t)
        self.assertIn("选文件不选数据库", t); self.assertNotIn("被取代的决策", t)
        self.assertIn("领域概念（1）", t)

    def test_sections_are_capped(self):
        d = repo()
        for n in range(ov.INBOX_LIMIT + 3):
            it.new_item(d, "inbox", f"问题{n}", stamp=f"20260901-1000{n:02d}")
        t = ov.build_overview(d)
        self.assertIn("还有 4 条", t)

    def test_rebuild_writes_the_file(self):
        d = repo()
        p = ov.rebuild_overview(d)
        self.assertEqual(p, d/".aip"/"OVERVIEW.md")
        self.assertIn("在做的线", p.read_text(encoding="utf-8"))

    def test_empty_repo(self):
        d = Path(tempfile.mkdtemp()); (d/".aip").mkdir()
        t = ov.build_overview(d)
        self.assertIn("当前没有在建线", t); self.assertIn("（无）", t)

if __name__ == "__main__":
    unittest.main()
