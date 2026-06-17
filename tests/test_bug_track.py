import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AIP = REPO / "scripts" / "aip.py"


def run(*args):
    return subprocess.run([sys.executable, str(AIP), *args], capture_output=True, text=True)


def init_repo() -> Path:
    d = Path(tempfile.mkdtemp())
    assert run("init", "--repo-root", str(d)).returncode == 0
    return d


def start_bug(d: Path, bug_id="2026-06-17-x", title="Crash on save"):
    return run("bug", bug_id, "--title", title, "--repo-root", str(d))


class BugScaffold(unittest.TestCase):
    def test_bug_creates_light_slots_only(self):
        d = init_repo()
        self.assertEqual(start_bug(d).returncode, 0)
        fd = d / ".aip/features/2026-06-17-x"
        for f in ("report.md", "file_scope.yaml", "verification.md", "handoff.md", "session_log.md"):
            self.assertTrue((fd / f).exists(), f)
        for f in ("spec.md", "plan.md", "task_board.yaml"):
            self.assertFalse((fd / f).exists(), f)

    def test_bug_sets_kind_and_phase(self):
        d = init_repo()
        start_bug(d)
        ct = json.loads((d / ".aip/_runtime/current_task.json").read_text(encoding="utf-8"))
        self.assertEqual(ct["kind"], "bug")
        self.assertEqual(ct["current_phase"], "investigate")
        self.assertIn(".aip/features/2026-06-17-x/report.md", ct["must_read"])
        self.assertIsNone(ct["resolution"])

    def test_bug_refuses_existing_dir(self):
        d = init_repo()
        self.assertEqual(start_bug(d).returncode, 0)
        self.assertNotEqual(start_bug(d).returncode, 0)


SAMPLE_GATE_CONFIG = """\
truth_sources: []
gates:
  tests:
    cmd: "pytest"
lenses: []
iron_rules: []
process_skills: ""
"""

FILLED_REPORT = """\
# Bug Report: Crash on save

## 症状 / 复现
点保存即崩溃；`app save` 退出码 139。

## 竞争假设
1) 空指针 2) 并发写 3) 编码

## 根因
save() 未判空 buffer，`core/io.py:42` 解引用 NULL。

## 证据
gdb backtrace 指向 io.py:42；加日志复现 100%。

## 触类旁通 · 同类波及面
file_scope 内扫到 io.py:42 与 io.py:88 同模式，均修；范围外 net.py 已登记 findings.md。

## 修复选项
A 判空返回错误（选）；B 改调用方契约。

## 选定方案
A：在 io.py:42/88 加判空，最小且不改契约。

## 沉淀
K-007
"""

FILLED_VERIFICATION = """\
# Verification

## Regression

| repro | command | before | after | evidence |
|-------|---------|--------|-------|----------|
| save 崩溃 | pytest tests/test_io.py::test_save_null | fail | pass | 退出码 0 |

## Machine Gates

| gate | command | result | evidence |
|------|---------|--------|----------|
| tests | pytest | pass | 12 passed |

## Independent Review (fresh-eyes)
- 结论：✅可信
- 处置：无
"""


def write_aip(d: Path, name: str, text: str):
    (d / ".aip" / name).write_text(text, encoding="utf-8", newline="\n")


def set_status(d: Path, **kw):
    p = d / ".aip/_runtime/current_task.json"
    ct = json.loads(p.read_text(encoding="utf-8"))
    ct.update(kw)
    p.write_text(json.dumps(ct, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def finalize_bug(d, report=FILLED_REPORT, verification=FILLED_VERIFICATION, resolution="fixed"):
    """把一个已 scaffold 的 bug 填成可 done 的状态（handoff/file_scope 用模板默认占位即可，
    但 handoff 需补必需小节、findings 无待分类）。"""
    fd = d / ".aip/features/2026-06-17-x"
    (fd / "report.md").write_text(report, encoding="utf-8", newline="\n")
    (fd / "verification.md").write_text(verification, encoding="utf-8", newline="\n")
    # handoff 必需小节填齐（check 对两种 kind 一致校验 handoff）
    handoff = "\n".join(f"## {s}\nok" for s in (
        "Current Phase", "Current Task", "Completed Work", "Remaining Work",
        "Blockers", "Next Action", "Files Touched", "Verification Status"))
    (fd / "handoff.md").write_text(handoff + "\n", encoding="utf-8", newline="\n")
    write_aip(d, "config.yaml", SAMPLE_GATE_CONFIG)
    set_status(d, status="done", current_phase="verify", resolution=resolution)


def check(d):
    return run("check", "--repo-root", str(d))


class BugDoneGate(unittest.TestCase):
    def test_complete_fixed_bug_passes(self):
        d = init_repo()
        start_bug(d)
        finalize_bug(d)
        r = check(d)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_root_cause_fails(self):
        d = init_repo()
        start_bug(d)
        broken = FILLED_REPORT.replace("save() 未判空 buffer，`core/io.py:42` 解引用 NULL.", "").replace(
            "save() 未判空 buffer，`core/io.py:42` 解引用 NULL。", "")
        finalize_bug(d, report=broken)
        r = check(d)
        self.assertEqual(r.returncode, 1)
        self.assertIn("根因", r.stdout)

    def test_fixed_without_regression_fails(self):
        d = init_repo()
        start_bug(d)
        no_reg = FILLED_VERIFICATION.replace("## Regression", "## Was-Regression")
        finalize_bug(d, verification=no_reg)
        r = check(d)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Regression", r.stdout)

    def test_wont_fix_without_regression_passes(self):
        d = init_repo()
        start_bug(d)
        no_reg = FILLED_VERIFICATION.replace("## Regression", "## Was-Regression")
        finalize_bug(d, verification=no_reg, resolution="wont_fix")
        r = check(d)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_wont_fix_still_needs_root_cause(self):
        d = init_repo()
        start_bug(d)
        broken = FILLED_REPORT.replace("save() 未判空 buffer，`core/io.py:42` 解引用 NULL。", "")
        finalize_bug(d, report=broken, resolution="wont_fix")
        r = check(d)
        self.assertEqual(r.returncode, 1)

    def test_illegal_resolution_fails(self):
        d = init_repo()
        start_bug(d)
        finalize_bug(d)
        set_status(d, resolution="bogus")
        r = check(d)
        self.assertEqual(r.returncode, 1)

    def test_failed_machine_gate_caught(self):
        d = init_repo()
        start_bug(d)
        finalize_bug(d)
        fd = d / ".aip/features/2026-06-17-x"
        bad_ver = FILLED_VERIFICATION.replace(
            "| tests | pytest | pass | 12 passed |",
            "| tests | pytest | fail | 0 passed |",
        )
        (fd / "verification.md").write_text(bad_ver, encoding="utf-8", newline="\n")
        r = check(d)
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
