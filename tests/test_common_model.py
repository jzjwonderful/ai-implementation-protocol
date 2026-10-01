import sys, unittest
from pathlib import Path
from _engine import ROOT, ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import _aip_common as c

class CommonModel(unittest.TestCase):
    def test_project_files_and_item_layout(self):
        self.assertEqual(c.PROJECT_FILES, ["reference.md", "conventions.md", "config.yaml"])
        self.assertEqual(c.OLD_BOARD_FILE, "OVERVIEW.md")
        self.assertEqual(c.OLD_LAYOUT_FILES, ["knowledge.md", "decisions.md", "inbox.md", "knowledge_index.md"])
    def test_forbidden_covers_residue_and_old_names(self):
        for name in ["current_task.json","task_board.yaml","handoff.md",
                     "STATUS.md","findings.md","canonical-assets.md"]:
            self.assertIn(name, c.FORBIDDEN_SLOT_FILENAMES)
    def test_old_helpers_removed(self):
        for a in ["REQUIRED_FEATURE_FILES","REQUIRED_BUG_FILES",
                  "AIP_SLOT_FILENAMES","feature_dir","current_task_path",
                  "PROJECT_LIVING_FILES","REQUIRED_KNOWLEDGE_FIELDS","project_docs_root"]:
            self.assertFalse(hasattr(c, a), f"{a} 应已删除")

if __name__ == "__main__":
    unittest.main()
