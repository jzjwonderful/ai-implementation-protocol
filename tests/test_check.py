import subprocess, sys, tempfile, unittest
from pathlib import Path
from _engine import ROOT, ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_check as chk, aip_init, aip_item as it

GOOD_BODY = "- 症状: 卡住\n- 根因: 锁没放\n"


def make_repo() -> Path:
    d = Path(tempfile.mkdtemp())
    aip_init.scaffold(d, ENGINE)
    return d


def knowledge(d: Path, title: str = "某坑", status: str = "active", body: str = GOOD_BODY, **meta) -> it.Item:
    meta = {"category": "other", "scope": "某模块", "last_reviewed": "2026-09-01", **meta}
    return it.new_item(d, "knowledge", title, status, meta=meta, body=body, stamp="20260901-100000")


class Layout(unittest.TestCase):
    def test_fresh_scaffold_passes(self):
        self.assertEqual(chk.run_all(make_repo()), [])

    def test_missing_doc_and_dir(self):
        d = make_repo()
        (d/".aip"/"reference.md").unlink()
        for p in (d/".aip"/"inbox").iterdir():
            p.unlink()
        (d/".aip"/"inbox").rmdir()
        viol = chk.run_all(d)
        self.assertTrue(any("reference.md" in v for v in viol))
        self.assertTrue(any("inbox/" in v for v in viol))

    def test_old_layout_points_to_migration_and_skips_the_rest(self):
        d = make_repo()
        (d/".aip"/"knowledge.md").write_text("# 旧\n", encoding="utf-8")
        (d/".aip"/"reference.md").unlink()
        viol = chk.run_all(d)
        self.assertEqual(len(viol), 1)
        self.assertIn("aip_migrate.py", viol[0])


class Names(unittest.TestCase):
    def test_bad_name_wrong_dir_and_bad_status(self):
        d = make_repo()
        k = d/".aip"/"knowledge"
        (k/"随手记.md").write_text("x\n", encoding="utf-8")
        (k/"20260901-100000_inbox_open_放错目录.md").write_text("x\n", encoding="utf-8")
        (k/"20260901-100000_knowledge_done_状态不对.md").write_text("x\n", encoding="utf-8")
        viol = chk.check_item_names(d)
        self.assertEqual(len(viol), 3, viol)
        self.assertTrue(any("随手记" in v and "不合格式" in v for v in viol))
        self.assertTrue(any("放错目录" in v and "不符" in v for v in viol))
        self.assertTrue(any("状态不对" in v and "只能是" in v for v in viol))

    def test_gitkeep_is_not_an_item(self):
        self.assertEqual(chk.check_item_names(make_repo()), [])


class Items(unittest.TestCase):
    def test_complete_knowledge_passes(self):
        d = make_repo(); knowledge(d)
        self.assertEqual(chk.check_items(d), [])

    def test_head_status_must_match_file_name(self):
        d = make_repo(); k = knowledge(d)
        k.path.write_text(k.path.read_text(encoding="utf-8").replace("status: active", "status: draft"),
                          encoding="utf-8")
        self.assertTrue(any("文件名里的状态是 active" in v for v in chk.check_items(d)))

    def test_missing_head_fields_and_body_sections(self):
        d = make_repo()
        it.new_item(d, "knowledge", "缺东西", "active", meta={"last_reviewed": "2026-09-01"},
                    body="- 症状: <可观察的表象>\n", stamp="20260901-100000")
        viol = chk.check_items(d)
        for word in ("category", "scope", "「症状」", "「根因」"):
            self.assertTrue(any(word in v for v in viol), (word, viol))

    def test_bad_review_date(self):
        d = make_repo(); knowledge(d, last_reviewed="六月")
        self.assertTrue(any("last_reviewed" in v and "不是" in v for v in chk.check_items(d)))

    def test_duplicate_id_after_a_bad_merge(self):
        d = make_repo(); k = knowledge(d)
        twin = k.path.with_name(k.path.name.replace("_active_", "_draft_"))
        twin.write_text(k.path.read_text(encoding="utf-8").replace("status: active", "status: draft"),
                        encoding="utf-8")
        self.assertTrue(any("标识重复" in v for v in chk.check_items(d)))

    def test_superseded_needs_a_target_text_is_fine_bad_id_is_not(self):
        d = make_repo(); knowledge(d, title="旧坑", status="superseded")
        self.assertTrue(any("superseded_by" in v for v in chk.check_items(d)))
        d = make_repo(); knowledge(d, title="旧坑", status="superseded", superseded_by="改用新机制后不再成立")
        self.assertEqual(chk.check_items(d), [])
        d = make_repo(); knowledge(d, title="旧坑", status="superseded", superseded_by="20990101-000000_没有")
        self.assertTrue(any("不存在的条目" in v for v in chk.check_items(d)))

    def test_related_must_point_to_a_real_item(self):
        d = make_repo()
        a = knowledge(d, title="甲")
        knowledge(d, title="乙", related=f"{a.id}, 20260101-000000_没有")
        viol = chk.check_items(d)
        self.assertEqual(len(viol), 1, viol)
        self.assertIn("20260101-000000_没有", viol[0])


class DoneTracks(unittest.TestCase):
    def test_leftover_done_track_file_is_flagged(self):
        d = make_repo()
        (d/".aip"/"tracks"/"20260901-100000_track_done_旧线.md").write_text(
            "---\ntitle: 旧线\nstatus: done\n---\n", encoding="utf-8")
        self.assertTrue(any("做完的在建线不留文件" in v for v in chk.check_item_names(d)))


class EngineCopies(unittest.TestCase):
    def engine_repo(self) -> Path:
        d = Path(tempfile.mkdtemp())
        src = d/chk.ENGINE_PKG/"skills"/"aip"
        (src/"scripts").mkdir(parents=True)
        (src/"SKILL.md").write_text("技能\n", encoding="utf-8")
        (src/"scripts"/"a.py").write_text("print(1)\n", encoding="utf-8")
        return d

    def install(self, d: Path, rel: str) -> Path:
        import shutil
        copy = d/rel
        shutil.copytree(d/chk.ENGINE_PKG/"skills"/"aip", copy)
        (copy/"SOURCE.json").write_text("{}\n", encoding="utf-8")          # 安装记录不算
        (copy/"scripts"/"__pycache__").mkdir()
        (copy/"scripts"/"__pycache__"/"a.pyc").write_bytes(b"x")            # 缓存不算
        return copy

    def test_matching_copies_pass_and_no_copy_is_fine(self):
        d = self.engine_repo()
        self.assertEqual(chk.check_engine_copies(d), [])
        self.install(d, ".claude/skills/aip"); self.install(d, ".codex/skills/aip")
        self.assertEqual(chk.check_engine_copies(d), [])

    def test_changed_or_missing_file_is_flagged(self):
        d = self.engine_repo()
        copy = self.install(d, ".claude/skills/aip")
        (d/chk.ENGINE_PKG/"skills"/"aip"/"scripts"/"a.py").write_text("print(2)\n", encoding="utf-8")
        (d/chk.ENGINE_PKG/"skills"/"aip"/"new.md").write_text("新\n", encoding="utf-8")
        [msg] = chk.check_engine_copies(d)
        self.assertIn(".claude/skills/aip", msg); self.assertIn("2 个文件", msg)
        self.assertIn("install_all.py --project", msg)

    def test_not_engine_repo_skipped(self):
        self.assertEqual(chk.check_engine_copies(Path(tempfile.mkdtemp())), [])

    def test_this_repo_copies_match_source(self):
        self.assertEqual(chk.check_engine_copies(ROOT), [])


class OrphanSlots(unittest.TestCase):
    def test_flags_old_file(self):
        d = make_repo(); (d/".aip"/"handoff.md").write_text("x\n", encoding="utf-8")
        self.assertTrue(any("handoff.md" in v for v in chk.check_no_orphan_slots(d)))
    def test_clean_ok(self):
        self.assertEqual(chk.check_no_orphan_slots(make_repo()), [])


class NoReminders(unittest.TestCase):
    def test_flag_skips_reminders(self):
        d = make_repo()
        (d/".aip"/"config.yaml").write_text("gates:\n", encoding="utf-8")   # 没记整份 review，会被提醒
        run = lambda *extra: subprocess.run([sys.executable, str(SCRIPTS/"aip_check.py"), "--repo-root", str(d), *extra],
                                            capture_output=True, text=True, encoding="utf-8").stdout
        self.assertIn("到期提醒", run())
        self.assertNotIn("到期提醒", run("--no-reminders"))


class EngineVersions(unittest.TestCase):
    def _mk(self, claude="0.3.0", codex="0.3.0", grok="0.3.0", version="0.3.0"):
        d = make_repo(); pkg = d/"plugins"/"ai-implementation-protocol"
        (pkg/"skills"/"aip").mkdir(parents=True)
        (pkg/"skills"/"aip"/"VERSION").write_text(version + "\n", encoding="utf-8")
        for sub, ver in [(".claude-plugin", claude), (".codex-plugin", codex), (".grok-plugin", grok)]:
            (pkg/sub).mkdir()
            (pkg/sub/"plugin.json").write_text('{"name": "x", "version": "%s"}\n' % ver, encoding="utf-8")
        return d
    def test_consistent_ok(self):
        self.assertEqual(chk.check_engine_versions(self._mk()), [])
    def test_manifest_drift(self):
        viol = chk.check_engine_versions(self._mk(codex="0.2.1"))
        self.assertTrue(any(".codex-plugin" in v for v in viol))
    def test_grok_manifest_drift(self):
        viol = chk.check_engine_versions(self._mk(grok="0.2.1"))
        self.assertTrue(any(".grok-plugin" in v for v in viol))
    def test_missing_version_file(self):
        d = self._mk(); (d/"plugins"/"ai-implementation-protocol"/"skills"/"aip"/"VERSION").unlink()
        self.assertTrue(any("VERSION" in v for v in chk.check_engine_versions(d)))
    def test_consumer_repo_skipped(self):
        self.assertEqual(chk.check_engine_versions(make_repo()), [])
    def test_own_repo_consistent(self):
        # 引擎仓库自身：各端 plugin.json 必须和 skills/aip/VERSION 一致。
        self.assertEqual(chk.check_engine_versions(ROOT), [])

if __name__ == "__main__":
    unittest.main()
