import subprocess, sys, tempfile, unittest
from pathlib import Path
from _engine import ROOT, ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_init, aip_discovery as disc, _aip_common as c, aip_item as it

class Init(unittest.TestCase):
    def test_scaffold_creates_docs_item_dirs_and_ignore(self):
        d = Path(tempfile.mkdtemp())
        aip_init.scaffold(d, ENGINE)
        for n in c.PROJECT_FILES:
            self.assertTrue((d/".aip"/n).exists(), f"{n} 未建")
        for t in it.TYPES.values():
            self.assertTrue((d/".aip"/t.folder/".gitkeep").exists(), t.folder)
        self.assertEqual((d/".aip"/".gitignore").read_text(encoding="utf-8"), "OVERVIEW.md\n")
    def test_new_config_starts_review_clock_today(self):
        from datetime import date
        import aip_upkeep
        d = Path(tempfile.mkdtemp())
        aip_init.scaffold(d, ENGINE)
        cfg = (d/".aip"/"config.yaml").read_text(encoding="utf-8")
        self.assertIn(f'review_last_full: "{date.today().isoformat()}"', cfg)
        self.assertEqual(aip_upkeep.last_full_review(d), (True, date.today()))
    def test_idempotent_and_keeps_existing_ignore_lines(self):
        d = Path(tempfile.mkdtemp())
        (d/".aip").mkdir(); (d/".aip"/".gitignore").write_text("scratch/\n", encoding="utf-8")
        aip_init.scaffold(d, ENGINE)
        aip_init.scaffold(d, ENGINE)
        self.assertEqual((d/".aip"/".gitignore").read_text(encoding="utf-8"), "scratch/\nOVERVIEW.md\n")
    def test_old_layout_refuses_and_points_to_migration(self):
        d = Path(tempfile.mkdtemp()); (d/".aip").mkdir()
        (d/".aip"/"knowledge.md").write_text("# 旧\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPTS/"aip_init.py"), "--repo-root", str(d), "--no-hooks"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 1)
        self.assertIn("aip_migrate.py", r.stdout)
        self.assertFalse((d/".aip"/"inbox").exists())

class UpgradeSafety(unittest.TestCase):
    def test_refill_never_overwrites_any_doc(self):
        # 模拟「AI 阶段 B 已填充过」的项目再跑 init：每份文档都不许被打回模板。
        d = Path(tempfile.mkdtemp())
        aip_init.scaffold(d, ENGINE)
        for n in c.PROJECT_FILES:
            (d/".aip"/n).write_text(f"# 用户内容 {n}\n", encoding="utf-8")
        aip_init.scaffold(d, ENGINE)
        for n in c.PROJECT_FILES:
            self.assertEqual((d/".aip"/n).read_text(encoding="utf-8"),
                             f"# 用户内容 {n}\n", f"{n} 被覆盖")

class ManagedBlock(unittest.TestCase):
    def test_upsert_idempotent_and_preserves_user_text(self):
        d = Path(tempfile.mkdtemp()); guide = d/"CLAUDE.md"
        guide.write_text("# 项目自述\n用户手写内容\n", encoding="utf-8")
        disc.upsert_managed_block(guide)
        disc.upsert_managed_block(guide)
        t = guide.read_text(encoding="utf-8")
        self.assertIn("用户手写内容", t)
        self.assertEqual(t.count(disc.BEGIN), 1)
        self.assertEqual(t.count(disc.END), 1)
        self.assertIn("AIP managed version: 3", t)
        self.assertIn("验收矩阵", t)

    def test_existing_managed_block_is_upgraded(self):
        d = Path(tempfile.mkdtemp()); guide = d/"AGENTS.md"
        guide.write_text(
            "# 项目规则\n\n"
            "<!-- BEGIN AIP (managed) -->\n"
            "旧版 AIP 引导\n"
            "<!-- END AIP (managed) -->\n\n"
            "项目自己的规则\n",
            encoding="utf-8")
        disc.upsert_managed_block(guide)
        t = guide.read_text(encoding="utf-8")
        self.assertIn("AIP managed version: 3", t)
        self.assertIn("行为证据", t)
        self.assertNotIn("旧版 AIP 引导", t)
        self.assertIn("项目自己的规则", t)
        self.assertEqual(t.count(disc.BEGIN), 1)
        self.assertEqual(t.count(disc.END), 1)
    def test_created_when_missing(self):
        d = Path(tempfile.mkdtemp()); guide = d/"AGENTS.md"
        disc.upsert_managed_block(guide)
        self.assertIn("OVERVIEW.md", guide.read_text(encoding="utf-8"))

class Hooks(unittest.TestCase):
    def test_hook_targets_check_not_router(self):
        import install_hooks
        body = install_hooks.pre_commit_body(ROOT)
        self.assertIn("aip_check.py", body)
        self.assertIn("--no-reminders", body)   # 提交前不算到期提醒
        self.assertNotIn("aip.py", body)

if __name__ == "__main__":
    unittest.main()
