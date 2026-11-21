"""0.8.1：按 tech-ai-kits、docflow-agent 两个仓库整理 0.8.0 的反馈做的修正。"""
import os, shutil, subprocess, sys, tempfile, unittest
from datetime import date
from pathlib import Path
from _engine import ROOT, ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "scripts"))
import aip_check as chk, aip_init, aip_item as it, aip_lookup as lk, aip_size as size, aip_upkeep as up
import aip_update, install_hooks, install_claude_plugin


def git(d: Path, *args: str) -> str:
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=d,
                       check=True, capture_output=True, text=True, encoding="utf-8")
    return r.stdout


def set_version(d: Path, version: str) -> None:
    cfg = d/".aip"/"config.yaml"
    text = cfg.read_text(encoding="utf-8")
    cur = (ENGINE/"VERSION").read_text(encoding="utf-8").strip()
    cfg.write_text(text.replace(f'aip_version: "{cur}"', f'aip_version: "{version}"'), encoding="utf-8")


def make_repo(version: str | None = None, git_init: bool = False) -> Path:
    d = Path(tempfile.mkdtemp())
    if git_init:
        git(d, "init", "-q", "-b", "master")
    aip_init.scaffold(d, ENGINE)
    if version:
        set_version(d, version)
    return d


def topic(d: Path, name: str, body: str, paths: str = "") -> Path:
    head = f"---\ntitle: {name}\nread_when: 改{name}时\n" + (f"paths: {paths}\n" if paths else "") + "---\n\n"
    p = d/".aip"/"reference"/f"{name}.md"
    p.write_text(head + body, encoding="utf-8")
    return p


def knowledge(d: Path, title: str, body: str = "- 症状: x\n- 根因: y\n", stamp: str = "20260901-100000", **meta):
    return it.new_item(d, "knowledge", title, "active", stamp=stamp,
                       meta={"category": "c", "scope": "s", **meta}, body=body)


class Worktree(unittest.TestCase):
    def project_repo(self) -> tuple[Path, Path]:
        """项目级安装：引擎拷进仓库的 .claude/skills/aip。"""
        d = Path(tempfile.mkdtemp()) / "main"
        d.mkdir()
        git(d, "init", "-q", "-b", "master")
        engine = d/".claude"/"skills"/"aip"
        shutil.copytree(ENGINE, engine, ignore=shutil.ignore_patterns("__pycache__", "SOURCE.json"))
        aip_init.scaffold(d, engine)
        git(d, "add", "-A"); git(d, "commit", "-q", "-m", "init", "--no-verify")
        return d, engine

    def test_init_in_worktree_and_hook_uses_that_checkouts_engine(self):
        d, engine = self.project_repo()
        wt = d.parent / "wt"
        git(d, "worktree", "add", "-q", str(wt), "-b", "feature")
        self.assertTrue((wt/".git").is_file())
        wt_engine = wt/".claude"/"skills"/"aip"
        r = subprocess.run([sys.executable, str(wt_engine/"scripts"/"aip_init.py"), "--repo-root", str(wt)],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        hooks = Path(git(wt, "rev-parse", "--path-format=absolute", "--git-path", "hooks").strip())
        # 各 worktree 共用一份钩子：从 worktree 装的就是主工作区用的那个文件
        self.assertEqual(hooks, Path(git(d, "rev-parse", "--path-format=absolute", "--git-path", "hooks").strip()))
        hook = hooks / "pre-commit"
        body = hook.read_text(encoding="utf-8")
        self.assertIn('ENGINE="$(git rev-parse --show-toplevel)/.claude/skills/aip"', body)
        # 在 worktree 里提交：钩子跑的是这个 worktree 检出的引擎，检查通过
        (wt/"a.txt").write_text("x\n", encoding="utf-8")
        git(wt, "add", "a.txt")
        r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "a"], cwd=wt,
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # 检出里没有引擎（切到装 AIP 之前的分支）就跳过，不挡提交
        shutil.rmtree(wt_engine)
        (wt/"b.txt").write_text("y\n", encoding="utf-8")
        git(wt, "add", "-A")
        r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "b"], cwd=wt,
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("check skipped", r.stderr)

    def test_engine_outside_repo_is_written_as_absolute_path(self):
        d = make_repo(git_init=True)
        self.assertIn(f'ENGINE="{ENGINE.as_posix()}"', install_hooks.pre_commit_body(ENGINE, d))

    def test_install_record_points_at_main_worktree(self):
        d, _ = self.project_repo()
        wt = d.parent / "wt2"
        git(d, "worktree", "add", "-q", str(wt), "-b", "f2")
        self.assertEqual(aip_update.main_worktree(wt), d.resolve())
        self.assertEqual(aip_update.main_worktree(d), d.resolve())


class Init(unittest.TestCase):
    def test_claude_md_that_only_imports_agents_md_gets_no_block(self):
        d = Path(tempfile.mkdtemp())
        (d/"CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
        self.assertEqual(aip_init.guide_files(d), ["AGENTS.md"])
        (d/"CLAUDE.md").write_text("# 规则\n自己的内容\n", encoding="utf-8")
        self.assertEqual(aip_init.guide_files(d), ["CLAUDE.md", "AGENTS.md"])

    def test_no_gitkeep_in_dir_that_already_has_files(self):
        d = make_repo()
        (d/".aip"/"reuse"/".gitkeep").unlink()
        it.new_item(d, "reuse", "重试", meta={"paths": "a.py"}, body="- 钦定实现: x\n- 边界: y\n", stamp="20261001-100000")
        aip_init.scaffold(d, ENGINE)
        self.assertFalse((d/".aip"/"reuse"/".gitkeep").exists())

    def test_gitignore_comment_is_not_an_exclusion(self):
        d = make_repo(git_init=True)
        skill = d/".claude"/"skills"/"aip"/"SKILL.md"
        skill.parent.mkdir(parents=True); skill.write_text("x\n", encoding="utf-8")
        (d/".gitignore").write_text("# 别把 .claude/skills 加进来\n", encoding="utf-8")
        self.assertFalse(install_claude_plugin._ignored(d, skill))
        (d/".gitignore").write_text(".claude/skills/\n", encoding="utf-8")
        self.assertTrue(install_claude_plugin._ignored(d, skill))


class Relevant(unittest.TestCase):
    def test_backtick_paths_in_body_count_like_paths(self):
        d = make_repo()
        k = knowledge(d, "正文写了路径", body="- 症状: x\n- 根因: `src/runner.py` 里的 `Run` 和 `tests/test_a.py::test_b`\n")
        hits, _ = lk.relevant(d, ["src/runner.py"])
        self.assertTrue(any(k.slug in h.target for h in hits))
        hits, _ = lk.relevant(d, ["tests/test_a.py"])
        self.assertTrue(any(k.slug in h.target for h in hits))

    def test_staged_only_anchors_near_the_change(self):
        d = make_repo(git_init=True)
        near = knowledge(d, "改动附近的", stamp="20260901-100001")
        far = knowledge(d, "离得远的", stamp="20260901-100002")
        lines = [f"第 {n} 行" for n in range(200)]
        lines[5] = f"见 .aip/knowledge/{far.id}"
        lines[150] = f"见 .aip/knowledge/{near.id}"
        doc = d/"docs"/"设计.md"
        doc.parent.mkdir()
        doc.write_text("\n".join(lines) + "\n", encoding="utf-8")
        git(d, "add", "-A"); git(d, "commit", "-q", "-m", "a", "--no-verify")
        lines[152] = "改了这一行"
        doc.write_text("\n".join(lines) + "\n", encoding="utf-8")
        git(d, "add", "docs")
        self.assertEqual(lk.staged_files(d), ["docs/设计.md"])  # 中文文件名不被转成八进制
        hits, _ = lk.relevant(d, lk.staged_files(d), lk.staged_hunks(d))
        targets = " ".join(h.target for h in hits)
        self.assertIn(near.slug, targets)
        self.assertNotIn(far.slug, targets)
        # 改代码前手动查：不知道会改哪里，按整个文件找
        targets = " ".join(h.target for h in lk.relevant(d, ["docs/设计.md"])[0])
        self.assertIn(far.slug, targets)


class Links(unittest.TestCase):
    def test_inbox_mentions_of_old_paths_are_not_red(self):
        d = make_repo()  # 当前版本（0.8.1），检查范围最大时旁路问题也不查
        it.new_item(d, "inbox", "外部仓库还指着旧文件", stamp="20261001-100000",
                    body="- 症状 / 证据: 外部仓库还指向已删除的 .aip/knowledge.md\n")
        self.assertEqual(chk.check_links(d), [])

    def test_self_section_pointer(self):
        d = make_repo()
        topic(d, "部署", "## 镜像\n- 见本文「镜像」\n- 见本文「回滚」\n")
        viol = chk.check_links(d)
        self.assertEqual(len(viol), 1, viol)
        self.assertIn("本文「回滚」", viol[0])

    def test_specs_and_project_skills_checked_from_081(self):
        for version, red in (("0.8.0", False), (None, True)):
            d = make_repo(version)
            (d/".aip"/"specs").mkdir()
            (d/".aip"/"specs"/"规格.md").write_text("先读 reference.md「环境」\n", encoding="utf-8")
            skill = d/".claude"/"skills"/"kit-dev"/"SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("见 `.aip/reference/没有.md`\n", encoding="utf-8")
            codex = d/".codex"/"skills"/"kit-dev"/"reference"/"细节.md"
            codex.parent.mkdir(parents=True)
            codex.write_text("见 .aip/knowledge/20200101-000000_没有\n", encoding="utf-8")
            (d/"docs").mkdir()
            (d/"docs"/"说明.md").write_text("见 conventions.md「没有这节」\n", encoding="utf-8")
            cfg = d/".aip"/"config.yaml"
            cfg.write_text(cfg.read_text(encoding="utf-8").replace('size_check_paths: ""', 'size_check_paths: "docs/*.md"'),
                           encoding="utf-8")
            viol = chk.check_links(d)
            self.assertEqual(any(".codex/skills/kit-dev/reference/细节.md" in v for v in viol), red, viol)
            self.assertEqual(any("docs/说明.md" in v for v in viol), red, viol)
            self.assertEqual(any("specs/规格.md" in v for v in viol), red, viol)
            self.assertEqual(any("kit-dev/SKILL.md" in v for v in viol), red, viol)


class Sizes(unittest.TestCase):
    def test_over_says_by_how_much(self):
        d = make_repo()
        topic(d, "大", "x" * 30200)
        viol = chk.check_sizes(d)
        self.assertTrue(any("大.md 有" in v and "上限 30000，超了" in v for v in viol), viol)

    def test_near_limit_is_a_reminder_not_red(self):
        d = make_repo()
        topic(d, "快满", ("x" * 99 + "\n") * 280)
        self.assertEqual(chk.check_sizes(d), [])
        self.assertTrue(any("快满.md" in x and "快到" in x for x in up.reminders(d, date(2026, 10, 16), limit=None)))

    def test_project_skill_body_limit_from_081(self):
        for version, red in (("0.8.0", False), (None, True)):
            d = make_repo(version)
            for name in ("kit-dev", "aip"):
                skill = d/".claude"/"skills"/name/"SKILL.md"
                skill.parent.mkdir(parents=True)
                skill.write_text("x" * 9000, encoding="utf-8")
            viol = chk.check_sizes(d)
            self.assertEqual(any("kit-dev/SKILL.md" in v for v in viol), red, viol)
            self.assertFalse(any("skills/aip/SKILL.md" in v for v in viol), viol)  # 装进来的 aip 是引擎拷贝，不重复查


if __name__ == "__main__":
    unittest.main()
