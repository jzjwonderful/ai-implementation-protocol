"""0.8.0：会越写越大的内容拆开——主题文件、可复用实现条目、体积和引用检查、按改动的文件反查。"""
import json, os, subprocess, sys, tempfile, unittest
from datetime import date
from pathlib import Path
from _engine import ROOT, ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_check as chk, aip_init, aip_item as it, aip_lookup as lk, aip_upkeep as up, install_hooks
import aip_discovery as disc, aip_size as size, aip_update


def make_repo(version: str | None = None) -> Path:
    """scaffold 出来的是当前版本（已拆分）；version 给了就改成那一版。"""
    d = Path(tempfile.mkdtemp())
    aip_init.scaffold(d, ENGINE)
    if version is not None:
        cfg = d/".aip"/"config.yaml"
        text = cfg.read_text(encoding="utf-8")
        cfg.write_text(text.replace(f'aip_version: "{(ENGINE/"VERSION").read_text(encoding="utf-8").strip()}"',
                                    f'aip_version: "{version}"'), encoding="utf-8")
    return d


def topic(d: Path, name: str, read_when: str = "改安装器时", paths: str = "", body: str = "## 小节\n- 内容\n") -> Path:
    head = f"---\ntitle: {name}\nread_when: {read_when}\n" + (f"paths: {paths}\n" if paths else "") + "---\n\n"
    p = d/".aip"/"reference"/f"{name}.md"
    p.write_text(head + body, encoding="utf-8")
    return p


def conventions(d: Path, text: str) -> None:
    (d/".aip"/"conventions.md").write_text(text, encoding="utf-8")


def reuse(d: Path, title: str = "HTTP 重试", paths: str = "src/http.py", stamp: str = "20261001-100000") -> it.Item:
    return it.new_item(d, "reuse", title, meta={"paths": paths}, stamp=stamp,
                       body="- 钦定实现: `src/http.py` `retry_request`\n- 边界: 只管幂等 GET\n")


class Layout(unittest.TestCase):
    def test_fresh_scaffold_has_topic_and_reuse_dirs_and_passes(self):
        d = make_repo()
        self.assertTrue((d/".aip"/"reference").is_dir())
        self.assertTrue((d/".aip"/"reuse").is_dir())
        self.assertFalse((d/".aip"/"reference.md").exists())
        self.assertEqual(chk.run_all(d), [])

    def test_leftover_reference_md_is_red_after_tidy_up_only(self):
        d = make_repo()
        (d/".aip"/"reference.md").write_text("# 参照\n", encoding="utf-8")
        self.assertTrue(any("reference.md" in v and "拆" in v for v in chk.run_all(d)))
        old = make_repo("0.7.0")
        (old/".aip"/"reference.md").write_text("# 参照\n", encoding="utf-8")
        self.assertEqual(chk.run_all(old), [])

    def test_missing_reuse_dir_only_required_after_tidy_up(self):
        for v, red in (("0.7.0", False), (None, True)):
            d = make_repo(v)
            (d/".aip"/"reuse"/".gitkeep").unlink(); (d/".aip"/"reuse").rmdir()
            (d/".aip"/"reference"/".gitkeep").unlink(); (d/".aip"/"reference").rmdir()
            viol = chk.run_all(d)
            self.assertEqual(any("reuse/" in x for x in viol), red, viol)
            self.assertEqual(any("主题目录" in x for x in viol), red, viol)


class Sizes(unittest.TestCase):
    def test_must_read_total_and_section_limits(self):
        d = make_repo()
        conventions(d, "# 规约\n## 铁律\n" + "- 规则\n" * 1600)   # 一节 9600 多字
        viol = chk.check_sizes(d)
        self.assertTrue(any("conventions.md 有" in v and "8000" in v for v in viol), viol)
        self.assertTrue(any("「铁律」一节" in v and "3000" in v for v in viol), viol)

    def test_small_conventions_passes(self):
        d = make_repo()
        conventions(d, "# 规约\n## 铁律\n" + "- 规则\n" * 100)
        self.assertEqual(chk.check_sizes(d), [])

    def test_on_demand_file_line_and_table_limits(self):
        d = make_repo()
        topic(d, "大主题", body="正文\n" * 11000)
        topic(d, "长行", body="| a | " + "很长" * 600 + " |\n")
        topic(d, "长表", body="| a | b |\n|---|---|\n" + "| x | y |\n" * 31)
        viol = chk.check_sizes(d)
        self.assertTrue(any("大主题.md 有" in v and "30000" in v for v in viol), viol)
        self.assertTrue(any("长行.md 第" in v and "1000" in v for v in viol), viol)
        self.assertTrue(any("长表.md 最长的一张表有 31 行" in v for v in viol), viol)

    def test_table_at_limit_passes(self):
        d = make_repo()
        topic(d, "刚好", body="| a | b |\n|---|---|\n" + "| x | y |\n" * 30)
        self.assertEqual(chk.check_sizes(d), [])

    def test_untidied_repo_is_not_checked(self):
        d = make_repo("0.7.0")
        conventions(d, "x" * 20000)
        (d/".aip"/"reference.md").write_text("y\n" * 40000, encoding="utf-8")
        self.assertEqual(chk.check_sizes(d), [])

    def test_size_check_paths_covers_project_docs(self):
        d = make_repo()
        (d/"docs").mkdir()
        (d/"docs"/"big.md").write_text("z\n" * 16000, encoding="utf-8")
        self.assertEqual(chk.check_sizes(d), [])
        cfg = d/".aip"/"config.yaml"
        cfg.write_text(cfg.read_text(encoding="utf-8").replace('size_check_paths: ""', 'size_check_paths: "docs/**/*.md"'),
                       encoding="utf-8")
        self.assertTrue(any("docs/big.md" in v for v in chk.check_sizes(d)))

    def test_this_repo_skill_body_is_under_limit(self):
        self.assertEqual([m.over_text() for m in size.measures(ROOT) if m.rel.endswith("SKILL.md") and m.over], [])

    def test_managed_block_stays_short(self):
        # 托管块每次会话都进上下文
        self.assertLess(len(disc.managed_block()), 1500)


class Topics(unittest.TestCase):
    def test_topic_needs_title_and_short_read_when(self):
        d = make_repo()
        (d/".aip"/"reference"/"无头.md").write_text("# 无头\n", encoding="utf-8")
        topic(d, "啰嗦", read_when="改" * 81)
        viol = chk.check_topics(d)
        self.assertTrue(any("无头.md 文件头缺 title" in v for v in viol), viol)
        self.assertTrue(any("无头.md 文件头缺 read_when" in v for v in viol), viol)
        self.assertTrue(any("啰嗦.md 的 read_when" in v for v in viol), viol)

    def test_index_lists_topics_with_read_when(self):
        d = make_repo()
        topic(d, "环境变量", "改安装器或环境变量时")
        self.assertEqual(lk.index_lines(d), ["- 环境变量.md：改安装器或环境变量时"])

    def test_session_start_prints_topic_index(self):
        d = make_repo()
        topic(d, "环境变量", "改安装器或环境变量时")
        out = subprocess.run([sys.executable, str(SCRIPTS/"aip_session_start.py"), "--repo-root", str(d)],
                             input=json.dumps({"source": "startup"}), capture_output=True, text=True,
                             encoding="utf-8").stdout
        self.assertIn("主题资料", out)
        self.assertIn("- 环境变量.md：改安装器或环境变量时", out)
        self.assertIn("aip_lookup.py relevant", out)


class Links(unittest.TestCase):
    def test_broken_refs_are_red(self):
        d = make_repo()
        topic(d, "环境变量", body="## 代理\n- 内容\n")
        conventions(d, "# 规约\n## 铁律\n"
                       "- 见 `.aip/reference/环境变量.md` 的「代理」\n"           # 对
                       "- 见 `.aip/reference/没有.md`\n"                        # 文件没了
                       "- 见 `.aip/reference/环境变量.md`「镜像」\n"             # 节没了
                       "- 见 reference.md「环境划分」\n"                        # 旧文件已拆
                       "- 坑见 .aip/knowledge/20260101-000000_不存在的坑\n"     # 条目没了
                       "- 项目说明见 README.md「安装」\n")                      # 不在 .aip/ 下，不管
        viol = chk.check_links(d)
        self.assertEqual(len(viol), 4, viol)
        self.assertTrue(any("没有.md 不存在" in v for v in viol))
        self.assertTrue(any("「镜像」找不到这一节" in v for v in viol))
        self.assertTrue(any("reference.md「环境划分」" in v and "拆" in v for v in viol))
        self.assertTrue(any("不存在的坑" in v for v in viol))

    def test_existing_item_anchor_is_fine_and_decisions_are_history(self):
        d = make_repo()
        k = it.new_item(d, "knowledge", "锁的坑", "active", stamp="20260901-100000",
                        meta={"category": "c", "scope": "s"}, body="- 症状: x\n- 根因: y\n")
        conventions(d, f"# 规约\n## 铁律\n- 见 .aip/knowledge/{k.id}\n")
        it.new_item(d, "decision", "旧决策", stamp="20260901-100001", body="- 当时写在 reference.md「可复用实现」\n")
        self.assertEqual(chk.check_links(d), [])

    def test_untidied_repo_links_not_checked(self):
        d = make_repo("0.7.0")
        conventions(d, "- 见 reference.md「不存在」\n")
        self.assertEqual(chk.check_links(d), [])


class Reuse(unittest.TestCase):
    def test_reuse_item_passes_check(self):
        d = make_repo()
        reuse(d)
        self.assertEqual(chk.run_all(d), [])

    def test_reuse_needs_paths_and_sections(self):
        d = make_repo()
        it.new_item(d, "reuse", "空的", stamp="20261001-100000")
        viol = chk.check_items(d)
        self.assertTrue(any("缺 paths" in v for v in viol), viol)
        self.assertTrue(any("「钦定实现」" in v for v in viol), viol)

    def test_cli_new_reuse_requires_paths(self):
        d = make_repo()
        r = subprocess.run([sys.executable, str(SCRIPTS/"aip_item.py"), "--repo-root", str(d), "new", "--type", "reuse",
                            "--title", "HTTP重试"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 1); self.assertIn("--paths", r.stdout)
        r = subprocess.run([sys.executable, str(SCRIPTS/"aip_item.py"), "--repo-root", str(d), "new", "--type", "reuse",
                            "--title", "HTTP重试", "--paths", "src/http.py"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout)
        item = it.list_items(d, "reuse")[0]
        self.assertEqual((item.status, item.meta["paths"]), ("active", "src/http.py"))

    def test_superseded_reuse_needs_by(self):
        d = make_repo()
        r = reuse(d)
        with self.assertRaises(ValueError):
            it.set_status(d, r.id, "superseded")
        self.assertEqual(it.set_status(d, r.id, "superseded", by="换成 httpx 自带重试").meta["superseded_by"],
                         "换成 httpx 自带重试")

    def test_grep_finds_by_paths(self):
        d = make_repo()
        reuse(d, paths="src/net/http.py")
        self.assertEqual(len(it.search(it.list_items(d), "net/http")[0]), 1)


class Relevant(unittest.TestCase):
    def test_topics_and_items_by_paths_and_anchors(self):
        d = make_repo()
        topic(d, "环境变量", "改安装器时", paths="scripts/install*.py")
        topic(d, "前端", "改界面时", paths="web/")
        r = reuse(d, paths="src/http.py")
        k = it.new_item(d, "knowledge", "限量", "active", stamp="20260901-100000",
                        meta={"category": "c", "scope": "s", "paths": "src/ai/"}, body="- 症状: x\n- 根因: y\n")
        old = it.new_item(d, "knowledge", "作废的", "active", stamp="20260901-100001",
                          meta={"category": "c", "scope": "s", "paths": "src/ai/"}, body="- 症状: x\n- 根因: y\n")
        it.set_status(d, old.id, "superseded", by=k.id)
        anchored = it.new_item(d, "knowledge", "被锚的", "active", stamp="20260901-100002",
                               meta={"category": "c", "scope": "s"}, body="- 症状: x\n- 根因: y\n")
        (d/"src"/"tapd").mkdir(parents=True)
        (d/"src"/"tapd"/"upload.py").write_text(
            f"# 见 .aip/knowledge/{anchored.id}\n# 见 .aip/knowledge/20200101-000000_没有这条\n# 加粗的 **.aip/knowledge/{anchored.id}**\n", encoding="utf-8")
        hits, broken = lk.relevant(d, ["scripts/install_all.py", "src/http.py", "src/ai/runner.py",
                                       "src/tapd/upload.py"])
        targets = {h.target for h in hits}
        self.assertIn(".aip/reference/环境变量.md", targets)
        self.assertNotIn(".aip/reference/前端.md", targets)
        self.assertIn(r.path.relative_to(d).as_posix(), targets)
        self.assertTrue(any(k.slug in t for t in targets))
        self.assertFalse(any("作废的" in t for t in targets))
        self.assertTrue(any(anchored.slug in t for t in targets))
        self.assertEqual(broken, ["src/tapd/upload.py 里的锚点「20200101-000000_没有这条」找不到对应条目"])
        (d/"notes.md").write_text("例：.aip/knowledge/20260928-153012_举例用的\n", encoding="utf-8")
        self.assertEqual(lk.relevant(d, ["notes.md"])[1], [])   # 文档里举例的锚点不报

    def test_staged_files_in_pre_commit(self):
        d = make_repo()
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        topic(d, "环境变量", "改安装器时", paths="scripts/")
        (d/"scripts").mkdir(); (d/"scripts"/"install.py").write_text("x = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "scripts/install.py"], cwd=d, check=True)
        self.assertEqual(lk.staged_files(d), ["scripts/install.py"])
        out = subprocess.run([sys.executable, str(SCRIPTS/"aip_lookup.py"), "--repo-root", str(d), "relevant", "--staged"],
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(out.returncode, 0)
        self.assertIn("环境变量.md", out.stdout)

    def test_pre_commit_lists_relevant_but_never_blocks(self):
        body = install_hooks.pre_commit_body(ENGINE)
        self.assertIn("aip_lookup.py", body)
        self.assertIn("relevant --staged || true", body)


class ReuseUpkeep(unittest.TestCase):
    def git(self, d: Path, *args: str, when: str) -> None:
        env = {**os.environ, "GIT_AUTHOR_DATE": f"{when}T12:00:00", "GIT_COMMITTER_DATE": f"{when}T12:00:00"}
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=d, env=env,
                       check=True, capture_output=True)

    def test_reuse_whose_implementation_disappeared_is_flagged(self):
        d = make_repo()
        self.git(d, "init", "-q", "-b", "master", when="2026-09-01")
        (d/"src").mkdir(); (d/"src"/"http.py").write_text("def retry_request():\n    pass\n", encoding="utf-8")
        self.git(d, "add", "src/http.py", when="2026-09-01"); self.git(d, "commit", "-q", "-m", "a", when="2026-09-01")
        reuse(d, stamp="20260902-100000")
        self.assertFalse(any("钦定实现" in x for x in up.reminders(d, date(2026, 10, 1))))
        self.git(d, "rm", "-q", "src/http.py", when="2026-09-10"); self.git(d, "commit", "-q", "-m", "b", when="2026-09-10")
        due = up.reminders(d, date(2026, 10, 1))
        self.assertTrue(any("钦定实现" in x and "src/http.py" in x for x in due), due)


if __name__ == "__main__":
    unittest.main()
