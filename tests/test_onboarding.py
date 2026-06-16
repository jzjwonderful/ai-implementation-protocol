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


class StartMustRead(unittest.TestCase):
    def test_start_keeps_knowledge_index_in_must_read(self):
        d = init_repo()
        assert run("start", "2026-06-16-x", "--title", "X", "--repo-root", str(d)).returncode == 0
        ct = json.loads((d / ".aip/_runtime/current_task.json").read_text(encoding="utf-8"))
        self.assertIn(".aip/knowledge_index.md", ct["must_read"])


class ResumeGraceful(unittest.TestCase):
    def test_resume_without_init_is_friendly(self):
        d = Path(tempfile.mkdtemp())  # 未 init
        r = run("resume", "--repo-root", str(d))
        self.assertEqual(r.returncode, 1)
        self.assertIn("aip init", r.stdout)
        self.assertNotIn("Traceback", r.stderr)


class DoneCommand(unittest.TestCase):
    def test_done_rolls_back_when_check_fails(self):
        d = init_repo()
        run("start", "2026-06-16-x", "--title", "X", "--repo-root", str(d))
        # spec/verification 未完成 → check 失败 → status 应回滚不为 done
        r = run("done", "--repo-root", str(d))
        self.assertEqual(r.returncode, 1)
        ct = json.loads((d / ".aip/_runtime/current_task.json").read_text(encoding="utf-8"))
        self.assertNotEqual(ct["status"], "done")


class ConfigGates(unittest.TestCase):
    def _set_done_with_full_feature(self, d: Path, verification_extra: str):
        run("start", "2026-06-16-x", "--title", "X", "--repo-root", str(d))
        fd = d / ".aip/features/2026-06-16-x"
        (fd / "spec.md").write_text("## Goal\ng\n## Scope\ns\n## Acceptance Criteria\n1. a\n", encoding="utf-8")
        (fd / "verification.md").write_text(
            "## Machine Gates\n| gate | result | evidence |\n|--|--|--|\n" + verification_extra
            + "\n## Independent Review\nreviewer=other\n", encoding="utf-8")
        ct = json.loads((d / ".aip/_runtime/current_task.json").read_text(encoding="utf-8"))
        ct["status"] = "done"
        (d / ".aip/_runtime/current_task.json").write_text(json.dumps(ct, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_done_fails_when_declared_gate_not_covered(self):
        d = init_repo()
        cfg = d / ".aip/config.yaml"
        cfg.write_text("gates:\n  tests:\n    cmd: \"pytest -q\"\n", encoding="utf-8")
        self._set_done_with_full_feature(d, "| build | pass | log |")  # 覆盖 build，没覆盖 tests
        r = run("check", "--repo-root", str(d))
        self.assertEqual(r.returncode, 1)
        self.assertIn("tests", r.stdout)

    def test_warns_when_no_gates_declared(self):
        d = init_repo()
        r = run("check", "--repo-root", str(d))  # 模板 gates 全空
        self.assertIn("未声明任何机器闸门", r.stdout)


class CompetingArtifacts(unittest.TestCase):
    def test_non_aip_file_with_slot_name_not_flagged(self):
        d = init_repo()
        docs = d / "docs"
        docs.mkdir()
        (docs / "verification.md").write_text("# 验收说明\n普通文档，不是 AIP 槽位\n", encoding="utf-8")
        r = run("check", "--repo-root", str(d))
        self.assertNotIn("Competing AIP artifact", r.stdout)

    def test_real_slot_outside_aip_is_flagged(self):
        d = init_repo()
        bad = d / "docs"
        bad.mkdir()
        (bad / "verification.md").write_text("## Machine Gates\n| g | pass | e |\n", encoding="utf-8")
        r = run("check", "--repo-root", str(d))
        self.assertIn("Competing AIP artifact", r.stdout)


class DiscoveryBlocks(unittest.TestCase):
    def test_init_writes_idempotent_blocks_to_both_files(self):
        d = init_repo()
        for fn in ("CLAUDE.md", "AGENTS.md"):
            txt = (d / fn).read_text(encoding="utf-8")
            self.assertIn("BEGIN AIP (managed)", txt)
            self.assertIn(".aip/knowledge_index.md", txt)
        # 用户内容 + 重跑 init 不破坏、不重复
        (d / "CLAUDE.md").write_text("# 我的项目\n保留我\n\n" + (d / "CLAUDE.md").read_text(encoding="utf-8"), encoding="utf-8")
        assert run("init", "--repo-root", str(d)).returncode == 0
        txt = (d / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("保留我", txt)
        self.assertEqual(txt.count("BEGIN AIP (managed)"), 1)


class InstallCommands(unittest.TestCase):
    def test_claude_installer_installs_commands(self):
        home = Path(tempfile.mkdtemp())
        r = subprocess.run([sys.executable, str(REPO / "scripts/install_claude_plugin.py"),
                            "--home", str(home), "--force"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((home / ".claude/commands/aip/init.md").exists())
        self.assertTrue((home / ".claude/commands/aip/done.md").exists())


if __name__ == "__main__":
    unittest.main()
