import sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import aip_overview as ov

def repo():
    d = Path(tempfile.mkdtemp()); a = d/".aip"; a.mkdir()
    (a/"OVERVIEW.md").write_text(
        "# 总览\n## 在建（多线看板）\n### ▶[active] t1 手写内容\n\n"
        "<!-- AIP:AUTO-DIGEST:BEGIN (勿手改) -->\n旧摘要\n<!-- AIP:AUTO-DIGEST:END -->\n",
        encoding="utf-8")
    (a/"knowledge.md").write_text("# k\n\n## 类目\nother\n\n## K-001: 某坑\n- 分类: other\n- 状态: active\n", encoding="utf-8")
    (a/"decisions.md").write_text("# 决策\n\n## ADR-1: 选了 A\n正文\n", encoding="utf-8")
    (a/"reference.md").write_text("# 参照\n\n## 领域概念\n### 订单\n说明\n", encoding="utf-8")
    return d

def repo_with_boilerplate():
    """decisions.md 含真实 ADR + 格式节 + 围栏代码块中的占位行"""
    d = Path(tempfile.mkdtemp()); a = d/".aip"; a.mkdir()
    (a/"OVERVIEW.md").write_text(
        "# 总览\n## 在建（多线看板）\n\n"
        "<!-- AIP:AUTO-DIGEST:BEGIN (勿手改) -->\n旧摘要\n<!-- AIP:AUTO-DIGEST:END -->\n",
        encoding="utf-8")
    (a/"knowledge.md").write_text("# k\n", encoding="utf-8")
    (a/"decisions.md").write_text(
        "# 决策记录\n\n"
        "## 格式\n"
        "```\n"
        "## ADR-N：<标题>\n"
        "- 日期 / 状态：YYYY-MM-DD\n"
        "```\n\n"
        "## ADR-1: 选了 A\n"
        "正文内容\n",
        encoding="utf-8")
    (a/"reference.md").write_text("# 参照\n", encoding="utf-8")
    return d

class Overview(unittest.TestCase):
    def test_digest_pulls_from_docs(self):
        dg = ov.build_digest(repo())
        self.assertIn("K-001", dg); self.assertIn("ADR-1", dg)
    def test_rebuild_keeps_handwritten_board(self):
        d = repo(); ov.rebuild_overview(d)
        t = (d/".aip"/"OVERVIEW.md").read_text(encoding="utf-8")
        self.assertIn("▶[active] t1 手写内容", t)     # 手写看板保留
        self.assertNotIn("旧摘要", t)                  # AUTO 区被刷新
        self.assertIn("K-001", t)
        self.assertEqual(t.count("AIP:AUTO-DIGEST:BEGIN"), 1)
    def test_digest_skips_boilerplate(self):
        """格式节、围栏代码块内的占位行不得出现在近期决策摘要中"""
        dg = ov.build_digest(repo_with_boilerplate())
        self.assertIn("ADR-1", dg)
        self.assertNotIn("格式", dg)
        self.assertNotIn("ADR-N", dg)

if __name__ == "__main__":
    unittest.main()
