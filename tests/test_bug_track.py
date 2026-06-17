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
    assert run("init", "--repo-root", str(d)).returncode == 0
    return d


def start_bug(d: Path, bug_id="2026-06-17-x", title="Crash on save"):
    return run("bug", bug_id, "--title", title, "--repo-root", str(d))


class BugScaffold(unittest.TestCase):
    def test_bug_creates_light_slots_only(self):
        d = init_repo()
        self.assertEqual(start_bug(d).returncode, 0)
        fd = d / ".aip/features/2026-06-17-x"
        for f in ("report.md", "file_scope.yaml", "verification.md", "handoff.md", "session_log.md"):
            self.assertTrue((fd / f).exists(), f)
        for f in ("spec.md", "plan.md", "task_board.yaml"):
            self.assertFalse((fd / f).exists(), f)

    def test_bug_sets_kind_and_phase(self):
        d = init_repo()
        start_bug(d)
        ct = json.loads((d / ".aip/_runtime/current_task.json").read_text(encoding="utf-8"))
        self.assertEqual(ct["kind"], "bug")
        self.assertEqual(ct["current_phase"], "investigate")
        self.assertIn(".aip/features/2026-06-17-x/report.md", ct["must_read"])

    def test_bug_refuses_existing_dir(self):
        d = init_repo()
        self.assertEqual(start_bug(d).returncode, 0)
        self.assertNotEqual(start_bug(d).returncode, 0)


if __name__ == "__main__":
    unittest.main()
