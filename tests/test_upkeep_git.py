"""到期提醒里靠 git 的两层：引用的代码改没改（按改动提醒）、引用的文件和名字还在不在。"""
import os, subprocess, sys, tempfile, unittest
from datetime import date
from pathlib import Path
from _engine import ROOT, ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_upkeep as up

TODAY = date(2026, 9, 27)


def git(repo: Path, *args: str, when: str | None = None) -> None:
    env = {**os.environ}
    if when:
        env.update(GIT_AUTHOR_DATE=f"{when}T12:00:00", GIT_COMMITTER_DATE=f"{when}T12:00:00")
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=repo, env=env,
                   check=True, capture_output=True)


def commit(repo: Path, when: str, files: dict[str, str | None]) -> None:
    for rel, content in files.items():
        p = repo / rel
        if content is None:
            git(repo, "rm", "-q", rel)
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        git(repo, "add", rel)
    git(repo, "commit", "-q", "-m", when, when=when)


def entry(kid: str, seen: str, body: str) -> str:
    return (f"## {kid}: 某坑\n- 分类: other\n- 状态: active\n- 症状: x\n- 根因: {body}\n"
            f"- 证据: z\n- 适用范围: w\n- 最后复核: {seen}\n\n")


def make_repo(knowledge: str, reference: str = "# 参照\n", last_review: str = "2026-09-20") -> Path:
    d = Path(tempfile.mkdtemp())
    git(d, "init", "-q", "-b", "master")
    commit(d, "2026-06-01", {
        "src/a.py": "def FooBar():\n    pass\n",
        "src/b.py": "def keep_me():\n    pass\n",
        "docs/guide.md": "# guide\n",
    })
    a = d / ".aip"; a.mkdir()
    (a / "knowledge.md").write_text("# k\n\n## 类目\nother\n\n" + knowledge, encoding="utf-8")
    (a / "reference.md").write_text(reference, encoding="utf-8")
    (a / "config.yaml").write_text(f'review_last_full: "{last_review}"\n', encoding="utf-8")
    return d


class ChangeDriven(unittest.TestCase):
    def test_untouched_code_is_not_nagged_even_after_90_days(self):
        d = make_repo(entry("K-001", "2026-06-15", "`src/a.py` 里的 `FooBar`"))
        self.assertEqual(up.reminders(d, TODAY), [])

    def test_code_changed_after_review_is_flagged(self):
        d = make_repo(entry("K-001", "2026-06-15", "`src/a.py` 里的 `FooBar`"))
        commit(d, "2026-07-01", {"src/a.py": "def FooBar():\n    return 1\n"})
        due = up.reminders(d, TODAY)
        self.assertTrue(any("改过" in x and "K-001" in x and "src/a.py" in x for x in due), due)

    def test_change_on_review_day_does_not_count(self):
        d = make_repo(entry("K-001", "2026-07-01", "`src/a.py`"))
        commit(d, "2026-07-01", {"src/a.py": "x = 1\n"})
        self.assertEqual(up.reminders(d, TODAY), [])

    def test_partial_path_and_line_suffix_resolve(self):
        d = make_repo(entry("K-001", "2026-06-15", "`a.py:12` 与 `src/a.py::FooBar`"))
        commit(d, "2026-07-01", {"src/a.py": "def FooBar():\n    return 2\n"})
        self.assertTrue(any("K-001" in x for x in up.reminders(d, TODAY)))

    def test_doc_only_change_is_not_a_code_change(self):
        d = make_repo(entry("K-001", "2026-06-15", "规则写在 `docs/guide.md`，代码在 `src/b.py`"))
        commit(d, "2026-07-01", {"docs/guide.md": "# guide v2\n"})
        self.assertEqual(up.reminders(d, TODAY), [])

    def test_entry_without_code_refs_falls_back_to_time(self):
        d = make_repo(entry("K-001", "2026-06-15", "树莓派装了 fail2ban，`/etc/fail2ban/jail.d` 下配置"))
        due = up.reminders(d, TODAY)
        self.assertTrue(any("只能按时间提醒" in x and "K-001" in x for x in due), due)

    def test_yearly_ceiling_for_untouched_code(self):
        d = make_repo(entry("K-001", "2026-06-15", "`src/a.py`"), last_review="2027-07-01")
        self.assertTrue(any("按年兜底" in x for x in up.reminders(d, date(2027, 7, 1))))


class GoneReferences(unittest.TestCase):
    def test_renamed_symbol_is_flagged(self):
        d = make_repo(entry("K-001", "2026-06-15", "`FooBar` 会卡住"))
        commit(d, "2026-07-01", {"src/a.py": "def BazQux():\n    pass\n"})
        due = up.reminders(d, TODAY)
        self.assertTrue(any("找不到" in x and "FooBar" in x for x in due), due)

    def test_deleted_file_is_flagged(self):
        d = make_repo(entry("K-001", "2026-06-15", "`src/b.py`"))
        commit(d, "2026-07-01", {"src/b.py": None})
        self.assertTrue(any("找不到" in x and "src/b.py" in x for x in up.reminders(d, TODAY)))

    def test_names_never_in_repo_are_not_flagged(self):
        # 外部接口、环境变量、服务器路径本来就不在仓库里，不能报
        d = make_repo(entry("K-001", "2026-06-15",
                            "`src/b.py` 调了 `RunAsClient`，环境变量 `ProgramFiles`，`/auth/me`，`.ps1`"))
        self.assertEqual(up.reminders(d, TODAY), [])

    def test_symbol_mentioned_only_in_docs_is_not_code(self):
        d = make_repo(entry("K-001", "2026-06-15", "`DocOnlyName`"))
        commit(d, "2026-06-10", {"docs/guide.md": "DocOnlyName\n"})
        commit(d, "2026-07-01", {"docs/guide.md": "# gone\n"})
        self.assertFalse(any("找不到" in x for x in up.reminders(d, TODAY)))

    def test_reference_items_gone_since_last_review(self):
        d = make_repo("", reference="# 参照\n## 可复用实现\n- `src/b.py` 的 `keep_me`\n", last_review="2026-06-15")
        commit(d, "2026-07-01", {"src/b.py": None})
        due = up.reminders(d, TODAY)
        self.assertTrue(any("reference.md" in x and "src/b.py" in x and "keep_me" in x for x in due), due)

    def test_not_a_git_repo_falls_back_to_time(self):
        d = Path(tempfile.mkdtemp()); a = d / ".aip"; a.mkdir()
        (a / "knowledge.md").write_text("# k\n\n" + entry("K-001", "2026-06-15", "`src/a.py`"), encoding="utf-8")
        (a / "config.yaml").write_text('review_last_full: "2026-09-20"\n', encoding="utf-8")
        self.assertTrue(any("只能按时间提醒" in x for x in up.reminders(d, TODAY)))


if __name__ == "__main__":
    unittest.main()
