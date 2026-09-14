import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _engine import ROOT, ENGINE


class ClaudeInstaller(unittest.TestCase):
    def run_installer(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "install_claude_plugin.py"), *args],
            cwd=ROOT, text=True, encoding="utf-8", capture_output=True,
        )

    def test_installs_whole_skill_dirs_and_overwrites(self):
        home = Path(tempfile.mkdtemp())
        old = home / ".claude" / "skills" / "aip"
        old.mkdir(parents=True)
        (old / "stale.txt").write_text("old", encoding="utf-8")
        (home / ".claude" / "commands" / "aip").mkdir(parents=True)

        result = self.run_installer("--home", str(home))
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        aip = home / ".claude" / "skills" / "aip"
        self.assertTrue((aip / "SKILL.md").exists())
        self.assertTrue((aip / "scripts" / "aip_init.py").exists())
        self.assertTrue((aip / "scripts" / "aip_session_start.py").exists())
        self.assertTrue((aip / "templates" / "overview-template.md").exists())
        self.assertTrue((aip / "reference").is_dir())
        self.assertEqual((aip / "VERSION").read_text(encoding="utf-8"),
                         (ENGINE / "VERSION").read_text(encoding="utf-8"))
        self.assertFalse((aip / "stale.txt").exists())
        self.assertTrue((home / ".claude" / "skills" / "root-cause" / "SKILL.md").exists())
        self.assertFalse((home / ".claude" / "commands" / "aip").exists())
        self.assertFalse((home / "plugins").exists())

    def test_installed_engine_runs_init_from_its_own_dir(self):
        # 装好的技能目录必须能脱离仓库独立跑：模板在技能目录里找得到。
        home = Path(tempfile.mkdtemp())
        self.assertEqual(self.run_installer("--home", str(home)).returncode, 0)
        target = Path(tempfile.mkdtemp())
        init = home / ".claude" / "skills" / "aip" / "scripts" / "aip_init.py"
        result = subprocess.run([sys.executable, str(init), "--repo-root", str(target), "--no-hooks"],
                                text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue((target / ".aip" / "OVERVIEW.md").exists())


if __name__ == "__main__":
    unittest.main()
