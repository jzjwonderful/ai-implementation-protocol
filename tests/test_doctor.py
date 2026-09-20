import sys, tempfile, unittest
from datetime import date
from pathlib import Path
from _engine import ROOT, ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_doctor as doc, aip_init
from _aip_common import SKILL_NAMES


def levels(items):
    return [lv for lv, _, _ in items]


class ProjectHealth(unittest.TestCase):
    def test_uninitialized_repo_is_info_not_error(self):
        d = Path(tempfile.mkdtemp())
        items = doc.check_project(d, ENGINE)
        self.assertEqual(levels(items), ["INFO"])

    def test_missing_living_doc_is_error_with_fix(self):
        d = Path(tempfile.mkdtemp())
        aip_init.scaffold(d, ENGINE)
        import aip_knowledge, aip_overview
        aip_knowledge.rebuild_index(d); aip_overview.rebuild_overview(d)
        (d/".aip"/"decisions.md").unlink()
        items = doc.check_project(d, ENGINE)
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
    def _skill(self, base: Path, name: str, version: str | None = None, scripts: bool = True) -> Path:
        p = base/"skills"/name
        p.mkdir(parents=True, exist_ok=True)
        (p/"SKILL.md").write_text("x", encoding="utf-8")
        if scripts:
            (p/"scripts").mkdir(exist_ok=True)
            (p/"scripts"/"aip_init.py").write_text("x", encoding="utf-8")
        if version is not None:
            (p/"VERSION").write_text(version + "\n", encoding="utf-8")
        return p

    def _engine_version(self) -> str:
        return (ENGINE/"VERSION").read_text(encoding="utf-8").strip()

    def test_missing_install_is_warn(self):
        home = Path(tempfile.mkdtemp())
        items = doc.check_install(home, ENGINE)
        self.assertIn("WARN", levels(items))
        self.assertTrue(any("Claude 技能未安装" in msg for _, msg, _ in items))

    def test_old_layout_without_scripts_is_warn(self):
        home = Path(tempfile.mkdtemp())
        for skill in SKILL_NAMES:
            self._skill(home/".claude", skill, version=self._engine_version(), scripts=False)
        items = doc.check_install(home, ENGINE)
        self.assertTrue(any("旧版布局" in msg and lv == "WARN" for lv, msg, _ in items))

    def test_version_mismatch_is_warn(self):
        home = Path(tempfile.mkdtemp())
        for skill in SKILL_NAMES:
            for base in [".claude", ".agents", ".grok"]:
                self._skill(home/base, skill, version="0.0.1")
        items = doc.check_install(home, ENGINE)
        self.assertTrue(any("版本不一致" in msg and lv == "WARN" for lv, msg, _ in items))
        # 三端技能都装了时，不应再提示某端 skill 缺失
        self.assertFalse(any("技能未安装" in msg for _, msg, _ in items))

    def test_matching_install_is_clean(self):
        home = Path(tempfile.mkdtemp())
        for skill in SKILL_NAMES:
            self._skill(home/".claude", skill, version=self._engine_version())
            self._skill(home/".codex", skill, version=self._engine_version())
            self._skill(home/".grok", skill, version=self._engine_version())
        self.assertEqual(doc.check_install(home, ENGINE, codex_home=home/".codex"), [])

    def test_codex_home_skill_counts_as_installed(self):
        home = Path(tempfile.mkdtemp())
        for skill in SKILL_NAMES:
            self._skill(home/".claude", skill, version=self._engine_version())
            self._skill(home/".codex", skill, version=self._engine_version())
        items = doc.check_install(home, ENGINE, codex_home=home/".codex")
        self.assertFalse(any("Codex 技能未安装" in msg for _, msg, _ in items))


class EngineRepoHealth(unittest.TestCase):
    def test_own_repo_is_clean(self):
        # 引擎仓库自身：两份 plugin.json 的 version 必须和 skills/aip/VERSION 一致。
        self.assertEqual(doc.check_engine_repo(ROOT), [])

    def test_non_engine_repo_skipped(self):
        d = Path(tempfile.mkdtemp())
        self.assertEqual(doc.check_engine_repo(d), [])


if __name__ == "__main__":
    unittest.main()
