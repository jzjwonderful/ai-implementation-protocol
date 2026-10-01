import sys, tempfile, unittest
from pathlib import Path
from _engine import ROOT, ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_doctor as doc, aip_init, aip_item as it
from _aip_common import SKILL_NAMES


def levels(items):
    return [lv for lv, _, _ in items]


class ProjectHealth(unittest.TestCase):
    def test_uninitialized_repo_is_info_not_error(self):
        d = Path(tempfile.mkdtemp())
        items = doc.check_project(d, ENGINE)
        self.assertEqual(levels(items), ["INFO"])

    def test_missing_doc_is_error_with_fix(self):
        d = Path(tempfile.mkdtemp())
        aip_init.scaffold(d, ENGINE)
        (d/".aip"/"reference.md").unlink()
        items = doc.check_project(d, ENGINE)
        self.assertIn("ERROR", levels(items))
        self.assertTrue(any("reference.md" in msg for _, msg, _ in items))

    def test_old_layout_is_error_pointing_to_migration(self):
        d = Path(tempfile.mkdtemp()); (d/".aip").mkdir()
        (d/".aip"/"knowledge.md").write_text("# 旧\n", encoding="utf-8")
        items = doc.check_project(d, ENGINE)
        self.assertEqual(set(levels(items)), {"ERROR"})
        self.assertTrue(all("aip_migrate.py" in fix for _, _, fix in items))


class DueSummary(unittest.TestCase):
    def test_many_due_items_are_one_warn_line(self):
        d = Path(tempfile.mkdtemp())
        aip_init.scaffold(d, ENGINE)
        for n in range(12):
            it.new_item(d, "knowledge", f"老坑{n}", "active", stamp=f"20260101-1000{n:02d}",
                        meta={"category": "other", "scope": "w", "last_reviewed": "2026-01-01"},
                        body="- 症状: x\n- 根因: y\n")
        items = doc.check_project(d, ENGINE)
        self.assertEqual(levels(items), ["WARN"])
        self.assertIn("12 项", items[0][1]); self.assertIn("--all", items[0][2])

    def test_nothing_due_is_silent(self):
        d = Path(tempfile.mkdtemp())
        aip_init.scaffold(d, ENGINE)
        self.assertEqual(doc.check_project(d, ENGINE), [])


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

    def test_retired_skill_still_installed_is_warn(self):
        home = Path(tempfile.mkdtemp())
        for skill in SKILL_NAMES:
            self._skill(home/".claude", skill, version=self._engine_version())
        self._skill(home/".claude", "root-cause")
        self._skill(home/".agents", "aip-brainstorm")
        warns = [msg for lv, msg, _ in doc.check_install(home, ENGINE) if lv == "WARN"]
        self.assertTrue(any("root-cause" in m and "还装着" in m for m in warns), warns)
        self.assertTrue(any("aip-brainstorm" in m and "还装着" in m for m in warns), warns)

    def test_codex_home_skill_counts_as_installed(self):
        home = Path(tempfile.mkdtemp())
        for skill in SKILL_NAMES:
            self._skill(home/".claude", skill, version=self._engine_version())
            self._skill(home/".codex", skill, version=self._engine_version())
        items = doc.check_install(home, ENGINE, codex_home=home/".codex")
        self.assertFalse(any("Codex 技能未安装" in msg for _, msg, _ in items))

    def test_project_install_counts_and_no_global_needed(self):
        home, repo = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
        for skill in SKILL_NAMES:
            self._skill(repo/".claude", skill, version=self._engine_version())
            self._skill(repo/".codex", skill, version=self._engine_version())
        items = doc.check_install(home, ENGINE, codex_home=home/".codex", repo=repo)
        self.assertEqual([lv for lv, msg, _ in items if "Grok" not in msg], [])

    def test_missing_everywhere_recommends_project_install(self):
        home, repo = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
        items = doc.check_install(home, ENGINE, repo=repo)
        fix = next(fix for _, msg, fix in items if "Claude 技能未安装" in msg)
        self.assertIn(f"--project {repo}", fix)

    def test_project_install_version_mismatch_is_warn(self):
        home, repo = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
        self._skill(repo/".claude", "aip", version="0.0.1")
        items = doc.check_install(home, ENGINE, repo=repo)
        self.assertTrue(any("项目级" in msg and "版本不一致" in msg for _, msg, _ in items), items)


class EngineRepoHealth(unittest.TestCase):
    def test_own_repo_is_clean(self):
        # 引擎仓库自身：两份 plugin.json 的 version 必须和 skills/aip/VERSION 一致。
        self.assertEqual(doc.check_engine_repo(ROOT), [])

    def test_non_engine_repo_skipped(self):
        d = Path(tempfile.mkdtemp())
        self.assertEqual(doc.check_engine_repo(d), [])


if __name__ == "__main__":
    unittest.main()
