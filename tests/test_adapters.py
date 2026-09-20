"""adapters/ 的可选集成：只验证它们不替调用方猜运行时。"""
import sys
import tempfile
import unittest
from pathlib import Path

from _engine import ROOT

sys.path.insert(0, str(ROOT / "adapters"))
import ci_adapter, git_adapter, nexus_adapter  # noqa: E402


class CiAdapter(unittest.TestCase):
    def test_command_follows_the_given_engine_root(self):
        for engine in ["~/.claude/skills/aip", "~/.agents/skills/aip", "/repo/.claude/skills/aip"]:
            step = ci_adapter.recommended_ci_step(engine)
            self.assertIn(f"{engine}/scripts/aip_check.py", step)
            self.assertTrue(step.endswith("--repo-root ."))

    def test_no_runtime_is_assumed(self):
        # 不给引擎路径就不该有命令可返回：写死某一端的落点正是这里修掉的毛病。
        with self.assertRaises(TypeError):
            ci_adapter.recommended_ci_step()


class OtherAdapters(unittest.TestCase):
    def test_git_repo_detection(self):
        d = Path(tempfile.mkdtemp())
        self.assertFalse(git_adapter.detect_git_repo(d))
        (d / ".git").mkdir()
        self.assertTrue(git_adapter.detect_git_repo(d))

    def test_nexus_map_detection(self):
        d = Path(tempfile.mkdtemp())
        self.assertIsNone(nexus_adapter.detect_nexus_map(d))
        (d / ".nexus-map").mkdir()
        (d / ".nexus-map" / "INDEX.md").write_text("x", encoding="utf-8")
        self.assertIsNotNone(nexus_adapter.detect_nexus_map(d))


if __name__ == "__main__":
    unittest.main()
