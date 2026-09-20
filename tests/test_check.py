import sys, tempfile, unittest
from pathlib import Path
from _engine import ROOT, ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_check as chk, aip_knowledge as k

def make_repo() -> Path:
    d = Path(tempfile.mkdtemp()); aip = d/".aip"; aip.mkdir()
    for n in ["OVERVIEW.md","decisions.md","reference.md","inbox.md","conventions.md","config.yaml"]:
        (aip/n).write_text("# stub\n", encoding="utf-8")
    (aip/"knowledge.md").write_text("# 知识库\n\n## 类目\nother\n", encoding="utf-8")
    (aip/"knowledge_index.md").write_text(k.expected_index_text(d), encoding="utf-8")
    return d

class LivingAndIndex(unittest.TestCase):
    def test_clean_passes(self):
        d = make_repo()
        self.assertEqual(chk.check_living_files(d), [])
        self.assertEqual(chk.check_index_sync(d), [])
    def test_missing_living(self):
        d = make_repo(); (d/".aip"/"decisions.md").unlink()
        self.assertTrue(any("decisions.md" in v for v in chk.check_living_files(d)))
    def test_stale_index(self):
        d = make_repo(); (d/".aip"/"knowledge_index.md").write_text("# 旧\n", encoding="utf-8")
        self.assertTrue(chk.check_index_sync(d))

class KnowledgeFields(unittest.TestCase):
    def test_missing_field(self):
        d = make_repo()
        (d/".aip"/"knowledge.md").write_text(
            "# k\n\n## 类目\nother\n\n## K-001: 缺\n- 分类: other\n- 状态: active\n", encoding="utf-8")
        viol = chk.check_knowledge_fields(d)
        self.assertTrue(any("症状" in v for v in viol))
    def test_complete_ok(self):
        d = make_repo()
        (d/".aip"/"knowledge.md").write_text(
            "# k\n\n## 类目\nother\n\n## K-001: 全\n- 分类: other\n- 状态: active\n- 症状: x\n"
            "- 根因: y\n- 证据: z\n- 适用范围: w\n- 最后复核: 2026-06-25\n", encoding="utf-8")
        self.assertEqual(chk.check_knowledge_fields(d), [])

class OrphanSlots(unittest.TestCase):
    def test_flags_old_file(self):
        d = make_repo(); (d/".aip"/"handoff.md").write_text("x\n", encoding="utf-8")
        self.assertTrue(any("handoff.md" in v for v in chk.check_no_orphan_slots(d)))
    def test_clean_ok(self):
        self.assertEqual(chk.check_no_orphan_slots(make_repo()), [])

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
