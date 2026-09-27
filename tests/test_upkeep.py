import io, subprocess, sys, tempfile, unittest
from datetime import date
from pathlib import Path
from _engine import ROOT, ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_upkeep as up, aip_check as chk, aip_overview as ov

TODAY = date(2026, 9, 27)

def entry(kid: str, status: str, seen: str) -> str:
    return (f"## {kid}: 某坑\n- 分类: other\n- 状态: {status}\n- 症状: x\n- 根因: y\n"
            f"- 证据: z\n- 适用范围: w\n- 最后复核: {seen}\n\n")

def make_repo(entries: str = "", config: str = 'review_last_full: "2026-09-20"\n') -> Path:
    d = Path(tempfile.mkdtemp()); a = d/".aip"; a.mkdir()
    (a/"OVERVIEW.md").write_text("# 总览\n", encoding="utf-8")
    (a/"knowledge.md").write_text("# k\n\n## 类目\nother\n\n" + entries, encoding="utf-8")
    (a/"config.yaml").write_text(config, encoding="utf-8")
    return d

class Reminders(unittest.TestCase):
    def test_fresh_repo_has_nothing_due(self):
        d = make_repo(entry("K-001", "active", "2026-09-01"))
        self.assertEqual(up.reminders(d, TODAY), [])

    def test_stale_active_knowledge_is_listed(self):
        d = make_repo(entry("K-001", "active", "2026-06-17") + entry("K-002", "active", "2026-09-01"))
        due = up.reminders(d, TODAY)
        self.assertEqual(len(due), 1)
        self.assertIn("K-001", due[0]); self.assertNotIn("K-002", due[0])

    def test_boundary_is_ninety_days(self):
        d = make_repo(entry("K-001", "active", "2026-06-29"))   # 正好 90 天
        self.assertEqual(up.reminders(d, TODAY), [])
        d = make_repo(entry("K-001", "active", "2026-06-28"))   # 91 天
        self.assertTrue(up.reminders(d, TODAY))

    def test_fixed_and_superseded_are_not_nagged(self):
        d = make_repo(entry("K-001", "fixed（已修，2026-06-28）", "2026-06-28")
                      + entry("K-002", "superseded(by K-003)", "2026-01-01"))
        self.assertEqual(up.reminders(d, TODAY), [])

    def test_drafts_are_always_listed(self):
        d = make_repo(entry("K-001", "draft", "2026-09-26"))
        due = up.reminders(d, TODAY)
        self.assertTrue(any("draft" in x and "K-001" in x for x in due))

    def test_long_lists_are_truncated(self):
        d = make_repo("".join(entry(f"K-{i:03d}", "active", "2026-01-01") for i in range(1, 12)))
        due = up.reminders(d, TODAY)[0]
        self.assertIn("等 11 条", due); self.assertNotIn("K-011", due)

    def test_full_review_overdue_missing_and_blank(self):
        self.assertTrue(any("已 38 天" in x for x in up.reminders(make_repo(config='review_last_full: "2026-08-20"\n'), TODAY)))
        self.assertTrue(any("没记上次整份 review" in x for x in up.reminders(make_repo(config="gates:\n"), TODAY)))
        self.assertTrue(any("没记上次整份 review" in x for x in up.reminders(make_repo(config='review_last_full: ""\n'), TODAY)))
        self.assertEqual(up.reminders(make_repo(config="review_last_full: 2026-09-20  # 注释\n"), TODAY), [])

class StatusCheck(unittest.TestCase):
    def test_allowed_status_words_pass(self):
        d = make_repo(entry("K-001", "active", "2026-09-01") + entry("K-002", "fixed（已修，2026-06-28）", "2026-06-28")
                      + entry("K-003", "superseded(by K-001)", "2026-06-01") + entry("K-004", "draft", "2026-09-01"))
        self.assertEqual(chk.check_knowledge_status(d), [])

    def test_unknown_status_and_bad_date_fail(self):
        d = make_repo(entry("K-001", "已修", "2026-09-01") + entry("K-002", "active", "六月"))
        viol = chk.check_knowledge_status(d)
        self.assertTrue(any("K-001" in v and "状态" in v for v in viol))
        self.assertTrue(any("K-002" in v and "最后复核" in v for v in viol))

class SessionStart(unittest.TestCase):
    def run_hook(self, repo: Path, source: str) -> str:
        return subprocess.run(
            [sys.executable, str(SCRIPTS/"aip_session_start.py"), "--repo-root", str(repo)],
            input=f'{{"source": "{source}"}}', capture_output=True, text=True, encoding="utf-8").stdout

    def test_startup_prints_reminders_but_compact_does_not(self):
        d = make_repo(entry("K-001", "active", "2020-01-01"))
        self.assertIn("到期提醒", self.run_hook(d, "startup"))
        self.assertNotIn("到期提醒", self.run_hook(d, "compact"))

class ReferenceDigest(unittest.TestCase):
    def test_template_tables_are_counted_and_placeholders_skipped(self):
        text = (ENGINE/"templates"/"reference-template.md").read_text(encoding="utf-8")
        self.assertEqual(ov.reference_sections(text), [])
        filled = text + "\n## 可复用实现（补充）\n| 能力 | 钦定实现 |\n|---|---|\n| 重试 | utils/retry.py |\n| 分页 | utils/paging.py |\n- 另一个\n"
        self.assertEqual(ov.reference_sections(filled), ["可复用实现（补充）（3）"])

    def test_subheadings_still_count(self):
        self.assertEqual(ov.reference_sections("# 参照\n## 领域概念\n### 订单\n说明\n"), ["领域概念（1）"])

if __name__ == "__main__":
    unittest.main()
