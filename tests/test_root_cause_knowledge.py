import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AIP = REPO / "scripts" / "aip.py"


def run(*args):
    return subprocess.run([sys.executable, str(AIP), *args], capture_output=True, text=True)


def init_repo() -> Path:
    d = Path(tempfile.mkdtemp())
    r = run("init", "--repo-root", str(d))
    assert r.returncode == 0, r.stderr
    return d


class KnowledgeMechanism(unittest.TestCase):
    def test_init_creates_knowledge_and_index_in_must_read(self):
        d = init_repo()
        self.assertTrue((d / ".aip/knowledge.md").exists())
        self.assertTrue((d / ".aip/knowledge_index.md").exists())
        ct = json.loads((d / ".aip/_runtime/current_task.json").read_text(encoding="utf-8"))
        self.assertIn(".aip/knowledge_index.md", ct["must_read"])

    def test_knowledge_rebuild_is_idempotent_and_indexes_entries(self):
        d = init_repo()
        kn = d / ".aip/knowledge.md"
        kn.write_text(
            kn.read_text(encoding="utf-8")
            + "\n## K-001: 杀进程后仍 running\n- 分类: process-lifecycle\n- 状态: active\n"
            "- 症状: x\n- 根因: y\n- 最后复核: 2026-06-16\n",
            encoding="utf-8",
        )
        self.assertEqual(run("knowledge", "--repo-root", str(d)).returncode, 0)
        idx = (d / ".aip/knowledge_index.md").read_text(encoding="utf-8")
        self.assertIn("K-001 | process-lifecycle | active | 杀进程后仍 running | 2026-06-16", idx)

    def test_check_fails_on_stale_index(self):
        d = init_repo()
        kn = d / ".aip/knowledge.md"
        kn.write_text(
            kn.read_text(encoding="utf-8")
            + "\n## K-001: t\n- 分类: ui\n- 状态: active\n- 症状: x\n- 根因: y\n- 最后复核: 2026-06-16\n",
            encoding="utf-8",
        )
        r = run("check", "--repo-root", str(d))
        self.assertEqual(r.returncode, 1)
        self.assertIn("stale", r.stdout)

    def test_check_warns_but_passes_on_old_entry(self):
        d = init_repo()
        kn = d / ".aip/knowledge.md"
        kn.write_text(
            kn.read_text(encoding="utf-8")
            + "\n## K-001: t\n- 分类: ui\n- 状态: active\n- 症状: x\n- 根因: y\n- 最后复核: 2000-01-01\n",
            encoding="utf-8",
        )
        run("knowledge", "--repo-root", str(d))
        r = run("check", "--repo-root", str(d))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("warning:", r.stdout)


if __name__ == "__main__":
    unittest.main()
