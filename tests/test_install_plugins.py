"""安装器冒烟：Claude / Codex / Grok 三端 skills 落点与覆盖安装行为。"""
from __future__ import annotations

import importlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _load(name: str):
    return importlib.import_module(name)


class InstallGrok(unittest.TestCase):
    def test_installs_skills_and_engine(self):
        home = Path(tempfile.mkdtemp())
        mod = _load("install_grok_plugin")
        # 直接调 main 的核心步骤：copy + skills
        src = ROOT / "plugins" / mod.PLUGIN_NAME
        dst = home / "plugins" / mod.PLUGIN_NAME
        mod.copy_plugin(src, dst)
        installed = mod.install_skills(dst, home)
        self.assertTrue((dst / ".grok-plugin" / "plugin.json").exists())
        self.assertTrue((dst / "scripts" / "aip_init.py").exists())
        self.assertEqual(
            {p.name for p in installed},
            {"SKILL.md"},
        )
        for skill in ["aip", "root-cause"]:
            self.assertTrue((home / ".grok" / "skills" / skill / "SKILL.md").exists())
        # 默认不装 ~/.grok/plugins/
        self.assertFalse((home / ".grok" / "plugins" / mod.PLUGIN_NAME).exists())

    def test_user_plugin_opt_in(self):
        home = Path(tempfile.mkdtemp())
        mod = _load("install_grok_plugin")
        src = ROOT / "plugins" / mod.PLUGIN_NAME
        dst = home / "plugins" / mod.PLUGIN_NAME
        mod.copy_plugin(src, dst)
        mod.install_skills(dst, home)
        grok_plugin = mod.install_user_plugin(dst, home)
        self.assertTrue((grok_plugin / ".grok-plugin" / "plugin.json").exists())
        self.assertTrue((grok_plugin / "skills" / "aip" / "SKILL.md").exists())

    def test_reinstall_overwrites_existing_skill(self):
        # 默认覆盖：重跑安装直接替换旧 SKILL.md，无需 --force。
        home = Path(tempfile.mkdtemp())
        mod = _load("install_grok_plugin")
        src = ROOT / "plugins" / mod.PLUGIN_NAME
        dst = home / "plugins" / mod.PLUGIN_NAME
        mod.copy_plugin(src, dst)
        mod.install_skills(dst, home)
        skill = home / ".grok" / "skills" / "aip" / "SKILL.md"
        skill.write_text("stale", encoding="utf-8")
        mod.install_skills(dst, home)
        self.assertNotEqual(skill.read_text(encoding="utf-8"), "stale")


class InstallClaudeAndCodexSmoke(unittest.TestCase):
    def test_claude_skill_dest(self):
        home = Path(tempfile.mkdtemp())
        mod = _load("install_claude_plugin")
        src = ROOT / "plugins" / mod.PLUGIN_NAME
        dst = home / "plugins" / mod.PLUGIN_NAME
        mod.copy_plugin(src, dst, force=False)
        installed = mod.install_skills(dst, home, force=False)
        self.assertTrue(any(".claude" in str(p) for p in installed))
        self.assertTrue((home / ".claude" / "skills" / "aip" / "SKILL.md").exists())

    def test_codex_skill_dest(self):
        home = Path(tempfile.mkdtemp())
        mod = _load("install_codex_plugin")
        src = ROOT / "plugins" / mod.PLUGIN_NAME
        dst = home / "plugins" / mod.PLUGIN_NAME
        mod.copy_plugin(src, dst)
        skill_roots = mod.codex_skill_roots(home, mod.default_codex_home(home), "agents")
        installed = mod.install_skills(dst, skill_roots)
        self.assertTrue(any(".agents" in str(p) for p in installed))
        self.assertTrue((home / ".agents" / "skills" / "aip" / "SKILL.md").exists())


class UninstallGrok(unittest.TestCase):
    def test_removes_grok_paths(self):
        home = Path(tempfile.mkdtemp())
        plugin = home / "plugins" / "ai-implementation-protocol"
        plugin.mkdir(parents=True)
        for base in [".claude", ".agents", ".grok"]:
            for skill in ["aip", "root-cause"]:
                p = home / base / "skills" / skill
                p.mkdir(parents=True)
                (p / "SKILL.md").write_text("x", encoding="utf-8")
        (home / ".grok" / "plugins" / "ai-implementation-protocol").mkdir(parents=True)

        mod = _load("uninstall_aip")
        # 调 main 逻辑：构造 argv
        old = sys.argv
        try:
            sys.argv = ["uninstall_aip.py", "--home", str(home)]
            rc = mod.main()
        finally:
            sys.argv = old
        self.assertEqual(rc, 0)
        self.assertFalse(plugin.exists())
        for skill in ["aip", "root-cause"]:
            self.assertFalse((home / ".grok" / "skills" / skill).exists())
        self.assertFalse((home / ".grok" / "plugins" / "ai-implementation-protocol").exists())


class InstallAll(unittest.TestCase):
    def test_installs_all_runtimes_once(self):
        home = Path(tempfile.mkdtemp())
        mod = _load("install_all")
        rc = mod.main(["--repo-root", str(ROOT), "--home", str(home)])
        self.assertEqual(rc, 0)
        engine = home / "plugins" / mod.PLUGIN_NAME
        self.assertTrue((engine / "scripts" / "aip_init.py").exists())
        for base in [".claude", ".agents", ".grok"]:
            for skill in ["aip", "root-cause"]:
                self.assertTrue((home / base / "skills" / skill / "SKILL.md").exists())
        self.assertTrue((home / ".agents" / "plugins" / "marketplace.json").exists())
        # 默认不装 grok user plugin
        self.assertFalse((home / ".grok" / "plugins" / mod.PLUGIN_NAME).exists())
        # 覆盖安装：重跑不因目标已存在而报错
        self.assertEqual(mod.main(["--repo-root", str(ROOT), "--home", str(home)]), 0)

    def test_targets_subset(self):
        home = Path(tempfile.mkdtemp())
        mod = _load("install_all")
        rc = mod.main(
            ["--repo-root", str(ROOT), "--home", str(home), "--targets", "grok"]
        )
        self.assertEqual(rc, 0)
        self.assertTrue((home / ".grok" / "skills" / "aip" / "SKILL.md").exists())
        self.assertFalse((home / ".claude" / "skills" / "aip").exists())
        self.assertFalse((home / ".agents" / "skills" / "aip").exists())

    def test_unknown_target_fails(self):
        mod = _load("install_all")
        with self.assertRaises(SystemExit):
            mod.parse_targets("claude,windsurf")


if __name__ == "__main__":
    unittest.main()
