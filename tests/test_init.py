import sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import aip_init, aip_discovery as disc, _aip_common as c

class Init(unittest.TestCase):
    def test_scaffold_creates_living_docs_no_prompt(self):
        d = Path(tempfile.mkdtemp())
        aip_init.scaffold(d, ROOT)
        for n in c.PROJECT_LIVING_FILES:
            self.assertTrue((d/".aip"/n).exists(), f"{n} 未建")
        # 零配置：config 存在但不含被追问的工程信息（留空骨架）
        self.assertTrue((d/".aip"/"config.yaml").exists())
    def test_idempotent(self):
        d = Path(tempfile.mkdtemp())
        aip_init.scaffold(d, ROOT)
        (d/".aip"/"OVERVIEW.md").write_text("# 我改过\n", encoding="utf-8")
        aip_init.scaffold(d, ROOT)  # 再跑不应覆盖已存在的
        self.assertIn("我改过", (d/".aip"/"OVERVIEW.md").read_text(encoding="utf-8"))

class UpgradeSafety(unittest.TestCase):
    def test_refill_never_overwrites_any_living_doc(self):
        # 模拟「AI 阶段 B 已填充过」的项目再跑 init：每个活文档都不许被打回模板。
        d = Path(tempfile.mkdtemp())
        aip_init.scaffold(d, ROOT)
        for n in c.PROJECT_LIVING_FILES:
            (d/".aip"/n).write_text(f"# 用户内容 {n}\n", encoding="utf-8")
        aip_init.scaffold(d, ROOT)
        for n in c.PROJECT_LIVING_FILES:
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
    def test_created_when_missing(self):
        d = Path(tempfile.mkdtemp()); guide = d/"AGENTS.md"
        disc.upsert_managed_block(guide)
        self.assertIn("OVERVIEW.md", guide.read_text(encoding="utf-8"))

class Hooks(unittest.TestCase):
    def test_hook_targets_check_not_router(self):
        import install_hooks
        body = install_hooks.pre_commit_body(ROOT)
        self.assertIn("aip_check.py", body)
        self.assertNotIn("aip.py", body)

if __name__ == "__main__":
    unittest.main()
