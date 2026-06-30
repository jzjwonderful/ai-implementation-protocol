import sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import aip_knowledge as k

SAMPLE = """# 知识库

## 类目
build | other

## K-001: pnpm 在 Windows 下软链报错
- 分类: build
- 状态: active
- 症状: EPERM
- 根因: 软链策略与文件锁冲突
- 证据: ci 日志
- 适用范围: 仅 Windows runner + pnpm<9
- 最后复核: 2026-06-01

## K-002: 偶现超时
- 分类: other
- 状态: draft
- 症状: 偶现超时
- 根因: 疑似连接池耗尽（未验证）
- 证据: 局部日志
- 适用范围: 高并发下
- 最后复核: 2026-06-25
"""

class KnowledgeIndex(unittest.TestCase):
    def _b(self):
        d = Path(tempfile.mkdtemp()); (d/".aip").mkdir()
        (d/".aip"/"knowledge.md").write_text(SAMPLE, encoding="utf-8"); return d
    def test_header_has_apply_scope(self):
        header = [l for l in k.expected_index_text(self._b()).splitlines() if l.startswith("| ID")][0]
        self.assertIn("适用范围", header)
    def test_valid_gfm_table(self):
        out = k.expected_index_text(self._b()).splitlines()
        hdr = next(i for i, l in enumerate(out) if l.startswith("| ID"))
        sep = out[hdr + 1]
        self.assertEqual(set(sep) - set(" "), {"|", "-"})  # 分隔行只由 | - 空格 组成
    def test_draft_preserved(self):
        line = [l for l in k.expected_index_text(self._b()).splitlines() if l.startswith("| K-002")][0]
        self.assertIn("draft", line)
    def test_row_order(self):
        line = [l for l in k.expected_index_text(self._b()).splitlines() if l.startswith("| K-001")][0]
        cols = [c.strip() for c in line.split("|")]  # 行首/尾的 | 会产生空串，列从下标 1 起
        self.assertEqual(cols[2], "build"); self.assertEqual(cols[3], "active")
        self.assertEqual(cols[4], "仅 Windows runner + pnpm<9"); self.assertEqual(cols[6], "2026-06-01")

if __name__ == "__main__":
    unittest.main()
