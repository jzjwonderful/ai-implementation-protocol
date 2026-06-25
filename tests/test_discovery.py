import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import aip_discovery as disc

class Discovery(unittest.TestCase):
    def test_bootstrap_is_new_model(self):
        b = disc.managed_block()
        self.assertIn("OVERVIEW.md", b)
        self.assertNotIn("current_task.json", b)
        self.assertNotIn("STATUS.md", b)
    def test_upsert_block_custom_markers_idempotent(self):
        d = Path(tempfile.mkdtemp()); p = d/"x.md"
        p.write_text("手写在上\n", encoding="utf-8")
        disc.upsert_block(p, "AUTO 内容\n", "<!--A-->", "<!--/A-->")
        disc.upsert_block(p, "AUTO 内容2\n", "<!--A-->", "<!--/A-->")
        t = p.read_text(encoding="utf-8")
        self.assertIn("手写在上", t)            # 手写区保留
        self.assertIn("AUTO 内容2", t)          # 只替换标记区
        self.assertNotIn("AUTO 内容\n", t.replace("AUTO 内容2", ""))
        self.assertEqual(t.count("<!--A-->"), 1)  # 不重复

if __name__ == "__main__":
    unittest.main()
