"""/aip update：装好的技能自己查远端、自己原地更新，不走安装器、不需要本机有 AIP 仓库。"""
import io, json, os, shutil, subprocess, sys, tempfile, unittest
from contextlib import redirect_stdout
from pathlib import Path
from _engine import ROOT, ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_update as upd

PKG = "plugins/ai-implementation-protocol/skills"


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=repo,
                       check=True, capture_output=True, text=True)
    return r.stdout.strip()


def write_package(work: Path, version: str) -> None:
    for skill in ("aip", "root-cause"):
        (work / PKG / skill).mkdir(parents=True, exist_ok=True)
        (work / PKG / skill / "SKILL.md").write_text(f"# {skill} {version}\n", encoding="utf-8")
    scripts = work / PKG / "aip" / "scripts"; scripts.mkdir(exist_ok=True)
    (work / PKG / "aip" / "VERSION").write_text(version + "\n", encoding="utf-8")
    for name in ("aip_check.py", "aip_update.py"):
        (scripts / name).write_text(f"# {version}\n", encoding="utf-8")


class Env:
    """一个远端（bare 仓库）+ 一个推代码用的工作副本 + 一个项目级安装了 v1 的项目。"""
    def __init__(self):
        self.root = Path(tempfile.mkdtemp())
        self.remote = self.root / "remote.git"
        git(self.root, "init", "-q", "--bare", "-b", "master", str(self.remote))
        self.work = self.root / "work"
        git(self.root, "clone", "-q", str(self.remote), str(self.work))
        git(self.work, "checkout", "-q", "-b", "master")
        self.push("0.1.0")
        self.project = self.root / "proj"
        for rel in (".claude/skills", ".codex/skills"):
            root = self.project / rel; root.mkdir(parents=True)
            for skill in ("aip", "root-cause"):
                shutil.copytree(self.work / PKG / skill, root / skill)
            (root / "gandalf-own").mkdir()
            (root / "gandalf-own" / "SKILL.md").write_text("# 项目自己的技能\n", encoding="utf-8")
            self.record(root / "aip", self.head)
        (self.project / ".aip").mkdir()
        (self.project / ".aip" / "config.yaml").write_text("gates:\n", encoding="utf-8")
        self.engine = self.project / ".claude" / "skills" / "aip"

    def push(self, version: str) -> None:
        write_package(self.work, version)
        git(self.work, "add", "-A"); git(self.work, "commit", "-q", "-m", version)
        git(self.work, "push", "-q", "origin", "master")
        self.head = git(self.work, "rev-parse", "HEAD")

    def record(self, aip_dir: Path, commit: str, **extra) -> None:
        data = {"remote": str(self.remote), "branch": "master", "commit": commit, "scope": "project",
                "target": str(self.project), "source_path": "", **extra}
        (aip_dir / upd.SOURCE_FILE).write_text(json.dumps(data), encoding="utf-8")


def quiet(fn, *a):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fn(*a)
    return rc, buf.getvalue()


class Check(unittest.TestCase):
    def test_latest_is_silent(self):
        e = Env()
        self.assertEqual(upd.check(e.project, e.engine)["state"], "latest")
        self.assertIsNone(upd.update_notice(e.project, e.engine))

    def test_new_remote_commit_is_announced(self):
        e = Env(); e.push("0.2.0")
        note = upd.update_notice(e.project, e.engine)
        self.assertIsNotNone(note)
        self.assertIn(e.head[:7], note); self.assertIn("/aip update", note)

    def test_unreachable_remote_missing_source_are_silent(self):
        e = Env()
        e.record(e.engine, "0" * 40, remote=str(e.root / "nowhere.git"))
        self.assertIsNone(upd.update_notice(e.project, e.engine))
        (e.engine / upd.SOURCE_FILE).unlink()
        self.assertIsNone(upd.update_notice(e.project, e.engine))

    def test_project_config_binds_remote(self):
        e = Env(); e.push("0.2.0")
        e.record(e.engine, e.head, remote=str(e.root / "nowhere.git"))  # 记录里的地址是坏的
        other = e.root / "mirror.git"
        git(e.root, "clone", "-q", "--bare", str(e.remote), str(other))
        git(e.work, "push", "-q", str(other), "master")
        (e.project / ".aip" / "config.yaml").write_text(f'aip_remote: "{other.as_posix()}"\n', encoding="utf-8")
        self.assertEqual(upd.check(e.project, e.engine)["state"], "latest")

    def test_installed_ahead_of_remote_is_not_an_update(self):
        e = Env()
        write_package(e.work, "0.3.0-local")
        git(e.work, "add", "-A"); git(e.work, "commit", "-q", "-m", "local only")
        local = git(e.work, "rev-parse", "HEAD")
        e.record(e.engine, local, source_path=str(e.work))
        self.assertEqual(upd.check(e.project, e.engine)["state"], "ahead")


class Apply(unittest.TestCase):
    def test_apply_swaps_every_project_copy_and_keeps_own_skills(self):
        e = Env(); e.push("0.2.0")
        rc, out = quiet(upd.apply, e.project, e.engine)
        self.assertEqual(rc, 0, out)
        for rel in (".claude/skills", ".codex/skills"):
            root = e.project / rel
            self.assertEqual((root / "aip" / "VERSION").read_text(encoding="utf-8").strip(), "0.2.0")
            self.assertIn("0.2.0", (root / "root-cause" / "SKILL.md").read_text(encoding="utf-8"))
            self.assertTrue((root / "gandalf-own" / "SKILL.md").exists())
            self.assertEqual(json.loads((root / "aip" / upd.SOURCE_FILE).read_text(encoding="utf-8"))["commit"], e.head)
            self.assertEqual(sorted(p.name for p in root.iterdir() if p.name.startswith(".")), [])
        self.assertEqual(upd.check(e.project, e.engine)["state"], "latest")

    def test_project_copies_found_from_install_location_not_recorded_path(self):
        e = Env(); e.push("0.2.0")
        moved = e.root / "moved-proj"
        shutil.move(str(e.project), str(moved))  # 仓库换了目录，记录里的 target 已不存在
        rc, out = quiet(upd.apply, moved, moved / ".claude" / "skills" / "aip")
        self.assertEqual(rc, 0, out)
        for rel in (".claude/skills", ".codex/skills"):
            self.assertEqual((moved / rel / "aip" / "VERSION").read_text(encoding="utf-8").strip(), "0.2.0")

    def test_incomplete_remote_leaves_install_untouched(self):
        e = Env()
        write_package(e.work, "0.2.0")
        (e.work / PKG / "aip" / "scripts" / "aip_check.py").unlink()
        git(e.work, "add", "-A"); git(e.work, "commit", "-q", "-m", "broken"); git(e.work, "push", "-q", "origin", "master")
        rc, out = quiet(upd.apply, e.project, e.engine)
        self.assertEqual(rc, 1); self.assertIn("不完整", out)
        self.assertEqual((e.engine / "VERSION").read_text(encoding="utf-8").strip(), "0.1.0")

    def test_swap_rolls_back_when_a_rename_fails(self):
        e = Env(); e.push("0.2.0")
        new_skills = e.work / PKG
        root = e.project / ".claude" / "skills"
        real_rename = Path.rename
        calls = {"n": 0}

        def flaky(self, target):
            calls["n"] += 1
            if calls["n"] == 3:  # 换第二个技能时出错
                raise OSError("disk full")
            return real_rename(self, target)
        Path.rename = flaky
        try:
            with self.assertRaises(OSError):
                upd.swap_skills(new_skills, root)
        finally:
            Path.rename = real_rename
        self.assertEqual((root / "aip" / "VERSION").read_text(encoding="utf-8").strip(), "0.1.0")
        self.assertIn("0.1.0", (root / "root-cause" / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual(sorted(p.name for p in root.iterdir() if p.name.startswith(".")), [])


class InstallRecord(unittest.TestCase):
    def test_installer_writes_source_from_repo(self):
        e = Env()
        aip_dir = Path(tempfile.mkdtemp()) / "aip"; aip_dir.mkdir()
        (aip_dir / "VERSION").write_text("0.1.0\n", encoding="utf-8")
        upd.write_install_source(aip_dir, e.work, "project", e.project)
        data = json.loads((aip_dir / upd.SOURCE_FILE).read_text(encoding="utf-8"))
        self.assertEqual(data["commit"], e.head)
        self.assertEqual(data["scope"], "project")
        self.assertEqual(data["version"], "0.1.0")
        self.assertTrue(data["remote"])


if __name__ == "__main__":
    unittest.main()
