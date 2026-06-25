# AIP 新引擎核心重建 Implementation Plan（一期）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 teardown 清出的空地上，按设计 spec（`docs/superpowers/specs/2026-06-24-aip-repositioning-discussion.md`）重建一个「技能为主、极少脚本」的 AIP 引擎，并把 v1 装回本仓库自托管（第一次真正的自我迭代）。

**Architecture:** 用户面是一个 `aip` 技能（SKILL.md），命令塌缩为 AI 自主触发——人日常只敲 `$aip init`。机器活只四个纯标准库脚本：`aip_check.py`（卫生闸门）、`aip_knowledge.py`（知识索引）、`aip_overview.py`（派生 OVERVIEW 摘要段）、`aip_init.py`（零配置初始化）；外加既有的 `aip_discovery.py`（托管块）、`install_hooks.py`（钩子）、`sync_plugin.py`（双副本）。活文档六类（OVERVIEW/decisions/knowledge/reference/inbox/conventions）是源。

**Tech Stack:** Python 3.10+ 纯标准库（`unittest` 测试，无 pytest）；Markdown 活文档；Claude Code 技能（plugin 形态）。

## Global Constraints

- **零依赖**：只用 Python 3.10+ 标准库，禁止任何 pip 依赖。
- **编码**：新建文件 UTF-8 无 BOM；编辑已有文件保持原编码；`write_text` 一律 `newline="\n"`（LF）。
- **双副本**：顶层 `scripts/`、`templates/` 是真源；`plugins/ai-implementation-protocol/` 副本由 `python scripts/sync_plugin.py --repo-root .` 再生——改顶层后必须跑 sync，禁止手改副本。
- **AIP 产物落 `.aip/`**，不污染项目根。
- **通用开发纪律（随 AIP 分发，单一来源在 aip 技能）**：在 `skills/aip/SKILL.md` 设一节「通用开发纪律（可增补）」，作为对所有项目生效、随插件分发的纪律清单的**唯一来源**；协议正文与 init 引导块只“指向”它、不复制内容（避免多处抄写漂移）。起步两条：①**禁止说黑话**——文档/注释/会话大白话，禁止晦涩比喻和生造术语（如 "scales to zero"、"footgun"、"毕业"），公认技术名词（LSP、git、闸门、索引）可直接用；②**注释不引外部编号**——代码注释禁止引用 plan/需求/任务/issue 编号或外部文档名（会漂移、改名即误导），注释只说代码本身的意图/约束、简洁自足。以后增补规则/技巧只往这一节加。中文、结论先行。
- **测试**：`python -m unittest tests.<module> -v`（系统无 pytest）。
- **commit message** 末尾附 `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`。
- **基线分支**：在 `chore/aip-teardown` 上继续（teardown 提交已在其上）。
- **二期不在本计划**：M2 全本语义纠偏、M3 反链派生、自动捕获回扫的完整编排、使用统计、归档、方法骨架（假设分级/证据标签）、力度分档。

---

## File Structure

**机器活（脚本，TDD）**
- `scripts/_aip_common.py`（改）— 收口到新模型常量。
- `scripts/aip_knowledge.py`（改）— 索引加 `适用范围` 列、接受 `draft`。
- `scripts/aip_check.py`（建）— 卫生闸门。
- `scripts/aip_discovery.py`（改）— 新模型引导块（只指路）+ 泛化托管块写入。
- `scripts/aip_overview.py`（建）— 派生 OVERVIEW 自动摘要段。
- `scripts/aip_init.py`（建）— 零配置初始化。
- `scripts/install_hooks.py`（改）— 钩子命令改指 `aip_check.py`。
- `tests/test_common_model.py`、`test_knowledge_index.py`、`test_check.py`、`test_discovery.py`、`test_overview.py`、`test_init.py`（建）。

**活文档与模板（Markdown）**
- `templates/`：`overview-template.md`（建，原 status-template 改名重写）、`knowledge-template.md`（改）、`reference-template.md`（建，原 canonical-assets 改名重写）、`inbox-template.md`（建）、`conventions-template.md`（建）、`decisions-template.md`（留）、`config-template.yaml`（留）。删 `status-template.md`、`canonical-assets-template.md`。
- `.aip/`：迁移本仓库自托管文档到六类。

**协议与技能**
- `plugins/ai-implementation-protocol/skills/aip/SKILL.md`（建）。
- `plugins/ai-implementation-protocol/skills/root-cause/SKILL.md`（改）— 沉淀对齐新 schema。
- `.aip/protocols/ai-implementation-protocol.md`（改）。

---

### Task 1: `_aip_common.py` 收口到新模型常量

**Files:** Modify `scripts/_aip_common.py`；Test `tests/test_common_model.py`

**Interfaces — Produces:**
- `PROJECT_LIVING_FILES = ["OVERVIEW.md","decisions.md","knowledge.md","knowledge_index.md","reference.md","inbox.md","conventions.md","config.yaml"]`
- `FORBIDDEN_SLOT_FILENAMES`：旧 per-feature 残留 + 旧文档名（迁移守卫）。
- `REQUIRED_KNOWLEDGE_FIELDS = ["分类","状态","症状","根因","适用范围","最后复核"]`
- 删除：`REQUIRED_FEATURE_FILES, REQUIRED_BUG_FILES, AIP_SLOT_FILENAMES, feature_dir, current_task_path`。

- [ ] **Step 1: 写失败测试** — `tests/test_common_model.py`:
```python
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import _aip_common as c

class CommonModel(unittest.TestCase):
    def test_living_files_new_set(self):
        self.assertEqual(c.PROJECT_LIVING_FILES, [
            "OVERVIEW.md","decisions.md","knowledge.md","knowledge_index.md",
            "reference.md","inbox.md","conventions.md","config.yaml"])
    def test_forbidden_covers_residue_and_old_names(self):
        for name in ["current_task.json","task_board.yaml","handoff.md",
                     "STATUS.md","findings.md","canonical-assets.md"]:
            self.assertIn(name, c.FORBIDDEN_SLOT_FILENAMES)
    def test_required_knowledge_fields(self):
        self.assertEqual(c.REQUIRED_KNOWLEDGE_FIELDS,
            ["分类","状态","症状","根因","适用范围","最后复核"])
    def test_old_helpers_removed(self):
        for a in ["REQUIRED_FEATURE_FILES","REQUIRED_BUG_FILES",
                  "AIP_SLOT_FILENAMES","feature_dir","current_task_path"]:
            self.assertFalse(hasattr(c, a), f"{a} 应已删除")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败** — `python -m unittest tests.test_common_model -v` → FAIL。

- [ ] **Step 3: 改 `_aip_common.py`** — 删 `REQUIRED_FEATURE_FILES`、`REQUIRED_BUG_FILES` 两段；`PROJECT_LIVING_FILES` 改为：
```python
PROJECT_LIVING_FILES = [
    "OVERVIEW.md", "decisions.md", "knowledge.md", "knowledge_index.md",
    "reference.md", "inbox.md", "conventions.md", "config.yaml",
]
```
把 `AIP_SLOT_FILENAMES = [...]` 整段替换为：
```python
# 不该出现在仓库任何地方的文件名：旧 per-feature 接管残留 + 已被取代的旧文档名（迁移守卫）。
FORBIDDEN_SLOT_FILENAMES = [
    "current_task.json", "task_board.yaml", "handoff.md", "verification.md",
    "session_log.md", "report.md", "file_scope.yaml",
    "STATUS.md", "findings.md", "canonical-assets.md",
]

# knowledge.md 每条目必填字段（check 校验）。
REQUIRED_KNOWLEDGE_FIELDS = ["分类", "状态", "症状", "根因", "适用范围", "最后复核"]
```
删 `feature_dir`、`current_task_path` 两个函数。

- [ ] **Step 4: 跑测试确认通过** — `python -m unittest tests.test_common_model -v` → PASS（4）。
- [ ] **Step 5: 提交** — `git add scripts/_aip_common.py tests/test_common_model.py && git commit -m "refactor(aip): retire old constants, add new-model living/forbidden/knowledge sets"`

---

### Task 2: knowledge 索引升级（apply_scope 进索引 + draft 状态）

**Files:** Modify `scripts/aip_knowledge.py`、`templates/knowledge-template.md`、`.aip/knowledge.md`；Test `tests/test_knowledge_index.py`

**Interfaces — Produces:** `INDEX_HEADER` 新格式 `ID | 分类 | 状态 | 适用范围 | 标题 | 最后复核`；`render_index` 输出含适用范围列；`parse_entries/expected_index_text/rebuild_index` 签名不变（check 复用）。

- [ ] **Step 1: 写失败测试** — `tests/test_knowledge_index.py`:
```python
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
        self.assertIn("适用范围", k.expected_index_text(self._b()).splitlines()[1])
    def test_draft_preserved(self):
        line = [l for l in k.expected_index_text(self._b()).splitlines() if l.startswith("K-002")][0]
        self.assertIn("draft", line)
    def test_row_order(self):
        line = [l for l in k.expected_index_text(self._b()).splitlines() if l.startswith("K-001")][0]
        cols = [c.strip() for c in line.split("|")]
        self.assertEqual(cols[1], "build"); self.assertEqual(cols[2], "active")
        self.assertEqual(cols[3], "仅 Windows runner + pnpm<9"); self.assertEqual(cols[5], "2026-06-01")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败** — FAIL（索引无适用范围列）。
- [ ] **Step 3: 改 `aip_knowledge.py`** — `INDEX_HEADER` 第二行改 `# 格式: ID | 分类 | 状态 | 适用范围 | 标题 | 最后复核\n`；`render_index` 拼行改为：
```python
        lines.append(
            f'{e["id"]} | {f.get("分类", "")} | {f.get("状态", "")} | '
            f'{f.get("适用范围", "")} | {e["title"]} | {f.get("最后复核", "")}'
        )
```
- [ ] **Step 4: 跑测试确认通过** — PASS（3）。
- [ ] **Step 5: 改模板与本仓库知识库头部** — `templates/knowledge-template.md` 与 `.aip/knowledge.md`（两处同改）：注释骨架 `- 状态: active` 行后加注 `# active=已人工确认 | draft=AI 待确认 | superseded(by K-00X)`；顶部加一句「AI 新沉淀一律先写 `状态: draft`，经人确认后改 `active`」。
- [ ] **Step 6: 重建索引 + 提交** — `python scripts/aip_knowledge.py --repo-root .`；`git add scripts/aip_knowledge.py templates/knowledge-template.md .aip/knowledge.md .aip/knowledge_index.md tests/test_knowledge_index.py && git commit -m "feat(aip): knowledge index gains apply_scope column + draft state"`

---

### Task 3: `aip_check.py` —— 活文档存在 + 索引一致

**Files:** Create `scripts/aip_check.py`；Test `tests/test_check.py`

**Interfaces — Produces:** `check_living_files(repo)->list[str]`、`check_index_sync(repo)->list[str]`、`run_all(repo)->list[str]`（后续任务追加）。

- [ ] **Step 1: 写失败测试** — `tests/test_check.py`:
```python
import sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
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

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败** — FAIL（`No module named 'aip_check'`）。
- [ ] **Step 3: 写最小实现** — `scripts/aip_check.py`:
```python
from __future__ import annotations
import argparse
from pathlib import Path
from _aip_common import PROJECT_LIVING_FILES, project_living_path, read_text
from aip_knowledge import expected_index_text

def check_living_files(repo: Path) -> list[str]:
    return [f"缺失活文档: .aip/{n}" for n in PROJECT_LIVING_FILES
            if not project_living_path(repo, n).exists()]

def check_index_sync(repo: Path) -> list[str]:
    idx = project_living_path(repo, "knowledge_index.md")
    if not idx.exists():
        return ["缺失 knowledge_index.md（跑 aip knowledge 重建）"]
    if read_text(idx) != expected_index_text(repo):
        return ["knowledge_index.md 与 knowledge.md 不一致（跑 aip knowledge 重建）"]
    return []

def run_all(repo: Path) -> list[str]:
    return check_living_files(repo) + check_index_sync(repo)

def main() -> int:
    p = argparse.ArgumentParser(description="AIP hygiene gate.")
    p.add_argument("--repo-root", required=True)
    viol = run_all(Path(p.parse_args().repo_root).resolve())
    if viol:
        print("aip check 未通过：")
        for v in viol: print(f"  - {v}")
        return 1
    print("aip check 通过"); return 0

if __name__ == "__main__":
    raise SystemExit(main())
```
- [ ] **Step 4: 跑测试确认通过** — PASS（3）。
- [ ] **Step 5: 提交** — `git add scripts/aip_check.py tests/test_check.py && git commit -m "feat(aip): check gate — living files + index sync"`

---

### Task 4: `aip_check.py` —— 知识字段校验 + 旧残留扫描

**Files:** Modify `scripts/aip_check.py`、`tests/test_check.py`

**Interfaces — Produces:** `check_knowledge_fields(repo)`、`check_no_orphan_slots(repo)`；`run_all` 追加。

- [ ] **Step 1: 写失败测试（追加到 `tests/test_check.py` 末尾 `if __name__` 之前）**:
```python
class KnowledgeFields(unittest.TestCase):
    def test_missing_field(self):
        d = make_repo()
        (d/".aip"/"knowledge.md").write_text(
            "# k\n\n## 类目\nother\n\n## K-001: 缺字段\n- 分类: other\n- 状态: draft\n", encoding="utf-8")
        self.assertTrue(any("K-001" in v and "适用范围" in v for v in chk.check_knowledge_fields(d)))
    def test_full_entry_ok(self):
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
```
- [ ] **Step 2: 跑测试确认失败** — FAIL（函数未定义）。
- [ ] **Step 3: 写实现** — 更新 import：
```python
from _aip_common import (
    FORBIDDEN_SLOT_FILENAMES, PROJECT_LIVING_FILES, REQUIRED_KNOWLEDGE_FIELDS,
    SCAN_PRUNE_DIRS, project_living_path, read_text,
)
from aip_knowledge import expected_index_text, parse_entries
```
在 `run_all` 前加：
```python
def check_knowledge_fields(repo: Path) -> list[str]:
    kn = project_living_path(repo, "knowledge.md")
    if not kn.exists():
        return []
    out = []
    for e in parse_entries(read_text(kn)):
        for field in REQUIRED_KNOWLEDGE_FIELDS:
            if not e["fields"].get(field):
                out.append(f'知识条目 {e["id"]} 缺必填字段: {field}')
    return out

def check_no_orphan_slots(repo: Path) -> list[str]:
    out = []
    for path in repo.rglob("*"):
        if not path.is_file() or any(p in SCAN_PRUNE_DIRS for p in path.parts):
            continue
        if path.name in FORBIDDEN_SLOT_FILENAMES:
            out.append(f"发现旧机制残留/未迁移文件: {path.relative_to(repo)}")
    return out
```
`run_all` 改为 `return (check_living_files(repo) + check_index_sync(repo) + check_knowledge_fields(repo) + check_no_orphan_slots(repo))`。注：`SCAN_PRUNE_DIRS` 含 `.git` 等但**不含** `.aip`，故 `.aip/` 内残留能被扫到。

- [ ] **Step 4: 跑测试确认通过** — PASS（7 累计）。
- [ ] **Step 5: 提交** — `git add scripts/aip_check.py tests/test_check.py && git commit -m "feat(aip): check enforces knowledge fields + scans old residue"`

---

### Task 5: `aip_check.py` —— 双副本一致性

**Files:** Modify `scripts/aip_check.py`、`tests/test_check.py`

**Interfaces — Produces:** `check_dual_copy(repo)`；`run_all` 追加。

- [ ] **Step 1: 写失败测试（追加）**:
```python
class DualCopy(unittest.TestCase):
    def _mk(self):
        d = make_repo(); (d/"scripts").mkdir()
        (d/"scripts"/"a.py").write_text("print(1)\n", encoding="utf-8")
        pl = d/"plugins"/"ai-implementation-protocol"/"scripts"; pl.mkdir(parents=True)
        (pl/"a.py").write_text("print(1)\n", encoding="utf-8"); return d
    def test_match_ok(self):
        self.assertEqual(chk.check_dual_copy(self._mk()), [])
    def test_drift(self):
        d = self._mk()
        (d/"plugins"/"ai-implementation-protocol"/"scripts"/"a.py").write_text("print(2)\n", encoding="utf-8")
        self.assertTrue(any("a.py" in v for v in chk.check_dual_copy(d)))
    def test_missing_mirror(self):
        d = self._mk(); (d/"scripts"/"b.py").write_text("x\n", encoding="utf-8")
        self.assertTrue(any("b.py" in v for v in chk.check_dual_copy(d)))
```
- [ ] **Step 2: 跑测试确认失败** — FAIL。
- [ ] **Step 3: 写实现** — 追加：
```python
MIRROR_DIRS = ["scripts", "templates"]
PLUGIN_ROOT = "plugins/ai-implementation-protocol"

def check_dual_copy(repo: Path) -> list[str]:
    out = []
    for sub in MIRROR_DIRS:
        src = repo / sub
        if not src.is_dir():
            continue
        for f in src.rglob("*"):
            if not f.is_file() or "__pycache__" in f.parts:
                continue
            rel = f.relative_to(repo)
            mirror = repo / PLUGIN_ROOT / rel
            if not mirror.exists():
                out.append(f"plugins 副本缺失: {rel}（跑 sync_plugin.py）")
            elif read_text(mirror) != read_text(f):
                out.append(f"plugins 副本漂移: {rel}（跑 sync_plugin.py）")
    return out
```
`run_all` 末尾追加 `+ check_dual_copy(repo)`。
- [ ] **Step 4: 跑测试确认通过** — `python -m unittest discover -s tests -v` → 全绿（10 check + 前序）。
- [ ] **Step 5: 提交** — `git add scripts/aip_check.py tests/test_check.py && git commit -m "feat(aip): check verifies dual-copy consistency"`

---

### Task 6: `aip_discovery.py` —— 新模型引导块 + 泛化托管块

**Files:** Modify `scripts/aip_discovery.py`；Test `tests/test_discovery.py`

**Interfaces — Produces:**
- `upsert_block(path, body, begin, end)`：通用幂等写入（任意标记对）。
- `managed_block()`、`upsert_managed_block(path)`：引导块，body 改为**新模型、只指路、不喂状态**，复用 `upsert_block`。

- [ ] **Step 1: 写失败测试** — `tests/test_discovery.py`:
```python
import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import aip_discovery as disc

class Discovery(unittest.TestCase):
    def test_bootstrap_is_new_model(self):
        b = disc.managed_block()
        self.assertIn("OVERVIEW.md", b)
        self.assertNotIn("current_task.json", b)
        self.assertNotIn("STATUS.md", b)
    def test_upsert_block_custom_markers_idempotent(self):
        d = Path(tempfile.mkdtemp()); p = d/"x.md"
        p.write_text("手写在上\n", encoding="utf-8")
        disc.upsert_block(p, "AUTO 内容\n", "<!--A-->", "<!--/A-->")
        disc.upsert_block(p, "AUTO 内容2\n", "<!--A-->", "<!--/A-->")
        t = p.read_text(encoding="utf-8")
        self.assertIn("手写在上", t)            # 手写区保留
        self.assertIn("AUTO 内容2", t)          # 只替换标记区
        self.assertNotIn("AUTO 内容\n", t.replace("AUTO 内容2", ""))
        self.assertEqual(t.count("<!--A-->"), 1)  # 不重复

if __name__ == "__main__":
    unittest.main()
```
- [ ] **Step 2: 跑测试确认失败** — FAIL（引导块仍旧模型 / `upsert_block` 不存在）。
- [ ] **Step 3: 改 `aip_discovery.py`** — `BLOCK_BODY` 改为新模型只指路：
```python
BLOCK_BODY = (
    "## AI Implementation Protocol\n"
    "本仓库用 AIP 管理实现工作（机制见 `.aip/protocols/`）。需要时去 `.aip/` 找：\n"
    "- `OVERVIEW.md` 现状/在建（开始或接手任务前先读）\n"
    "- `knowledge.md`(+`knowledge_index.md`) 验证过的坑（遇问题先查）\n"
    "- `decisions.md` 为什么这么定 / `reference.md` 这工程是什么+该复用什么\n"
    "- `inbox.md` 旁路问题 / `conventions.md` 项目规约\n"
    "AIP 动作由 AI 按时机自主触发；语言一律大白话，禁止黑话。\n"
)
```
新增通用函数并让引导块复用它：
```python
def upsert_block(path: Path, body: str, begin: str, end: str) -> None:
    """幂等写入标记块：无文件则建；有标记则只替换标记区；否则末尾追加。"""
    block = f"{begin}\n{body}{end}\n"
    if not path.exists():
        path.write_text(block, encoding="utf-8", newline="\n"); return
    text = path.read_text(encoding="utf-8")
    if begin in text and end in text:
        new = text[: text.index(begin)] + block.rstrip("\n") + text[text.index(end) + len(end):]
    else:
        sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
        new = text + sep + block
    path.write_text(new, encoding="utf-8")

def managed_block() -> str:
    return f"{BEGIN}\n{BLOCK_BODY}{END}\n"

def upsert_managed_block(path: Path) -> None:
    upsert_block(path, BLOCK_BODY, BEGIN, END)
```
- [ ] **Step 4: 跑测试确认通过** — PASS（2）。
- [ ] **Step 5: 提交** — `git add scripts/aip_discovery.py tests/test_discovery.py && git commit -m "feat(aip): new-model bootstrap block + generic managed-block upsert"`

---

### Task 7: `aip_overview.py` —— 派生 OVERVIEW 自动摘要段

**Files:** Create `scripts/aip_overview.py`；Test `tests/test_overview.py`

**Interfaces — Consumes:** `aip_knowledge.parse_entries`、`aip_discovery.upsert_block`、`_aip_common.{project_living_path, read_text}`。
**Produces:** `top_headings(text, prefix)`、`build_digest(repo)->str`、`rebuild_overview(repo)->Path`（把摘要写进 OVERVIEW.md 的 AUTO 标记区，**不碰手写看板**）。

- [ ] **Step 1: 写失败测试** — `tests/test_overview.py`:
```python
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

if __name__ == "__main__":
    unittest.main()
```
- [ ] **Step 2: 跑测试确认失败** — FAIL（无模块）。
- [ ] **Step 3: 写实现** — `scripts/aip_overview.py`:
```python
from __future__ import annotations
import argparse
from pathlib import Path
from _aip_common import project_living_path, read_text
from aip_knowledge import parse_entries
from aip_discovery import upsert_block

AUTO_BEGIN = "<!-- AIP:AUTO-DIGEST:BEGIN (勿手改) -->"
AUTO_END = "<!-- AIP:AUTO-DIGEST:END -->"

def top_headings(text: str, prefix: str) -> list[str]:
    return [l[len(prefix):].strip() for l in text.splitlines() if l.startswith(prefix)]

def _read(repo: Path, name: str) -> str:
    p = project_living_path(repo, name)
    return read_text(p) if p.exists() else ""

def build_digest(repo: Path) -> str:
    ks = parse_entries(_read(repo, "knowledge.md"))
    kn = "\n".join(f'- {e["id"]} {e["title"]} [{e["fields"].get("状态","")}]' for e in ks) or "- （空）"
    dec = "\n".join(f"- {h}" for h in top_headings(_read(repo, "decisions.md"), "## ")[-5:]) or "- （空）"
    ref = "\n".join(f"- {h}" for h in top_headings(_read(repo, "reference.md"), "### ")) or "- （空）"
    return (f"### 自动摘要（派生，勿手改）\n**知识（{len(ks)} 条）**\n{kn}\n\n"
            f"**近期决策**\n{dec}\n\n**核心概念**\n{ref}\n")

def rebuild_overview(repo: Path) -> Path:
    p = project_living_path(repo, "OVERVIEW.md")
    upsert_block(p, build_digest(repo), AUTO_BEGIN, AUTO_END)
    return p

def main() -> int:
    ap = argparse.ArgumentParser(description="Rebuild OVERVIEW auto-digest.")
    ap.add_argument("--repo-root", required=True)
    print(f"OVERVIEW digest rebuilt: {rebuild_overview(Path(ap.parse_args().repo_root).resolve())}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```
- [ ] **Step 4: 跑测试确认通过** — PASS（2）。
- [ ] **Step 5: 提交** — `git add scripts/aip_overview.py tests/test_overview.py && git commit -m "feat(aip): derive OVERVIEW auto-digest, leaving hand board intact"`

---

### Task 8: 文档模板 + 迁移本仓库 `.aip/`

**Files:** `templates/`（建 overview/reference/inbox/conventions，删 status/canonical-assets）；`.aip/`（迁移）

**Interfaces — Produces:** 六类活文档模板齐备；本仓库 `.aip/` 迁到六类、旧名文件删除。

- [ ] **Step 1: 建 `templates/overview-template.md`**（手写看板 + AUTO 标记区）:
```markdown
# 总览（OVERVIEW）· 活文档 · 开始/接手任务前读这页

> 顶部「在建」是手写源（AI 收尾时改）；下面「自动摘要」由 `aip overview` 派生、勿手改。
> 只装往前看 + 易腐的状态；不装 git 能派生的（改了哪些文件、流水账）。每块封顶几行；线 done 立即移出。

## 在建（多线看板）
### ▶[active] <track-id>  <一句话标题>   状态: 进行中
- 卡哪 / blocker：<无则写「无」>
- 下一步：<具体到能直接上手>
- must_read：<≤3 个关键文件路径>

### ⏸ <track-id>  <标题>   状态: 阻塞(<等什么>) | 待开始

## 已知缺口 / 旁路待办
1. <一行一条，标去向；详情入 inbox.md>

<!-- AIP:AUTO-DIGEST:BEGIN (勿手改) -->
<!-- AIP:AUTO-DIGEST:END -->
```
- [ ] **Step 2: 建 `templates/reference-template.md`**:
```markdown
# 本工程权威参照 · 活文档

> 动手前查这里：这工程是什么、该复用什么。从空白靠捕获长大——AI 读代码推断、跟人确认后记。
> 造新工具/函数前按退化链先查同类：有 LSP 用 findReferences；查同义实现用 grep+读候选+查本表；大工程用 nexus-query/CodeGraph（若装）。命中复用；确需造新且该成权威件 → 记「可复用实现」并写明为什么已有的不适用。

## 领域概念 / 术语口径
| 概念 | 在本项目里指什么 | 关联 |
|---|---|---|
| <例：订单> | <明确定义，避免歧义> | <ADR-N / K-NNN> |

## 核心实体与关键铁律（不变量）
- <例：金额一律按分存，不用浮点> （关联: ADR-N）

## 可复用实现（裁决）
| 能力 | 钦定实现 | 边界（只在什么情况用） | 来源 |
|---|---|---|---|
| <例：HTTP 重试> | <utils/http.py:retry_request> | <只管幂等 GET> | <YYYY-MM-DD> |
```
- [ ] **Step 3: 建 `templates/inbox-template.md`**:
```markdown
# 旁路问题收件箱 · 活文档

> 干 A 时撞见的、与 A 无关的问题。投递前先在 knowledge.md + 本表检索：已有类似（解决方案/旧讨论）就复用并加关联，确认是新问题才整理后登记。**不无脑 append**。
> trivial 且同文件 → 顺手修不登记。出口：立项为新线 / 进 decisions / 进 OVERVIEW 旁路待办 / 关闭。

## 条目
## I-N：<一句话症状>
- 发现 / 状态：YYYY-MM-DD（发现于<哪条线>）/ 待分类 | 已立项 | 接受为债 | 已修 | won't-fix
- 影响域：<按项目填>
- 症状 / 证据：<现象 + repro / 日志（趁新鲜抓）>
- 去向：<分类结论 + 关联：OVERVIEW#x / ADR-N / I-M>
```
- [ ] **Step 4: 建 `templates/conventions-template.md`**:
```markdown
# 项目规约 · 活文档

> 这工程「怎么干」的常驻规则。从空白靠捕获长大——被纠正一次就记一条。机器能强制的（linter/formatter/CI）指向它，文档只记需人/AI 判断的。

## 代码风格
- <例：命名 snake_case；提交前跑 <formatter>>
## 注释风格
- <例：注释写 why 不写 what>
## 设计风格
- <例：优先组合而非继承>
## 构建 / 调试 / 验收固定流程
- 构建：<命令> ｜ 测试：<命令> ｜ 验收通用标准：<清单>
```
- [ ] **Step 5: 删旧模板、迁移本仓库 `.aip/`** —
```bash
git rm templates/status-template.md templates/canonical-assets-template.md
```
迁移（保留原编码 UTF-8 无 BOM）：
- `git mv .aip/STATUS.md .aip/OVERVIEW.md`，再按 overview 模板重写：顶部留一条 `▶[active] aip-rebuild-core 重建 AIP 新引擎`（卡哪=无；下一步=按本计划继续；must_read=本计划 + 设计 spec），末尾加 AUTO 标记区空块。
- `git mv .aip/canonical-assets.md .aip/reference.md`，按 reference 模板重写（无强条目则各节留表头 + `<暂无>`）。
- 新建 `.aip/inbox.md`、`.aip/conventions.md`（用模板，内容留占位）。
- [ ] **Step 6: 自检 + 提交** —
```bash
python - <<'PY'
import pathlib
for n in ["overview","reference","inbox","conventions"]:
    t = pathlib.Path(f"templates/{n}-template.md").read_text(encoding="utf-8")
    assert "findings.md" not in t and "current_task" not in t, f"{n} 模板有旧引用"
ov = pathlib.Path(".aip/OVERVIEW.md").read_text(encoding="utf-8")
assert "▶[active]" in ov and "AIP:AUTO-DIGEST:BEGIN" in ov, "OVERVIEW 缺看板或 AUTO 区"
assert not pathlib.Path(".aip/STATUS.md").exists(), "旧 STATUS.md 未删"
print("OK")
PY
python scripts/aip_overview.py --repo-root .
git add -A templates .aip
git commit -m "feat(aip): six-doc templates (overview/reference/inbox/conventions) + migrate self-host"
```

---

### Task 9: `aip_init.py`（零配置）+ `install_hooks.py` 修命令

**Files:** Create `scripts/aip_init.py`；Modify `scripts/install_hooks.py`；Test `tests/test_init.py`

**Interfaces — Consumes:** `_aip_common.{PROJECT_LIVING_FILES, aip_root, load_template, write_text, ensure_dir}`、`aip_discovery.upsert_managed_block`。
**Produces:** `scaffold(repo, engine_root)->list[Path]`（建 `.aip/` 六类活文档骨架 + 空 config + protocols；不问工程任何事）；`aip_init` main 还写引导块、装钩子。`install_hooks.pre_commit_body` 命令改指 `aip_check.py`。

- [ ] **Step 1: 写失败测试** — `tests/test_init.py`:
```python
import sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import aip_init, _aip_common as c

class Init(unittest.TestCase):
    def test_scaffold_creates_living_docs_no_prompt(self):
        d = Path(tempfile.mkdtemp())
        aip_init.scaffold(d, ROOT)
        for n in c.PROJECT_LIVING_FILES:
            self.assertTrue((d/".aip"/n).exists(), f"{n} 未建")
        # 零配置：config 存在但不含被追问的工程信息（留空骨架）
        self.assertTrue((d/".aip"/"config.yaml").exists())
    def test_idempotent(self):
        d = Path(tempfile.mkdtemp())
        aip_init.scaffold(d, ROOT)
        (d/".aip"/"OVERVIEW.md").write_text("# 我改过\n", encoding="utf-8")
        aip_init.scaffold(d, ROOT)  # 再跑不应覆盖已存在的
        self.assertIn("我改过", (d/".aip"/"OVERVIEW.md").read_text(encoding="utf-8"))

class Hooks(unittest.TestCase):
    def test_hook_targets_check_not_router(self):
        import install_hooks
        body = install_hooks.pre_commit_body(ROOT)
        self.assertIn("aip_check.py", body)
        self.assertNotIn("aip.py", body)

if __name__ == "__main__":
    unittest.main()
```
- [ ] **Step 2: 跑测试确认失败** — FAIL（无 `aip_init` / 钩子仍指 aip.py）。
- [ ] **Step 3a: 写 `scripts/aip_init.py`**:
```python
from __future__ import annotations
import argparse
from pathlib import Path
from _aip_common import PROJECT_LIVING_FILES, aip_root, ensure_dir, load_template, write_text
from aip_discovery import upsert_managed_block

# 活文档名 → 模板名（无模板的建空骨架）。零配置：不向用户索取工程信息。
TEMPLATE_OF = {
    "OVERVIEW.md": "overview-template.md",
    "decisions.md": "decisions-template.md",
    "knowledge.md": "knowledge-template.md",
    "reference.md": "reference-template.md",
    "inbox.md": "inbox-template.md",
    "conventions.md": "conventions-template.md",
    "config.yaml": "config-template.yaml",
}

def scaffold(repo: Path, engine_root: Path) -> list[Path]:
    root = aip_root(repo); ensure_dir(root); ensure_dir(root / "protocols")
    created = []
    for name in PROJECT_LIVING_FILES:
        dst = root / name
        if dst.exists():
            continue  # 幂等：不覆盖
        if name == "knowledge_index.md":
            write_text(dst, "# 知识索引（自动生成，勿手改）\n")
        else:
            tpl = TEMPLATE_OF.get(name)
            write_text(dst, load_template(engine_root, tpl) if tpl else "")
        created.append(dst)
    return created

def main() -> int:
    ap = argparse.ArgumentParser(description="Init AIP into a repo (zero-config).")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--engine-root", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--no-hooks", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo_root).resolve(); engine = Path(a.engine_root).resolve()
    scaffold(repo, engine)
    for guide in ["CLAUDE.md", "AGENTS.md"]:
        upsert_managed_block(repo / guide)
    if not a.no_hooks and (repo / ".git").exists():
        import install_hooks
        install_hooks.install_pre_commit(repo, engine, force=False)
    print("AIP 已初始化（零配置）。工程信息将在用到时自动捕获，不在此追问。")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```
- [ ] **Step 3b: 改 `scripts/install_hooks.py`** — `pre_commit_body` 与 `install_claude_stop` 里的命令：
```python
    cmd = f'python "{engine_root.as_posix()}/scripts/aip_check.py" --repo-root .'
```
（两处都把 `/scripts/aip.py" check` 换成 `/scripts/aip_check.py"`。）
- [ ] **Step 4: 跑测试确认通过** — `python -m unittest tests.test_init -v` → PASS（3）。
- [ ] **Step 5: 提交** — `git add scripts/aip_init.py scripts/install_hooks.py tests/test_init.py && git commit -m "feat(aip): zero-config init; point hook at aip_check.py"`

---

### Task 10: 重建 `aip` 技能 + root-cause 沉淀对齐

**Files:** Create `plugins/ai-implementation-protocol/skills/aip/SKILL.md`；Modify `plugins/ai-implementation-protocol/skills/root-cause/SKILL.md`

**Interfaces — Produces:** skill 定义 AI 自主驱动的 AIP 行为 + 捕获纪律 + 退化链 + 禁止黑话；机器活调 `scripts/aip_check.py`/`aip_knowledge.py`/`aip_overview.py`。

- [ ] **Step 1: 写 `skills/aip/SKILL.md`**:
```markdown
---
name: aip
description: Use when the user invokes `$aip` 或要应用 AI Implementation Protocol。Skill 为主的引擎：AIP 行为由 AI 按时机自主触发，人日常只敲 `$aip init`。机器活只调 aip_check.py / aip_knowledge.py / aip_overview.py。
---

# AIP 引擎（技能为主，AI 自主驱动）

AIP 用六类活文档管项目级状态，零依赖、随处可用。命令塌缩为 AI 自主行为；人只在装 AIP 时敲 `$aip init`。每次用到 AIP 都**吭一声**报给人（记了什么、参考了哪条、跑了什么闸门），方便人观测效果。

## 六类活文档（去哪找什么）
- `.aip/OVERVIEW.md` — 多线看板（手写顶部）+ 自动摘要。开始/接手任务前读它。
- `.aip/decisions.md` — 架构/方向级决策（非任务级需求）。
- `.aip/knowledge.md`(+`_index`) — 验证过的技术坑/根因。
- `.aip/reference.md` — 领域概念/术语、核心铁律、可复用实现（裁决）。
- `.aip/inbox.md` — 旁路问题收件箱。
- `.aip/conventions.md` — 项目规约。

## 通用开发纪律（随 AIP 分发，可增补）
> 这一节是 AIP 随插件分发、对所有项目生效的纪律清单的唯一来源。以后增补规则/技巧只往这里加。
1. **禁止说黑话**：所有文档/注释/会话大白话，禁止晦涩比喻和生造术语（"scales to zero"/"footgun"/"毕业"等），公认技术名词除外。
2. **注释不引外部编号**：代码注释禁止引用 plan/需求/任务/issue 编号或外部文档名（会漂移、改名即误导）；注释只说代码本身的意图/约束，简洁自足，能不写就不写。

## AI 自主行为（按时机触发，不用人敲）
- **接手/新会话**：读 OVERVIEW 的 `▶[active]` 线 + 它的 must_read，从下一步接着干；不回放历史。
- **开一条线**：在 OVERVIEW 看板加一块（大线外挂 `tracks/<id>.md`）。
- **造新前先查**：按退化链——有 LSP 用 findReferences；查同义实现用 grep+读候选+查 reference；大工程用 nexus-query/CodeGraph（若装）。命中复用；确需造新且该成权威件 → 记 reference。
- **改接口前先查引用**：有 LSP 用 findReferences/incomingCalls，否则 grep。
- **撞见无关问题**：先在 knowledge+inbox 检索，没有再整理投 inbox（不无脑 append）。
- **验证出根因**：用 root-cause 沉淀进 knowledge（先写 draft）。

## 捕获纪律（所有沉淀通用）
拟草稿 → 读目标文档比对去重（像就并/加关联，不像才新增）→ 写 `状态: draft` → 吭一声。draft 直到人确认才 active；从不擅自当权威、不静默改旧内容。只收**已验证**的进 knowledge；trivial 且同文件的顺手修、不登记。

## 完成闸门（一条线做完时）
1. 跑 `python scripts/aip_check.py --repo-root .`（红了挡住，逐条修）。
2. 范围内纠偏：只整理本次碰过的条目及其直接关联（draft/diff，不静默改）。
3. 捕获回扫：列本次具体学到/碰到的候选——进 knowledge/inbox/reference/conventions/config？
4. 改完 knowledge 跑 `python scripts/aip_knowledge.py --repo-root .`；刷新总览 `python scripts/aip_overview.py --repo-root .`。
5. 把该线移出看板。

## $aip init（唯一人敲的命令）
`python scripts/aip_init.py --repo-root .` —— 零配置：建 `.aip/` 骨架、写引导块、装钩子；**不问工程任何事**，工程信息（构建/测试命令、规约、概念）用到时自动捕获。

## 不做
- 不探查/记录本机装了哪些外部工具（平台每会话已给可用清单，用时现场挑）。
- 不为搜索加后端（破坏零依赖）。
```
- [ ] **Step 2: 对齐 root-cause 沉淀** — 用 Grep 在 `skills/root-cause/SKILL.md` 定位写 `knowledge.md` 的骨架段，确保：`状态` 默认 `draft`、必含 `适用范围`、改后提示 `python scripts/aip_knowledge.py --repo-root .`、并走捕获纪律（先检索去重）。已一致则只补「默认 draft + 先检索去重」一句。
- [ ] **Step 3: 自检** —
```bash
python - <<'PY'
import pathlib
s = pathlib.Path("plugins/ai-implementation-protocol/skills/aip/SKILL.md").read_text(encoding="utf-8")
assert s.startswith("---") and "name: aip" in s
for m in ["OVERVIEW.md","$aip init","禁止说黑话","注释不引外部编号","完成闸门","捕获纪律"]:
    assert m in s, f"SKILL 缺: {m}"
assert "aip.py" not in s, "不应引用已删的 aip.py 路由"
print("OK")
PY
```
- [ ] **Step 4: 提交** — `git add plugins/ai-implementation-protocol/skills && git commit -m "feat(aip): rebuild aip skill (AI-autonomous, capture discipline, no-jargon); align root-cause"`

---

### Task 11: 协议正文 + sync + 全绿 check + 自托管 v1（里程碑）

**Files:** Modify `.aip/protocols/ai-implementation-protocol.md`；运行 `sync_plugin.py`、`aip_overview.py`、`aip_knowledge.py`、`aip_check.py`

**Interfaces — Consumes:** 前 10 个 Task 的产物。**Produces:** 协议反映 spec 模型；双副本同步；本仓库 `aip check` 全绿 = v1 自托管成立。

- [ ] **Step 1: 改协议正文** — `.aip/protocols/ai-implementation-protocol.md`，用 Grep 定位逐点改写（中文大白话、结论先行、**禁止黑话**）：
  - 文档模型 → 六类（OVERVIEW 看板+派生 / decisions 架构级 / knowledge 技术坑 / reference 这工程是什么+复用 / inbox 旁路 / conventions 规约）；删除 per-feature 包描述。
  - 接管 → 读 OVERVIEW active 线 + must_read。
  - 新增「自动捕获 + 完成闸门」节：两路捕获、统一写入纪律（草稿→去重→draft→吭一声）、完成闸门两档、只收已验证。
  - 新增「外部工具退化链」节：能力意图、不内置不探查、用时现场挑、产物与 `.aip/` 解耦。
  - 新增「通用开发纪律」一节：**指向** aip 技能里那节为唯一来源（禁止说黑话、注释不引外部编号，可增补），注明随分发生效、不在协议里复制清单。
  - `aip check` 职责 → 活文档存在/索引一致/知识字段/旧残留/双副本。
  - 命令 → AI 自主，人只敲 init；可靠性靠钩子+完成闸门+开场引导。
- [ ] **Step 2: 同步双副本** — `python scripts/sync_plugin.py --repo-root .`（无报错）。
- [ ] **Step 3: 刷新派生物 + 跑全量 check** —
```bash
python scripts/aip_knowledge.py --repo-root .
python scripts/aip_overview.py --repo-root .
python scripts/aip_check.py --repo-root .
```
Expected: `aip check 通过`（退出码 0）。若报旧残留/未迁移文件——按提示清。
- [ ] **Step 4: 全量单测** — `python -m unittest discover -s tests -v` → 全绿。
- [ ] **Step 5: 装钩子（自托管）+ 提交** —
```bash
python scripts/install_hooks.py --repo-root . --engine-root .
git add -A
git commit -m "feat(aip): protocol reflects new model; sync; check green; self-host v1"
```
里程碑达成：本仓库用新引擎管自己，pre-commit 钩子上线，check 全绿。

---

## Self-Review

**1. 对 spec 覆盖**
- 六类文档（spec §3）→ Task 8（模板+迁移）、Task 1（常量）、Task 11（协议）。OVERVIEW 合并 → Task 7（派生）+ Task 8（模板手写区+AUTO 区）。reference 升级 → Task 8。✅
- 自我成长引擎（spec §4）M1 去重/M2 范围内纠偏 → 写进技能（Task 10 捕获纪律 + 完成闸门）与协议（Task 11）；**M2 全本纠偏、M3 反链派生明确列二期**。✅（部分，已声明）
- 自动捕获两路 + 写入纪律（spec §5）→ Task 10 技能 + Task 11 协议。✅
- 命令塌缩 AI 自主、吭一声（spec §6）→ Task 10 技能；可靠性三层（钩子 Task 9、完成闸门 Task 10、开场引导 Task 6）。✅
- 零配置 init（spec §7）→ Task 9。✅
- 钩子项目级（改指 aip_check）→ Task 9；开场只指路 → Task 6；禁止黑话（spec §8）→ Global Constraints + Task 10 + Task 11。✅
- 外部工具退化链（spec §9）→ 写进技能 Task 10 + 协议 Task 11。✅
- 自托管里程碑（spec §11）→ Task 11。✅

**2. Placeholder scan**：code step 均完整代码；markdown step 给整文件内容或精确改写点 + 自检脚本。无 TBD。✅

**3. Type consistency**：`PROJECT_LIVING_FILES/FORBIDDEN_SLOT_FILENAMES/REQUIRED_KNOWLEDGE_FIELDS`（Task 1）贯穿 check（3–5）、init（9）；`check_*`/`run_all`（3–5）一致；`upsert_block`（Task 6）被 overview（7）复用；`expected_index_text/parse_entries`（2）被 check（3–4）、overview（7）复用；钩子命令 `aip_check.py`（9）与脚本名一致。✅

**4. 明确不纳入**：M2 全本语义纠偏、M3 反链派生、自动捕获回扫的完整编排、使用统计、归档、方法骨架（假设分级/证据标签）、力度分档 —— 二期，建议用装好的 v1 自己来管（第一次自我迭代）。
