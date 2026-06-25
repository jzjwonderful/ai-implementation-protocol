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

class KnowledgeFields(unittest.TestCase):
    def test_missing_field(self):
        d = make_repo()
        (d/".aip"/"knowledge.md").write_text(
            "# k\n\n## 类目\nother\n\n## K-001: 缺字段\n- 分类: other\n- 状态: draft\n", encoding="utf-8")
        self.assertTrue(any("K-001" in v and "适用范围" in v for v in chk.check_knowledge_fields(d)))
    def test_full_entry_ok(self):
        d = make_repo()
        (d/".aip"/"knowledge.md").write_text(
            "# k\n\n## 类目\nother\n\n## K-001: 全\n- 分类: other\n- 状态: active\n- 症状: x\n"
            "- 根因: y\n- 证据: z\n- 适用范围: w\n- 最后复核: 2026-06-25\n", encoding="utf-8")
        self.assertEqual(chk.check_knowledge_fields(d), [])

class OrphanSlots(unittest.TestCase):
    def test_flags_old_file(self):
        d = make_repo(); (d/".aip"/"handoff.md").write_text("x\n", encoding="utf-8")
        self.assertTrue(any("handoff.md" in v for v in chk.check_no_orphan_slots(d)))
    def test_clean_ok(self):
        self.assertEqual(chk.check_no_orphan_slots(make_repo()), [])

class DualCopy(unittest.TestCase):
    def _mk(self):
        d = make_repo(); (d/"scripts").mkdir()
        (d/"scripts"/"a.py").write_text("print(1)\n", encoding="utf-8")
        pl = d/"plugins"/"ai-implementation-protocol"/"scripts"; pl.mkdir(parents=True)
        (pl/"a.py").write_text("print(1)\n", encoding="utf-8"); return d
    def test_match_ok(self):
        self.assertEqual(chk.check_dual_copy(self._mk()), [])
    def test_drift(self):
        d = self._mk()
        (d/"plugins"/"ai-implementation-protocol"/"scripts"/"a.py").write_text("print(2)\n", encoding="utf-8")
        self.assertTrue(any("a.py" in v for v in chk.check_dual_copy(d)))
    def test_missing_mirror(self):
        d = self._mk(); (d/"scripts"/"b.py").write_text("x\n", encoding="utf-8")
        self.assertTrue(any("b.py" in v for v in chk.check_dual_copy(d)))

if __name__ == "__main__":
    unittest.main()
