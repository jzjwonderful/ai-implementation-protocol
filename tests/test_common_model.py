import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import _aip_common as c

class CommonModel(unittest.TestCase):
    def test_living_files_new_set(self):
        self.assertEqual(c.PROJECT_LIVING_FILES, [
            "OVERVIEW.md","decisions.md","knowledge.md","knowledge_index.md",
            "reference.md","inbox.md","conventions.md","config.yaml"])
    def test_forbidden_covers_residue_and_old_names(self):
        for name in ["current_task.json","task_board.yaml","handoff.md",
                     "STATUS.md","findings.md","canonical-assets.md"]:
            self.assertIn(name, c.FORBIDDEN_SLOT_FILENAMES)
    def test_required_knowledge_fields(self):
        self.assertEqual(c.REQUIRED_KNOWLEDGE_FIELDS,
            ["分类","状态","症状","根因","适用范围","最后复核"])
    def test_old_helpers_removed(self):
        for a in ["REQUIRED_FEATURE_FILES","REQUIRED_BUG_FILES",
                  "AIP_SLOT_FILENAMES","feature_dir","current_task_path"]:
            self.assertFalse(hasattr(c, a), f"{a} 应已删除")

if __name__ == "__main__":
    unittest.main()
