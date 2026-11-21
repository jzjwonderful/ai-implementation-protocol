"""0.8.2：tech-ai-kits、docflow-agent 按 0.8.1 整理后反馈的误报。"""
import sys, unittest
from _engine import SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_check as chk, aip_item as it, aip_lookup as lk, aip_upkeep as up
from test_fix081 import knowledge, make_repo, topic
import test_upkeep_git as ug


def targets(d, changed):
    return " ".join(h.target for h in lk.relevant(d, changed)[0])


class Relevant(unittest.TestCase):
    def test_bare_filenames_and_dirs_in_body_do_not_match(self):
        d = make_repo()
        (d/"src"/"runner").mkdir(parents=True)
        k = knowledge(d, "正文提了一串", body="- 症状: x\n- 根因: 改 `SKILL.md`、`kb-v2.md`、`.aip/knowledge/`、`src/runner`\n")
        for f in (".claude/skills/kit-dev/SKILL.md", "docs/kb-v2.md", ".aip/knowledge/20260901-100000_x.md",
                  "src/runner/main.py"):
            self.assertNotIn(k.slug, targets(d, [f]), f)

    def test_body_paths_only_match_changed_code(self):
        d = make_repo()
        k = knowledge(d, "影响一栏", body="- 症状: x\n- 根因: `docs/specs/kb-v2.md`、`.aip/config.yaml`、`src/runner.py`\n")
        self.assertNotIn(k.slug, targets(d, ["docs/specs/kb-v2.md"]))
        self.assertNotIn(k.slug, targets(d, [".aip/config.yaml"]))
        self.assertIn(k.slug, targets(d, ["src/runner.py"]))

    def test_header_paths_still_match_any_file(self):
        d = make_repo()
        k = knowledge(d, "文件头写了文档", paths="docs/specs/")
        self.assertIn(k.slug, targets(d, ["docs/specs/kb-v2.md"]))


class Links(unittest.TestCase):
    def test_history_docs_may_mention_old_paths(self):
        d = make_repo()
        (d/".aip"/"specs").mkdir()
        (d/".aip"/"specs"/"规格.md").write_text(
            "当时改了 `.aip/reference.md` 和 .aip/OVERVIEW.md\n见 .aip/knowledge/20200101-000000_没有\n",
            encoding="utf-8")
        conv = d/".aip"/"conventions.md"
        conv.write_text(conv.read_text(encoding="utf-8") + "\n先读 `.aip/reference.md`\n", encoding="utf-8")
        viol = chk.check_links(d)
        self.assertFalse(any("规格.md" in v and "reference.md" in v for v in viol), viol)
        self.assertFalse(any("OVERVIEW" in v for v in viol), viol)
        self.assertTrue(any("规格.md" in v and "20200101-000000_没有" in v for v in viol), viol)  # 锚点照查
        self.assertTrue(any("conventions.md" in v and "reference.md" in v for v in viol), viol)

    def test_self_pointer_with_de_needs_a_section_word(self):
        d = make_repo()
        topic(d, "部署", "## 镜像\n- 只读分享和本文的「邀请加入」是两回事\n- 见本文的「回滚」一节\n- 见本文「发布」\n")
        viol = chk.check_links(d)
        self.assertEqual(len(viol), 2, viol)
        self.assertFalse(any("邀请加入" in v for v in viol))


class EngineCopies(unittest.TestCase):
    def repo(self, with_source: bool):
        d = ug.make_repo(ug.entry("引擎拷贝的坑", "2026-06-15", "`.claude/skills/aip/scripts/aip_check.py`"))
        files = {".claude/skills/aip/scripts/aip_check.py": "x = 1\n"}
        if with_source:
            files[f"{up.ENGINE_SOURCE}/scripts/aip_check.py"] = "x = 1\n"
        ug.commit(d, "2026-06-02", files)
        ug.commit(d, "2026-07-01", {".claude/skills/aip/scripts/aip_check.py": "x = 2\n"})
        # 0.8.3：「代码改过」的提示挪到了反查，这条规矩在那边查
        return [h.reason for h in lk.relevant(d, [".claude/skills/aip/scripts/aip_check.py"])[0]
                if "改过" in h.reason]

    def test_copy_in_engine_repo_is_not_code(self):
        self.assertEqual(self.repo(with_source=True), [])

    def test_copy_elsewhere_is_code(self):
        self.assertTrue(self.repo(with_source=False))


class Template(unittest.TestCase):
    def test_knowledge_has_optional_how_to(self):
        d = make_repo()
        k = it.new_item(d, "knowledge", "操作步骤", "active", stamp="20260901-100000",
                        meta={"category": "c", "scope": "s"})
        self.assertIn("- 做法:", k.path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
