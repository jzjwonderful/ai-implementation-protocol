import sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import aip_check as chk, aip_knowledge as k

def make_repo() -> Path:
    d = Path(tempfile.mkdtemp()); aip = d/".aip"; aip.mkdir()
    for n in ["OVERVIEW.md","decisions.md","reference.md","inbox.md","conventions.md","config.yaml"]:
        (aip/n).write_text("# stub\n", encoding="utf-8")
    (aip/"knowledge.md").write_text("# 知识库\n\n## 类目\nother\n", encoding="utf-8")
    (aip/"knowledge_index.md").write_text(k.expected_index_text(d), encoding="utf-8")
    return d

class LivingAndIndex(unittest.TestCase):
    def test_clean_passes(self):
        d = make_repo()
        self.assertEqual(chk.check_living_files(d), [])
        self.assertEqual(chk.check_index_sync(d), [])
    def test_missing_living(self):
        d = make_repo(); (d/".aip"/"decisions.md").unlink()
        self.assertTrue(any("decisions.md" in v for v in chk.check_living_files(d)))
    def test_stale_index(self):
        d = make_repo(); (d/".aip"/"knowledge_index.md").write_text("# 旧\n", encoding="utf-8")
        self.assertTrue(chk.check_index_sync(d))

if __name__ == "__main__":
    unittest.main()
