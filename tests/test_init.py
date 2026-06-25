import sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import aip_init, _aip_common as c

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

class Hooks(unittest.TestCase):
    def test_hook_targets_check_not_router(self):
        import install_hooks
        body = install_hooks.pre_commit_body(ROOT)
        self.assertIn("aip_check.py", body)
        self.assertNotIn("aip.py", body)

if __name__ == "__main__":
    unittest.main()
