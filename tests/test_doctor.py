import sys, tempfile, unittest
from datetime import date
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import aip_doctor as doc, aip_init


def levels(items):
    return [lv for lv, _, _ in items]


class ProjectHealth(unittest.TestCase):
    def test_uninitialized_repo_is_info_not_error(self):
        d = Path(tempfile.mkdtemp())
        items = doc.check_project(d, ROOT)
        self.assertEqual(levels(items), ["INFO"])

    def test_missing_living_doc_is_error_with_fix(self):
        d = Path(tempfile.mkdtemp())
        aip_init.scaffold(d, ROOT)
        import aip_knowledge, aip_overview
        aip_knowledge.rebuild_index(d); aip_overview.rebuild_overview(d)
        (d/".aip"/"decisions.md").unlink()
        items = doc.check_project(d, ROOT)
        self.assertIn("ERROR", levels(items))
        self.assertTrue(any("decisions.md" in msg for _, msg, _ in items))


class Freshness(unittest.TestCase):
    def _repo_with_entry(self, reviewed: str) -> Path:
        d = Path(tempfile.mkdtemp()); (d/".aip").mkdir()
        (d/".aip"/"knowledge.md").write_text(
            "# 知识库\n\n## 类目\nother\n\n"
            "## K-001: 条目\n- 分类: other\n- 状态: active\n- 症状: s\n- 根因: r\n"
            f"- 适用范围: a\n- 最后复核: {reviewed}\n", encoding="utf-8")
        return d

    def test_stale_entry_warns(self):
        d = self._repo_with_entry("2026-01-01")
        items = doc.check_knowledge_freshness(d, today=date(2026, 7, 1))
        self.assertEqual(levels(items), ["WARN"])

    def test_fresh_entry_silent(self):
        d = self._repo_with_entry("2026-06-20")
        self.assertEqual(doc.check_knowledge_freshness(d, today=date(2026, 7, 1)), [])

    def test_bad_date_warns(self):
        d = self._repo_with_entry("最近")
        items = doc.check_knowledge_freshness(d, today=date(2026, 7, 1))
        self.assertEqual(levels(items), ["WARN"])

    def test_stale_days_override(self):
        # 60 天前的条目：默认 90 天阈值不报，收紧到 30 天就报。
        d = self._repo_with_entry("2026-05-02")
        self.assertEqual(doc.check_knowledge_freshness(d, today=date(2026, 7, 1)), [])
        items = doc.check_knowledge_freshness(d, today=date(2026, 7, 1), stale_days=30)
        self.assertEqual(levels(items), ["WARN"])


class InstallHealth(unittest.TestCase):
    def test_missing_install_is_warn(self):
        home = Path(tempfile.mkdtemp())
        items = doc.check_install(home, ROOT)
        self.assertEqual(levels(items), ["WARN"])

    def test_version_mismatch_is_warn(self):
        home = Path(tempfile.mkdtemp())
        installed = home/"plugins"/doc.PLUGIN_NAME
        installed.mkdir(parents=True)
        (installed/"VERSION").write_text("0.0.1\n", encoding="utf-8")
        for skill in ["aip", "root-cause"]:
            for base in [".claude", ".agents"]:
                p = home/base/"skills"/skill
                p.mkdir(parents=True)
                (p/"SKILL.md").write_text("x", encoding="utf-8")
        items = doc.check_install(home, ROOT)
        self.assertTrue(any("版本不一致" in msg and lv == "WARN" for lv, msg, _ in items))


class EngineRepoHealth(unittest.TestCase):
    def test_own_repo_is_clean(self):
        # 引擎仓库自身：双副本与 VERSION 必须同步（红了说明忘跑 sync_plugin.py）。
        self.assertEqual(doc.check_engine_repo(ROOT), [])

    def test_non_engine_repo_skipped(self):
        d = Path(tempfile.mkdtemp())
        self.assertEqual(doc.check_engine_repo(d), [])


if __name__ == "__main__":
    unittest.main()
