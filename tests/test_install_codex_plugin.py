import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class CodexInstaller(unittest.TestCase):
    def run_installer(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "install_codex_plugin.py"), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            env=env,
        )

    def test_default_overwrites_existing_install_and_installs_both_skill_locations(self):
        home = Path(tempfile.mkdtemp())
        env = os.environ.copy()
        env.pop("CODEX_HOME", None)
        old_plugin = home / "plugins" / "ai-implementation-protocol"
        old_plugin.mkdir(parents=True)
        (old_plugin / "old.txt").write_text("old", encoding="utf-8")
        old_skill = home / ".agents" / "skills" / "aip"
        old_skill.mkdir(parents=True)
        (old_skill / "SKILL.md").write_text("old", encoding="utf-8")

        result = self.run_installer("--home", str(home), env=env)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue((home / "plugins" / "ai-implementation-protocol" / ".codex-plugin" / "plugin.json").exists())
        self.assertFalse((old_plugin / "old.txt").exists())
        self.assertTrue((home / ".agents" / "skills" / "aip" / "SKILL.md").exists())
        self.assertTrue((home / ".agents" / "skills" / "root-cause" / "SKILL.md").exists())
        self.assertTrue((home / ".codex" / "skills" / "aip" / "SKILL.md").exists())
        self.assertTrue((home / ".codex" / "skills" / "root-cause" / "SKILL.md").exists())
        self.assertTrue((home / ".agents" / "plugins" / "marketplace.json").exists())

    def test_codex_home_scope_installs_skills_under_codex_home(self):
        home = Path(tempfile.mkdtemp())
        codex_home = home / "codex-home"
        env = os.environ.copy()
        env["CODEX_HOME"] = str(codex_home)
        result = self.run_installer(
            "--home", str(home),
            "--skill-scope", "codex-home",
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue((codex_home / "skills" / "aip" / "SKILL.md").exists())
        self.assertTrue((codex_home / "skills" / "root-cause" / "SKILL.md").exists())
        self.assertFalse((home / ".agents" / "skills" / "aip" / "SKILL.md").exists())
        self.assertTrue((home / ".agents" / "plugins" / "marketplace.json").exists())


if __name__ == "__main__":
    unittest.main()
