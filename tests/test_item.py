"""条目一条一个文件：文件名、文件头、新建、改状态、查找。"""
import subprocess, sys, tempfile, unittest
from datetime import date
from pathlib import Path
from _engine import ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_item as it


def repo() -> Path:
    return Path(tempfile.mkdtemp())


class Slug(unittest.TestCase):
    def test_spaces_between_chinese_and_english_are_dropped(self):
        self.assertEqual(it.slugify("新增 AI 客户端支持时不要只改 installer"), "新增AI客户端支持时不要只改installer")

    def test_english_words_keep_a_hyphen(self):
        self.assertEqual(it.slugify("skills via kite"), "skills-via-kite")

    def test_brackets_and_windows_unsafe_chars_removed(self):
        self.assertEqual(it.slugify("gbrain-standalone（2026-09-19 开工）"), "gbrain-standalone")
        self.assertEqual(it.slugify('读 `a:b` 的 "c"/d?'), "读ab的cd")
        self.assertEqual(it.slugify("装成项目级技能：用 `--project`，钩子"), "装成项目级技能用-project钩子")

    def test_cut_does_not_leave_half_an_english_word(self):
        s = it.slugify("超过二十四个字的标题一定会被截断截断截断 installer")
        self.assertLessEqual(len(s), it.SLUG_LIMIT)
        self.assertFalse(s.endswith(("i", "in", "ins")))

    def test_long_title_is_cut_at_a_clause_not_mid_sentence(self):
        self.assertEqual(it.slugify("引擎搬家后合并旧分支，危险的不是 git 冲突而是没冲突的路径假设"), "引擎搬家后合并旧分支")
        self.assertEqual(it.slugify("复核提醒按「代码有没有动」判定；装好的技能自己查更新、自己更新"), "复核提醒按代码有没有动判定")

    def test_too_short_first_clause_falls_back_to_hard_cut(self):
        s = it.slugify("注意：超过二十四个字的标题一定会被截断截断截断截断截断")
        self.assertEqual(len(s), it.SLUG_LIMIT)

    def test_empty_title_still_gives_a_name(self):
        self.assertEqual(it.slugify("（）"), "untitled")


class NewAndRead(unittest.TestCase):
    def test_new_item_name_head_and_template_body(self):
        d = repo()
        i = it.new_item(d, "knowledge", "gbrain 健康分是扣分制", stamp="20260928-153012",
                        meta={"category": "other", "scope": "看健康分的人"}, engine=ENGINE)
        self.assertEqual(i.path.name, "20260928-153012_knowledge_draft_gbrain健康分是扣分制.md")
        self.assertEqual(i.path.parent, d / ".aip" / "knowledge")
        back = it.read_item(i.path)
        self.assertEqual(back.meta["status"], "draft")          # 状态在文件头里也有
        self.assertEqual(back.meta["title"], "gbrain 健康分是扣分制")
        self.assertEqual(back.meta["last_reviewed"], date.today().isoformat())
        self.assertIn("- 症状:", back.body)
        self.assertEqual(back.id, "20260928-153012_gbrain健康分是扣分制")

    def test_same_second_different_slug_is_fine_same_slug_is_not(self):
        d = repo()
        it.new_item(d, "inbox", "甲问题", stamp="20260928-153012")
        it.new_item(d, "inbox", "乙问题", stamp="20260928-153012")
        with self.assertRaises(FileExistsError):
            it.new_item(d, "inbox", "甲问题", stamp="20260928-153012", status="closed")

    def test_given_slug_must_be_short(self):
        with self.assertRaises(ValueError):
            it.new_item(repo(), "inbox", "x", slug="这个简述写得太长了已经远远超过二十四个字的上限了吧真的")

    def test_cli_asks_for_a_slug_when_title_is_long(self):
        d = repo()
        title = "在 AI 会话里重启本机 Kite，会把会话的环境变量和当前目录带进 Kite"
        run = lambda *extra: subprocess.run(
            [sys.executable, str(SCRIPTS/"aip_item.py"), "--repo-root", str(d), "new", "--type", "inbox",
             "--title", title, *extra], capture_output=True, text=True, encoding="utf-8")
        r = run()
        self.assertEqual(r.returncode, 1)
        self.assertIn("--slug", r.stdout)
        self.assertFalse(it.list_items(d))
        r = run("--slug", "会话里重启Kite会带走会话环境")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(it.list_items(d)[0].slug, "会话里重启Kite会带走会话环境")

    def test_bad_type_and_status_rejected(self):
        with self.assertRaises(ValueError):
            it.new_item(repo(), "note", "x")
        with self.assertRaises(ValueError):
            it.new_item(repo(), "inbox", "x", status="active")

    def test_parse_name(self):
        self.assertEqual(it.parse_name("20260928-153012_inbox_open_两个桥互判失败.md"),
                         ("20260928-153012", "inbox", "open", "两个桥互判失败"))
        self.assertIsNone(it.parse_name("20260928_inbox_open_x.md"))
        self.assertIsNone(it.parse_name("20261399-153012_inbox_open_x.md"))
        self.assertIsNone(it.parse_name("README.md"))


class Find(unittest.TestCase):
    def setUp(self):
        self.d = repo()
        self.a = it.new_item(self.d, "decision", "选文件不选数据库", stamp="20261001-100000",
                             meta={"aliases": "ADR-7"})

    def test_by_full_id_filename_or_alias(self):
        items = it.list_items(self.d)
        for ref in ["20261001-100000_选文件不选数据库", self.a.path.name, "ADR-7", "`ADR-7`"]:
            self.assertEqual(it.find(items, ref).id, self.a.id, ref)

    def test_timestamp_alone_is_not_a_reference(self):
        with self.assertRaises(LookupError):
            it.find(it.list_items(self.d), "20261001-100000")


class Status(unittest.TestCase):
    def test_rename_keeps_id_and_updates_head(self):
        d = repo()
        i = it.new_item(d, "inbox", "某问题", stamp="20261001-100000")
        moved = it.set_status(d, i.id, "closed")
        self.assertFalse(i.path.exists())
        self.assertEqual(moved.path.name, "20261001-100000_inbox_closed_某问题.md")
        self.assertEqual(it.read_item(moved.path).meta["status"], "closed")
        self.assertEqual(moved.id, i.id)

    def test_superseded_needs_by_and_records_it(self):
        d = repo()
        old = it.new_item(d, "decision", "旧决策", stamp="20261001-100000")
        new = it.new_item(d, "decision", "新决策", stamp="20261001-110000")
        with self.assertRaises(ValueError):
            it.set_status(d, old.id, "superseded")
        done = it.set_status(d, old.id, "superseded", by=new.id)
        self.assertEqual(it.read_item(done.path).meta["superseded_by"], new.id)

    def test_superseded_by_a_mechanism_can_be_text(self):
        d = repo()
        k = it.new_item(d, "knowledge", "旧坑", stamp="20261001-100000")
        done = it.set_status(d, k.id, "superseded", by="改用服务端鉴权后不再成立")
        self.assertEqual(done.meta["superseded_by"], "改用服务端鉴权后不再成立")
        with self.assertRaises(LookupError):  # 像标识却找不到：多半写错了
            it.set_status(d, done.id, "superseded", by="20990101-000000_不存在")

    def test_reviewed_only_for_knowledge(self):
        d = repo()
        k = it.new_item(d, "knowledge", "某坑", stamp="20261001-100000", meta={"last_reviewed": "2026-01-01"})
        self.assertEqual(it.mark_reviewed(d, k.id, date(2026, 10, 1)).meta["last_reviewed"], "2026-10-01")
        t = it.new_item(d, "track", "某线", stamp="20261001-100000")
        with self.assertRaises(ValueError):
            it.mark_reviewed(d, t.id)

    def test_done_track_is_deleted(self):
        d = repo()
        t = it.new_item(d, "track", "某线", stamp="20261001-100000")
        gone = it.set_status(d, t.id, "done")
        self.assertFalse(gone.path.exists())
        self.assertEqual(it.list_items(d), [])
        with self.assertRaises(ValueError):
            it.new_item(d, "track", "某线", status="done")       # 不能新建做完的线


def cli(d: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS/"aip_item.py"), "--repo-root", str(d), *args],
                          capture_output=True, text=True, encoding="utf-8")


class Cli(unittest.TestCase):
    def test_knowledge_needs_category_and_scope(self):
        d = repo()
        r = cli(d, "new", "--type", "knowledge", "--title", "某坑")
        self.assertEqual(r.returncode, 1); self.assertIn("--category", r.stdout)
        self.assertFalse(it.list_items(d))
        r = cli(d, "new", "--type", "knowledge", "--title", "某坑", "--category", "部署", "--scope", "安装器")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_list_grep_looks_at_title_category_and_scope(self):
        d = repo()
        it.new_item(d, "knowledge", "钩子路径失效", stamp="20261001-100000",
                    meta={"category": "Deployment", "scope": "项目级安装"})
        it.new_item(d, "knowledge", "别的坑", stamp="20261001-100001", meta={"category": "other", "scope": "x"})
        for kw in ("钩子", "deploy", "项目级"):
            out = cli(d, "list", "--grep", kw).stdout
            self.assertIn("钩子路径失效", out, kw); self.assertNotIn("别的坑", out, kw)

    def test_status_done_on_track_says_deleted(self):
        d = repo()
        t = it.new_item(d, "track", "某线", stamp="20261001-100000")
        r = cli(d, "status", t.id, "done")
        self.assertEqual(r.returncode, 0, r.stdout); self.assertIn("已删除", r.stdout)


if __name__ == "__main__":
    unittest.main()
