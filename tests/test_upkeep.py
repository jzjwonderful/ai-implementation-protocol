import json, subprocess, sys, tempfile, unittest
from datetime import date
from pathlib import Path
from _engine import ROOT, ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_upkeep as up, aip_item as it, aip_session_start as ss
from _aip_common import OLD_BOARD_HEADER

TODAY = date(2026, 9, 27)


CURRENT = f'aip_version: "{(ENGINE/"VERSION").read_text(encoding="utf-8").strip()}"\n'


def make_repo(config: str = 'review_last_full: "2026-09-20"\n', tidied: bool = True) -> Path:
    """tidied：config 里写上当前版本的 aip_version，不触发升级整理提醒。"""
    d = Path(tempfile.mkdtemp()); a = d/".aip"; a.mkdir()
    (a/"config.yaml").write_text(config + (CURRENT if tidied else ""), encoding="utf-8")
    return d


def knowledge(d: Path, title: str, status: str, seen: str, stamp: str = "20260601-100000") -> it.Item:
    return it.new_item(d, "knowledge", title, status, stamp=stamp,
                       meta={"category": "other", "scope": "w", "last_reviewed": seen},
                       body="- 症状: x\n- 根因: y\n")


class Reminders(unittest.TestCase):
    def test_fresh_repo_has_nothing_due(self):
        d = make_repo(); knowledge(d, "新坑", "active", "2026-09-01")
        self.assertEqual(up.reminders(d, TODAY), [])

    def test_stale_active_knowledge_is_listed_by_full_id(self):
        d = make_repo()
        old = knowledge(d, "老坑", "active", "2026-06-17")
        knowledge(d, "新坑", "active", "2026-09-01")
        due = up.reminders(d, TODAY)
        self.assertEqual(len(due), 1)
        self.assertIn(old.id, due[0]); self.assertNotIn("新坑", due[0])

    def test_boundary_is_ninety_days(self):
        d = make_repo(); knowledge(d, "坑", "active", "2026-06-29")   # 正好 90 天
        self.assertEqual(up.reminders(d, TODAY), [])
        d = make_repo(); knowledge(d, "坑", "active", "2026-06-28")   # 91 天
        self.assertTrue(up.reminders(d, TODAY))

    def test_fixed_and_superseded_are_not_nagged(self):
        d = make_repo()
        knowledge(d, "已修", "fixed", "2026-01-01")
        k = knowledge(d, "被取代", "active", "2026-01-01")
        it.set_status(d, k.id, "superseded", by="新机制")
        self.assertEqual(up.reminders(d, TODAY), [])

    def test_drafts_are_listed(self):
        d = make_repo(); k = knowledge(d, "草稿", "draft", "2026-09-26")
        self.assertTrue(any("draft" in x and k.id in x for x in up.reminders(d, TODAY)))

    def test_long_lists_get_a_summary_and_are_capped_in_priority_order(self):
        d = make_repo()
        for n in range(8):
            knowledge(d, f"老坑{n}", "active", "2026-01-01", stamp=f"20260601-10000{n}")
        draft = knowledge(d, "草稿", "draft", "2026-09-26")
        due = up.reminders(d, TODAY)
        self.assertEqual(len(due), up.REMINDER_LIMIT + 1)
        self.assertIn("共 9 项", due[0]); self.assertIn("--all", due[0])
        self.assertIn(draft.id, due[1])          # draft 排在按时间到期的前面
        self.assertEqual(len(up.reminders(d, TODAY, limit=None)), 9)

    def test_each_item_lands_in_one_bucket_only(self):
        d = make_repo()
        k = knowledge(d, "老坑", "active", "2026-01-01")
        self.assertEqual(sum(k.id in x for x in up.reminders(d, TODAY, limit=None)), 1)

    def test_full_review_overdue_missing_and_blank(self):
        self.assertTrue(any("已 38 天" in x for x in up.reminders(make_repo('review_last_full: "2026-08-20"\n'), TODAY)))
        self.assertTrue(any("没记上次整份 review" in x for x in up.reminders(make_repo("gates:\n"), TODAY)))
        self.assertTrue(any("没记上次整份 review" in x for x in up.reminders(make_repo('review_last_full: ""\n'), TODAY)))
        self.assertEqual(up.reminders(make_repo("review_last_full: 2026-09-20  # 注释\n"), TODAY), [])


class Tracks(unittest.TestCase):
    def test_long_track_is_flagged(self):
        d = make_repo()
        body = "\n".join(f"- 第 {n} 段流水账" for n in range(up.TRACK_LINE_LIMIT + 1))
        live = it.new_item(d, "track", "长线", body=body, stamp="20260901-100000")
        due = up.reminders(d, TODAY)
        self.assertEqual(len(due), 1)
        self.assertIn(live.id, due[0])


class Upgrade(unittest.TestCase):
    def test_repo_without_aip_version_is_asked_to_tidy_up(self):
        due = up.reminders(make_repo(tidied=False), TODAY)
        self.assertEqual(len(due), 1, due)
        self.assertIn("reference/upgrade.md", due[0]); self.assertIn("0.7.0", due[0])

    def test_only_versions_newer_than_aip_version_are_pending(self):
        self.assertEqual(up.pending_upgrades(make_repo('aip_version: "0.6.0"\n', tidied=False)), ["0.7.0"])
        self.assertEqual(up.pending_upgrades(make_repo('aip_version: "0.7.0"\n', tidied=False)), [])
        self.assertEqual(up.pending_upgrades(make_repo('aip_version: "0.10.0"\n', tidied=False)), [])

    def test_doc_headings_are_versions(self):
        heads = up.UPGRADE_HEAD_RE.findall(up.UPGRADE_DOC.read_text(encoding="utf-8"))
        self.assertIn("0.7.0", heads)
        version = (ENGINE/"VERSION").read_text(encoding="utf-8").strip()
        self.assertTrue(all(up._version(h) <= up._version(version) for h in heads), heads)


class Guides(unittest.TestCase):
    def test_dead_script_path_outside_managed_block(self):
        d = make_repo()
        (d/"CLAUDE.md").write_text(
            "# 项目\n跑 `python3 ~/plugins/aip-gone-for-test/scripts/aip_check.py --repo-root .`\n"
            "占位写法 `python <skill>/scripts/aip_check.py` 不算\n"
            "<!-- BEGIN AIP (managed) -->\n`/no/such/scripts/aip_overview.py`\n<!-- END AIP (managed) -->\n",
            encoding="utf-8")
        due = up.reminders(d, TODAY)
        self.assertEqual(len(due), 1, due)
        self.assertIn("aip-gone-for-test", due[0]); self.assertNotIn("aip_overview", due[0])

    def test_existing_path_is_fine(self):
        d = make_repo()
        (d/"AGENTS.md").write_text(f"`{SCRIPTS.as_posix()}/aip_check.py`\n", encoding="utf-8")
        self.assertEqual(up.reminders(d, TODAY), [])


class SessionStart(unittest.TestCase):
    def run_hook(self, repo: Path, source: str) -> str:
        return subprocess.run(
            [sys.executable, str(SCRIPTS/"aip_session_start.py"), "--repo-root", str(repo)],
            input=json.dumps({"source": source}), capture_output=True, text=True, encoding="utf-8").stdout

    def test_startup_prints_board_and_reminders_but_compact_skips_reminders(self):
        d = make_repo(); knowledge(d, "老坑", "active", "2020-01-01")
        it.new_item(d, "track", "在做的线", stamp="20260901-100000")
        out = self.run_hook(d, "startup")
        self.assertIn("在做的线", out); self.assertIn("到期提醒", out)
        self.assertIn(Path(sys.executable).as_posix(), out)   # 打出探测到的解释器
        self.assertFalse((d/".aip"/"OVERVIEW.md").exists())   # 看板只打印，不存文件
        compact = self.run_hook(d, "compact")
        self.assertIn("在做的线", compact); self.assertNotIn("到期提醒", compact)

    def test_old_layout_asks_for_migration(self):
        d = make_repo()
        (d/".aip"/"knowledge.md").write_text("# 旧\n", encoding="utf-8")
        (d/".aip"/"OVERVIEW.md").write_text("# 旧看板\n", encoding="utf-8")
        out = self.run_hook(d, "startup")
        self.assertIn("旧格式", out); self.assertIn("# 旧看板", out)


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=repo, check=True,
                   capture_output=True)


class CheckoutNotes(unittest.TestCase):
    def test_behind_upstream_and_uncommitted_aip_changes(self):
        origin = make_repo()
        git(origin, "init", "-q", "-b", "master")
        (origin/"a.txt").write_text("1\n", encoding="utf-8")
        git(origin, "add", "."); git(origin, "commit", "-q", "-m", "1")
        clone = Path(tempfile.mkdtemp()) / "c"
        git(origin.parent, "clone", "-q", str(origin), str(clone))
        self.assertEqual(ss.checkout_notes(clone), [])
        (origin/"a.txt").write_text("2\n", encoding="utf-8")
        git(origin, "commit", "-q", "-am", "2")
        git(clone, "fetch", "-q")
        (clone/".aip"/"inbox").mkdir(parents=True)
        (clone/".aip"/"inbox"/"x.md").write_text("x\n", encoding="utf-8")
        (clone/".aip"/"inbox"/"y.md").write_text("y\n", encoding="utf-8")
        notes = ss.checkout_notes(clone)
        self.assertTrue(any("2 个文件" in n for n in notes), notes)   # 没进版本库的目录也逐个数
        self.assertTrue(any("落后 origin/master 1 个提交" in n for n in notes), notes)
        self.assertTrue(any("没提交" in n for n in notes), notes)

    def test_not_a_git_repo_is_silent(self):
        self.assertEqual(ss.checkout_notes(make_repo()), [])


class Board(unittest.TestCase):
    def test_board_lists_tracks_in_full_and_open_inbox_by_file_name(self):
        d = make_repo()
        t = it.new_item(d, "track", "在做的线", body="- 目标: 做完它\n", stamp="20260901-100000")
        opened = it.new_item(d, "inbox", "没处理的问题", stamp="20260902-100000")
        closed = it.new_item(d, "inbox", "处理完的问题", "closed", stamp="20260903-100000")
        it.new_item(d, "knowledge", "某个坑", "active", meta={"category": "c", "scope": "s"},
                    body="- 症状: x\n- 根因: y\n", stamp="20260904-100000")
        out = ss.board(d)
        self.assertIn(t.path.name, out); self.assertIn("做完它", out)
        self.assertIn(opened.path.name, out); self.assertNotIn(closed.path.name, out)
        self.assertNotIn("某个坑", out)          # 知识不上看板，按文件名查

    def test_leftover_done_track_from_old_version_is_not_live(self):
        d = make_repo()
        (d/".aip"/"tracks").mkdir()
        (d/".aip"/"tracks"/"20260901-100000_track_done_旧线.md").write_text(
            "---\ntitle: 旧线\nstatus: done\n---\n", encoding="utf-8")
        self.assertNotIn("旧线", ss.board(d))

    def test_empty_repo(self):
        out = ss.board(make_repo())
        self.assertEqual(out.count("（没有）"), 2)

    def test_inbox_is_capped_newest_first(self):
        d = make_repo()
        for n in range(ss.INBOX_LIMIT + 2):
            it.new_item(d, "inbox", f"问题{n:02d}", stamp=f"202609{n + 1:02d}-100000")
        out = ss.board(d)
        self.assertLess(out.index("问题11"), out.index("问题10"))
        self.assertNotIn("问题00", out); self.assertIn("还有 2 条", out)

    def test_generated_board_from_old_version_is_removed_hand_written_kept(self):
        d = make_repo()
        board = d/".aip"/"OVERVIEW.md"
        board.write_text(OLD_BOARD_HEADER + "\n旧内容\n", encoding="utf-8")
        SessionStart().run_hook(d, "startup")
        self.assertFalse(board.exists())
        board.write_text("# 有人手写的看板\n", encoding="utf-8")
        SessionStart().run_hook(d, "startup")
        self.assertTrue(board.exists())

if __name__ == "__main__":
    unittest.main()
