# AIP Bug 轨道 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `$aip bug <id>` 轻量轨道，把"根因分析 → 修复 → 回归验证"连贯走完，并用 `aip check` 的 bug 分叉强制保障修复完整性。

**Architecture:** 路线 A——bug 是一种新的工作单元类型，`current_task.json` 加 `kind` 字段，复用 resume/handoff/knowledge 机器，仅在脚手架槽位与 `aip check` 完成闸门上按 `kind` 分叉。bug 包砍掉 spec/plan/task_board，进度由 `current_task.current_phase` 跟踪，核心活文档是 `report.md`。

**Tech Stack:** Python 3（标准库，无第三方依赖）、unittest、Markdown/YAML 模板。

## Global Constraints

- 文件编码 UTF-8 无 BOM，换行 `\n`（`write_text` 已固定 `newline="\n"`）。
- 真源在根目录 `scripts/templates/docs/schemas/`；改完必须跑 `python scripts/sync_plugin.py` 再生 plugin 副本。
- `skills/` 与 `commands/` 是 plugin 独有，直接改 `plugins/ai-implementation-protocol/` 下副本（不被 sync 覆盖）。
- 无第三方依赖；YAML 用现有轻量行解析风格，不引 PyYAML。
- 向后兼容：`current_task.json` 无 `kind` 字段一律视为 `feature`，既有行为零变化。
- 未经用户授权不得 `git commit`。
- bug id 形如 `YYYY-MM-DD-<kebab-slug>`，复用 `feature_dir()`，目录已存在则报错不覆盖。

---

### Task 1: Bug 脚手架（`$aip bug` 建出 bug 工作包）

**Files:**
- Create: `templates/bug-report-template.md`
- Create: `templates/bug-verification-template.md`
- Create: `scripts/aip_start_bug.py`
- Modify: `scripts/_aip_common.py`（新增 `REQUIRED_BUG_FILES`；`AIP_SLOT_FILENAMES` 加 `report.md`）
- Modify: `scripts/aip.py:30-35,54-68`（新增 `bug` 子命令 + 路由）
- Test: `tests/test_bug_track.py`

**Interfaces:**
- Consumes: `_aip_common.{feature_dir, current_task_path, iso_now, write_json, write_text, AIP_DIR}`
- Produces:
  - `REQUIRED_BUG_FILES = ["report.md","file_scope.yaml","handoff.md","verification.md","session_log.md"]`
  - `aip_start_bug.py` CLI: `--repo-root --bug-id --title --template-root`，建包并写 `current_task.json`（`kind="bug", status="planned", current_phase="investigate", resolution=None`）
  - `aip.py bug <id> [--title]` 子命令

- [ ] **Step 1: 写失败测试 `tests/test_bug_track.py`**

```python
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

    def test_bug_refuses_existing_dir(self):
        d = init_repo()
        self.assertEqual(start_bug(d).returncode, 0)
        self.assertNotEqual(start_bug(d).returncode, 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_bug_track.py -v`
Expected: FAIL —— `aip.py` 无 `bug` 子命令（argparse error / 非 0 退出）。

- [ ] **Step 3: 建模板 `templates/bug-report-template.md`**

```markdown
# Bug Report: <title>

## 症状 / 复现
<可观察表象 + 复现步骤/命令；不靠脑补>

## 竞争假设
<2–3 个，不认定第一个>

## 根因
<挖到能在代码/配置/环境里指出来的真正断裂层>

## 证据
<命令输出 / 日志 / 代码引用，逐层证伪后的判别证据>

## 触类旁通 · 同类波及面
<已扫范围(file_scope) + 命中的兄弟站点；范围外同类已登记 findings.md>

## 修复选项
<2–3 个方案 + 各自取舍，交用户判断>

## 选定方案
<用户拍板后填；含为何选它>

## 沉淀
<指向 knowledge.md 的 K-NNN；或 "N/A — <理由>">
```

- [ ] **Step 4: 建模板 `templates/bug-verification-template.md`**

```markdown
# Verification

> 修复硬绑**真实证据**：先证明 bug 真被复现并修掉（Regression），再过机器闸门与独立复核。

## Regression
<!-- 能复现该 bug 的测试/探针：修复前失败、修复后通过。给命令 + 前后结果。 -->

| repro | command | before | after | evidence |
|-------|---------|--------|-------|----------|
| <一句话复现项> | <cmd> | fail | pass | <输出摘要 / 测试路径> |

## Machine Gates
<!-- 每个 config.yaml gates 里声明的闸门一行；result 取 pass/fail；evidence 给命令输出摘要或报告路径。 -->

| gate | command | result | evidence |
|------|---------|--------|----------|
| <tests> | <cmd> | pass\|fail | <输出摘要 / 报告路径> |

## Independent Review (fresh-eyes)
<!-- 评审者 ≠ 实现者；带证伪视角。结论 + 处置。 -->
- 结论：<✅可信 / ⚠️有缺口已处置 / ❌需改>
- 处置：<退回改了什么 / 已知局限如实记>

## Not Run
<!-- 该跑没跑的（环境/时间所限），如实列，不静默略过。 -->

## Known Risks
<!-- 残留风险与边界。 -->

## Side-Findings This Round
<!-- 本轮撞见的无关问题是否都登记进 findings.md 并标了去向。 -->
```

- [ ] **Step 5: 改 `scripts/_aip_common.py`**

在 `REQUIRED_FEATURE_FILES` 块后新增：

```python
# bug 工作包（轻量轨）必需文件：砍掉 spec/plan/task_board，进度用 current_task.current_phase 跟踪。
REQUIRED_BUG_FILES = [
    "report.md",
    "file_scope.yaml",
    "handoff.md",
    "verification.md",
    "session_log.md",
]
```

并把 `report.md` 加进 `AIP_SLOT_FILENAMES`（列表末尾追加 `"report.md",`）。

- [ ] **Step 6: 建 `scripts/aip_start_bug.py`**

```python
from __future__ import annotations

import argparse
from pathlib import Path

from _aip_common import AIP_DIR, current_task_path, feature_dir, iso_now, write_json, write_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new AIP bug work package (light track).")
    parser.add_argument("--repo-root", required=True, help="Target project root.")
    parser.add_argument("--bug-id", required=True, help="Bug directory id.")
    parser.add_argument("--title", default="", help="Optional human-readable title.")
    parser.add_argument(
        "--template-root",
        default=Path(__file__).resolve().parents[1],
        help="AIP repository root. Defaults to this script's repository.",
    )
    args = parser.parse_args()

    target_repo = Path(args.repo_root).resolve()
    template_root = Path(args.template_root).resolve()
    out_dir = feature_dir(target_repo, args.bug_id)
    if out_dir.exists():
        print(f"Refusing to overwrite existing work package: {out_dir}")
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)

    template_map = {
        "report.md": "bug-report-template.md",
        "handoff.md": "handoff-template.md",
        "verification.md": "bug-verification-template.md",
        "file_scope.yaml": "file-scope-template.yaml",
    }
    for out_name, tpl_name in template_map.items():
        content = (template_root / "templates" / tpl_name).read_text(encoding="utf-8")
        write_text(out_dir / out_name, content)

    write_text(out_dir / "session_log.md", f"# Session Log\n\n- {iso_now()} bug created: {args.bug_id}\n")
    write_text(out_dir / "decisions.md", "# Decisions\n\n")

    current_task = {
        "kind": "bug",
        "feature_id": args.bug_id,
        "status": "planned",
        "current_phase": "investigate",
        "current_task": args.title or f"Investigate bug {args.bug_id}",
        "resolution": None,
        "next_action": "Run root-cause investigation; fill report.md before any fix.",
        "last_updated": iso_now(),
        "owner": "ai",
        "blocking": [],
        "must_read": [
            f"{AIP_DIR}/protocols/ai-implementation-protocol.md",
            f"{AIP_DIR}/STATUS.md",
            f"{AIP_DIR}/knowledge_index.md",
            f"{AIP_DIR}/features/{args.bug_id}/report.md",
            f"{AIP_DIR}/features/{args.bug_id}/handoff.md",
        ],
    }
    write_json(current_task_path(target_repo), current_task)

    print(f"Bug package initialized: {args.bug_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 7: 改 `scripts/aip.py` 加 `bug` 子命令**

在 `start_parser` 块后（约 line 35 之后）新增：

```python
    bug_parser = subparsers.add_parser("bug", help="Create a new AIP bug work package (light track).")
    add_repo_root(bug_parser)
    bug_parser.add_argument("bug_id", nargs="?", help="Bug directory id.")
    bug_parser.add_argument("--bug-id", dest="bug_id_flag", help="Bug directory id.")
    bug_parser.add_argument("--title", default="", help="Optional human-readable title.")
    bug_parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT), help="AIP template root.")
```

在 `start` 路由块后新增：

```python
    if args.command == "bug":
        bug_id = args.bug_id_flag or args.bug_id
        if not bug_id:
            parser.error("bug requires BUG_ID or --bug-id BUG_ID")
        script_args = ["--repo-root", args.repo_root, "--bug-id", bug_id, "--template-root", args.template_root]
        if args.title:
            script_args.extend(["--title", args.title])
        return run_script("aip_start_bug.py", script_args)
```

- [ ] **Step 8: 跑测试确认通过**

Run: `python -m pytest tests/test_bug_track.py -v`
Expected: PASS（3 个测试全绿）。

- [ ] **Step 9: Commit**

```bash
git add templates/bug-report-template.md templates/bug-verification-template.md \
        scripts/aip_start_bug.py scripts/_aip_common.py scripts/aip.py tests/test_bug_track.py
git commit -m "feat(aip): add bug work-package scaffolding (aip bug)"
```

---

### Task 2: Bug 完成闸门（`aip check` 按 `kind=bug` 分叉）

**Files:**
- Modify: `scripts/aip_check.py`
- Test: `tests/test_bug_track.py`（追加类）

**Interfaces:**
- Consumes: `_aip_common.REQUIRED_BUG_FILES`、现有 `section_body / missing / read_text / read_json` 等
- Produces:
  - `BUG_REPORT_REQUIRED`（report.md 必需标题）
  - `shared_done_gate(verification_text) -> list[str]`（Machine Gates / fail / 占位 / Independent Review，feature+bug 共用）
  - `bug_done_gate_problems(report_text, verification_text, resolution) -> list[str]`

- [ ] **Step 1: 追加失败测试到 `tests/test_bug_track.py`**

```python
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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_bug_track.py::BugDoneGate -v`
Expected: FAIL —— check 尚未识别 kind=bug，仍按 feature 校验（会报缺 spec.md 等）。

- [ ] **Step 3: 改 `scripts/aip_check.py` —— 常量与 helper**

顶部 import 加 `REQUIRED_BUG_FILES`：

```python
from _aip_common import (
    AIP_DIR,
    AIP_SLOT_FILENAMES,
    PROJECT_LIVING_FILES,
    REQUIRED_BUG_FILES,
    REQUIRED_FEATURE_FILES,
    SCAN_PRUNE_DIRS,
    aip_root,
    current_task_path,
    feature_dir,
    project_living_path,
    read_json,
    read_text,
)
```

在常量区新增：

```python
BUG_REPORT_REQUIRED = [
    "## 症状 / 复现", "## 竞争假设", "## 根因", "## 证据",
    "## 触类旁通 · 同类波及面", "## 修复选项", "## 沉淀",
]
```

把现有 `done_gate_problems` 的共享部分抽成 helper（替换原函数）：

```python
def shared_done_gate(verification_text: str) -> list[str]:
    """feature 与 bug 共用的 done 残渣校验：机器闸门绑真证据 + fresh-eyes review。"""
    problems: list[str] = []
    if "## Machine Gates" not in verification_text:
        problems.append("verification.md missing '## Machine Gates' section")
    if "| fail |" in verification_text:
        problems.append("verification.md has a gate with result 'fail'")
    if "| <" in verification_text:
        problems.append("verification.md still has unfilled placeholder rows ('| <...')")
    if "## Independent Review" not in verification_text:
        problems.append("verification.md missing '## Independent Review' (fresh-eyes) section")
    return problems


def done_gate_problems(verification_text: str, spec_text: str) -> list[str]:
    problems = shared_done_gate(verification_text)
    if not section_body(spec_text, "## Acceptance Criteria"):
        problems.append("spec.md '## Acceptance Criteria' is empty")
    return problems


def bug_done_gate_problems(report_text: str, verification_text: str, resolution: str) -> list[str]:
    """bug 完成闸门：根因/证据/同类面/沉淀非空；fixed 时必有回归证据；叠加共享闸门。"""
    problems = shared_done_gate(verification_text)
    for heading, label in (("## 根因", "根因"), ("## 证据", "证据"),
                           ("## 触类旁通 · 同类波及面", "同类波及面"), ("## 沉淀", "沉淀")):
        if not section_body(report_text, heading):
            problems.append(f"report.md '{heading}' 节为空（{label}缺失 = 表面补丁/未沉淀）")
    if resolution == "fixed":
        reg = section_body(verification_text, "## Regression")
        if not reg:
            problems.append("resolution=fixed 但 verification.md 缺 '## Regression' 回归证据")
        elif "pass" not in reg:
            problems.append("verification.md '## Regression' 无 after=pass 的回归行")
    return problems
```

- [ ] **Step 4: 改 `scripts/aip_check.py` —— 活动单元校验分叉**

把 `main()` 内"活动 feature 校验"块（现 line 243-286）替换为按 kind 分叉：

```python
    # --- 活动工作单元校验（无活动单元则跳过，使其可当提交闸门）---
    task_path = current_task_path(target_repo)
    if task_path.exists():
        current_task = read_json(task_path)
        kind = current_task.get("kind", "feature")
        fid = current_task.get("feature_id", "")
        status_done = current_task.get("status") == "done"
        resolution = current_task.get("resolution") or ""
        if fid:
            fd = feature_dir(target_repo, fid)
            if not fd.exists():
                errors.append(f"Missing work package directory: {fd}")
            elif kind == "bug":
                for name in REQUIRED_BUG_FILES:
                    if not (fd / name).exists():
                        errors.append(f"Missing bug file: {fd / name}")
                handoff = fd / "handoff.md"
                if handoff.exists():
                    for sec in missing(HANDOFF_REQUIRED, read_text(handoff)):
                        errors.append(f"handoff.md missing section: {sec}")
                report = fd / "report.md"
                if report.exists():
                    for sec in missing(BUG_REPORT_REQUIRED, read_text(report)):
                        errors.append(f"report.md missing section: {sec}")
                if status_done:
                    if resolution not in ("fixed", "wont_fix", "by_design"):
                        errors.append("bug done 但 current_task.resolution 非法（fixed|wont_fix|by_design）")
                    verification = fd / "verification.md"
                    rep_txt = read_text(report) if report.exists() else ""
                    ver_txt = read_text(verification) if verification.exists() else ""
                    if not verification.exists():
                        errors.append("bug marked done but verification.md is missing")
                    errors.extend(bug_done_gate_problems(rep_txt, ver_txt, resolution))
                    g_err, g_warn = gate_coverage_problems(target_repo, ver_txt, True)
                    errors.extend(g_err)
                    warnings.extend(g_warn)
            else:
                for name in REQUIRED_FEATURE_FILES:
                    if not (fd / name).exists():
                        errors.append(f"Missing feature file: {fd / name}")
                handoff = fd / "handoff.md"
                if handoff.exists():
                    for sec in missing(HANDOFF_REQUIRED, read_text(handoff)):
                        errors.append(f"handoff.md missing section: {sec}")
                spec = fd / "spec.md"
                if spec.exists():
                    for sec in missing(SPEC_REQUIRED_HEADINGS, read_text(spec)):
                        errors.append(f"spec.md missing section: {sec}")
                plan = fd / "plan.md"
                if plan.exists() and "## Tasks" not in read_text(plan):
                    errors.append("plan.md missing '## Tasks' section")
                tb = fd / "task_board.yaml"
                if tb.exists() and count_in_progress(read_text(tb)) > 1:
                    errors.append("task_board.yaml has more than one in_progress task")
                if status_done:
                    verification = fd / "verification.md"
                    if not verification.exists():
                        errors.append("feature marked done but verification.md is missing")
                    else:
                        vt = read_text(verification)
                        st = read_text(spec) if spec.exists() else ""
                        errors.extend(done_gate_problems(vt, st))
                        g_err, g_warn = gate_coverage_problems(target_repo, vt, True)
                        errors.extend(g_err)
                        warnings.extend(g_warn)
```

注意：原 `done_gate_problems(vt, st)` 调用签名未变（仍 `(verification_text, spec_text)`），feature 回归不受影响。

- [ ] **Step 5: 跑 bug 闸门测试确认通过**

Run: `python -m pytest tests/test_bug_track.py::BugDoneGate -v`
Expected: PASS（5 个测试全绿）。

- [ ] **Step 6: 跑既有测试确认 feature 无回归**

Run: `python -m pytest tests/ -v`
Expected: PASS（含 `test_root_cause_knowledge.py` / `test_onboarding.py` 全绿）。

- [ ] **Step 7: Commit**

```bash
git add scripts/aip_check.py tests/test_bug_track.py
git commit -m "feat(aip): bug-aware aip check (completeness gate)"
```

---

### Task 3: `aip done` 的 resolution 收尾

**Files:**
- Modify: `scripts/aip_done.py`
- Modify: `scripts/aip.py`（done 子命令加 `--resolution` 透传）
- Test: `tests/test_bug_track.py`（追加）

**Interfaces:**
- Consumes: 现有 `aip_done` 流程（设 done → 跑 check → 失败回滚）
- Produces: `aip done [--resolution fixed|wont_fix|by_design]`；kind=bug 且无 resolution 时拒绝收尾

- [ ] **Step 1: 追加失败测试**

```python
class BugDoneResolution(unittest.TestCase):
    def test_done_without_resolution_refused(self):
        d = init_repo()
        start_bug(d)
        # 用 finalize_bug 的内容但不设 resolution
        finalize_bug(d, resolution="fixed")  # 先填齐文档
        set_status(d, status="in_progress", resolution=None)  # 清掉 resolution，回到未收尾
        r = run("done", "--repo-root", str(d))
        self.assertEqual(r.returncode, 1)
        self.assertIn("resolution", r.stdout)

    def test_done_with_resolution_flag_passes(self):
        d = init_repo()
        start_bug(d)
        finalize_bug(d, resolution="fixed")
        set_status(d, status="in_progress", resolution=None)
        r = run("done", "--resolution", "fixed", "--repo-root", str(d))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ct = json.loads((d / ".aip/_runtime/current_task.json").read_text(encoding="utf-8"))
        self.assertEqual(ct["resolution"], "fixed")
        self.assertEqual(ct["status"], "done")
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_bug_track.py::BugDoneResolution -v`
Expected: FAIL —— `done` 无 `--resolution`，且不校验 resolution。

- [ ] **Step 3: 改 `scripts/aip_done.py`**

`argparse` 加参数，并在写 done 前处理 resolution：

```python
    parser.add_argument("--resolution", choices=["fixed", "wont_fix", "by_design"], default=None,
                        help="Bug 收尾结论（kind=bug 必填）。")
    args = parser.parse_args()

    target_repo = Path(args.repo_root).resolve()
    ct_path = current_task_path(target_repo)
    if not ct_path.exists():
        print("AIP 未初始化。请先运行 `$aip init`。")
        return 1

    current_task = read_json(ct_path)
    if current_task.get("kind", "feature") == "bug":
        resolution = args.resolution or current_task.get("resolution")
        if resolution not in ("fixed", "wont_fix", "by_design"):
            print("bug 收尾需指定 resolution：`$aip done --resolution fixed|wont_fix|by_design`。")
            return 1
        current_task["resolution"] = resolution

    prev_status = current_task.get("status", "in_progress")
    current_task["status"] = "done"
    current_task["last_updated"] = iso_now()
    write_json(ct_path, current_task)
```

（其余 check + 回滚逻辑不变。回滚时只回滚 `status`，resolution 保留为已填值，符合"分析结论不丢"。）

- [ ] **Step 4: 改 `scripts/aip.py` done 子命令透传 `--resolution`**

`done_parser` 加参数：

```python
    done_parser.add_argument("--resolution", choices=["fixed", "wont_fix", "by_design"], default=None,
                             help="Bug 收尾结论（kind=bug 必填）。")
```

done 路由块改为：

```python
    if args.command == "done":
        done_args = ["--repo-root", args.repo_root]
        if args.resolution:
            done_args.extend(["--resolution", args.resolution])
        return run_script("aip_done.py", done_args)
```

- [ ] **Step 5: 跑测试确认通过**

Run: `python -m pytest tests/test_bug_track.py -v`
Expected: PASS（全部 bug 测试绿）。

- [ ] **Step 6: Commit**

```bash
git add scripts/aip_done.py scripts/aip.py tests/test_bug_track.py
git commit -m "feat(aip): require resolution to close a bug (aip done)"
```

---

### Task 4: 协议与 skill/命令文档接线

**Files:**
- Modify: `docs/protocol.md`
- Modify: `plugins/ai-implementation-protocol/skills/aip/SKILL.md`
- Modify: `plugins/ai-implementation-protocol/skills/root-cause/SKILL.md`
- Create: `plugins/ai-implementation-protocol/commands/aip/bug.md`

**Interfaces:** 纯文档，无代码接口。验收 = 文档自洽 + `aip check` 仍过。

- [ ] **Step 1: `docs/protocol.md` 增工作单元类型说明**

在 "## Mandatory Objects" 的 "Every active feature must have" 段后，新增一段：

```markdown
## Work-Unit Kinds

A work unit is either a **feature** (new development) or a **bug** (fix, light track).
`current_task.json.kind` distinguishes them (absent ⇒ `feature`, backward-compatible).

A **bug** package is lighter: it drops `spec.md` / `plan.md` / `task_board.yaml` and tracks
progress through `current_task.current_phase` (`investigate` → `fix` → `verify`). Its core
living doc is `report.md` (症状/复现 → 竞争假设 → 根因+证据 → 触类旁通同类波及面 → 修复选项 →
沉淀). Verification adds a `## Regression` gate (a repro that failed before and passes after).

Bug completeness gate (`aip check`, status==done): 根因 + 证据 + 同类波及面 + 沉淀 节非空；
`resolution==fixed` 时必有回归证据；`resolution` ∈ {fixed, wont_fix, by_design}. Pure
"won't fix / by-design" closes via `resolution` without a regression gate but still requires
a root cause. The bug track binds the `root-cause` skill (Safeguard #9) to a resumable work unit.
```

- [ ] **Step 2: `skills/aip/SKILL.md` 增 `$aip bug` 命令与流程**

在 "Supported forms" 代码块加一行 `$aip bug 2026-06-17-crash-on-save --title "Crash on save"`；
在 "Routing Rules" 加：

```markdown
- `$aip bug <bug-id> [--title "..."]`: run `python <plugin-root>/scripts/aip.py bug <bug-id> --title "..." --repo-root .`，随后**挂起 `root-cause` skill** 驱动调查，产物落该 bug 包 `report.md`。
- `$aip done` 收尾 bug 需带 `--resolution fixed|wont_fix|by_design`。
```

并新增一节：

```markdown
## Bug Track (analysis + fix, coherent)

`$aip bug <id>` 建轻量 bug 包（report/file_scope/verification/handoff/session_log/decisions，
无 spec/plan/task_board），`current_task.kind=bug, current_phase=investigate`。连贯流程：

1. 建包后**挂起 `root-cause` skill**：先查 knowledge_index → 复现取证 → 竞争假设 → 逐层证伪 →
   症状 vs 根因 → 触类旁通同类排查；产物逐节落 `report.md`。
2. 根因确认 → root-cause 的 Stop-and-ask：摆【根因+证据+同类波及面+修复选项】交用户拍板，写"选定方案"。
3. `current_phase=fix`：修主站点 + file_scope 内同类兄弟站点（同一变更）。
4. `current_phase=verify`：先写 `## Regression`（修前 fail/修后 pass），跑机器闸门，记 fresh-eyes review；
   真因沉淀进 `knowledge.md`（填 report `## 沉淀`：K-NNN 或 N/A+理由）→ `aip knowledge`。
5. `$aip check` → `$aip done --resolution fixed|wont_fix|by_design`。
```

phase→skill 映射表的 `debug` 行后补一行（或在 debug 行注明）：bug 轨道 investigate 阶段绑 `root-cause`。

- [ ] **Step 3: `skills/root-cause/SKILL.md` 注明落点**

在"沉淀"步骤（第 8 步）末尾或"与 superpowers 的关系"前补一句：

```markdown
> 在 AIP **bug 轨道**（`current_task.kind=bug`）下，调查产物落该 bug 包 `report.md` 的对应节
> （症状/复现、竞争假设、根因、证据、触类旁通·同类波及面、修复选项、选定方案、沉淀），
> 不另起平行位置；`aip check` 会校验这些节非空与回归证据。
```

- [ ] **Step 4: 建 `plugins/ai-implementation-protocol/commands/aip/bug.md`**

参照同目录 `start.md` 的 frontmatter 与风格（先 Read `commands/aip/start.md` 对齐格式），写 `$aip bug` 命令说明：用途、参数（bug-id/--title）、连贯流程、与 root-cause 的关系、done 需 resolution。

- [ ] **Step 5: 验收**

Run: `python -m pytest tests/ -v`
Expected: PASS（文档改动不破坏测试）。
人工通读四处文档，确认无 spec/plan/task_board 残留描述、命令拼写与脚本一致。

- [ ] **Step 6: Commit**

```bash
git add docs/protocol.md plugins/ai-implementation-protocol/skills/aip/SKILL.md \
        plugins/ai-implementation-protocol/skills/root-cause/SKILL.md \
        plugins/ai-implementation-protocol/commands/aip/bug.md
git commit -m "docs(aip): document bug track + wire root-cause into aip bug"
```

---

### Task 5: 同步 plugin 副本并全量验证

**Files:**
- Modify: `plugins/ai-implementation-protocol/{scripts,docs,templates,schemas}/*`（由 sync 再生）
- Modify（可选）: `schemas/current_task.*`（文档化 `kind`/`resolution` 字段，参考性）

- [ ] **Step 1: 文档化 schema 字段（若 schema 文件存在）**

先 `ls schemas/`；若有 `current_task` schema，加 `kind`（enum feature|bug，默认 feature）与
`resolution`（enum fixed|wont_fix|by_design，bug 专用）字段说明。schema 仅参考，不被 check 强校验。

- [ ] **Step 2: 同步 plugin 包**

Run: `python scripts/sync_plugin.py`
Expected: `synced: scripts` / `synced: docs` / `synced: templates` / `synced: schemas` / `Plugin sync complete.`

- [ ] **Step 3: 校验同步一致**

Run: `python scripts/sync_plugin.py --check`
Expected: 仅打印 `would sync ...`，无差异告警。

- [ ] **Step 4: 全量测试**

Run: `python -m pytest tests/ -v`
Expected: 全绿。

- [ ] **Step 5: 端到端冒烟（真跑一条 bug 流）**

```bash
python scripts/aip.py init --repo-root /tmp/aipbug
python scripts/aip.py bug 2026-06-17-smoke --title "Smoke" --repo-root /tmp/aipbug
python scripts/aip.py resume --repo-root /tmp/aipbug
```
Expected: bug 包建出、resume 打印 kind=bug/phase=investigate 的摘要、`aip check`（未 done）通过。

- [ ] **Step 6: Commit**

```bash
git add plugins/ai-implementation-protocol schemas
git commit -m "chore(aip): sync plugin package with bug track"
```

---

## Self-Review

**Spec coverage:**
- 工作单元 `kind` 模型 → Task 1（current_task 写 kind）、Task 2（check 读 kind）✓
- bug 槽位（砍 spec/plan/task_board、加 report）→ Task 1 ✓
- report.md / verification 模板 → Task 1 ✓
- 连贯流程（investigate→fix→verify + root-cause 挂起）→ Task 4（skill 文档）✓
- 完整性闸门（根因/证据/同类面/沉淀 + 回归 + resolution）→ Task 2 ✓
- resolution 收尾 + wont_fix 边界 → Task 2（闸门）+ Task 3（done）✓
- 撞名拒绝 → Task 1（`out_dir.exists()` 报错）✓
- 向后兼容（无 kind=feature、feature 回归）→ Task 2 Step 6 ✓
- sync plugin → Task 5 ✓
- schema 文档化 → Task 5 Step 1 ✓

**Placeholder scan:** 无 TBD/TODO；模板内 `<...>` 为模板占位（设计要求），非计划占位；所有代码步骤含完整代码。

**Type consistency:** `bug_done_gate_problems(report_text, verification_text, resolution)` 在 Task 2 定义与调用签名一致；`shared_done_gate(verification_text)` 被 `done_gate_problems` 与 `bug_done_gate_problems` 共用，签名一致；`REQUIRED_BUG_FILES` 在 Task 1 定义、Task 2 import 使用；`finalize_bug` / `set_status` / `check` 测试 helper 在 Task 2 定义、Task 3 复用，名称一致；`BUG_REPORT_REQUIRED` 标题与 `bug-report-template.md` 标题逐字对齐（含 `## 触类旁通 · 同类波及面` 的全角空格）。
