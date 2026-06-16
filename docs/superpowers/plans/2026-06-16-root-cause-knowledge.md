# 根因导向调查 + 知识沉淀机制 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 AIP 增加"根因调查 skill + 可主动调用的知识库（含自动索引、防腐校验）"，随插件分发到任意仓库。

**Architecture:** 方法层是一个 AI 可主动加载的 `root-cause` skill（直接写在 plugin 包内，因 `sync_plugin.py` 不同步 skills/）。产物层是 `.aip/knowledge.md`（append-only 真理源，顶部 `## 类目`）+ `.aip/knowledge_index.md`（由 `aip_knowledge.py` 从 knowledge.md 幂等派生）。`aip init` 生成它们、把索引写进 `must_read`；`aip check` 校验索引一致性（恒）、条目完整性与类目合法（done 闸门）、过期（软告警）。顶层 scripts/docs/templates 改完后 `sync_plugin.py` 再生 plugin 副本；安装器改为安装 plugin 下全部 skill。

**Tech Stack:** Python 3（标准库，无第三方依赖）；测试用 `unittest` + `subprocess` 跑脚本对真实临时仓库断言。

---

## 文件结构

顶层规范源（改完由 `sync_plugin.py` 再生到 plugin）：
- Create `templates/knowledge-template.md` — knowledge.md 初始模板（`## 类目` + 写法说明 + 一条示例占位说明）
- Create `scripts/aip_knowledge.py` — 解析 knowledge.md、生成索引（被 init/check/CLI 共用的单一来源）
- Modify `scripts/_aip_common.py` — `PROJECT_LIVING_FILES` 增两文件
- Modify `scripts/aip_init.py` — 跳过无模板的 living 文件、生成索引、must_read 增索引、README 文案
- Modify `scripts/aip.py` — 增 `knowledge` 子命令
- Modify `scripts/aip_check.py` — 增知识校验（索引一致性/完整性/类目/过期）
- Modify `docs/protocol.md` — 安全机制清单加第 9 条

Plugin-only（不被 sync 覆盖，直接编辑）：
- Create `plugins/ai-implementation-protocol/skills/root-cause/SKILL.md`
- Modify `plugins/ai-implementation-protocol/skills/aip/SKILL.md` — debug 行加 AIP-native fallback

安装器：
- Modify `scripts/install_claude_plugin.py` — 装 plugin 下全部 skill
- Modify `scripts/install_codex_plugin.py` — 同上（dest 为 `~/.agents/skills`）

测试：
- Create `tests/test_root_cause_knowledge.py`

---

## Task 1: 知识库模板 + living docs 接线

**Files:**
- Create: `templates/knowledge-template.md`
- Modify: `scripts/_aip_common.py`（`PROJECT_LIVING_FILES`）

- [ ] **Step 1: 写知识库模板**

Create `templates/knowledge-template.md`:

```markdown
# 知识库（验证过的根因 / 坎 / 领域事实）

append-only。过时条目不删，标 `状态: superseded(by K-00X)`。
改完跑 `aip knowledge` 重建 `knowledge_index.md`。

## 类目
process-lifecycle | concurrency | build | config | ui | data | deployment | domain | other

<!--
新增条目复制下面骨架，ID 递增；标题一句话：

## K-001: 标题
- 分类: process-lifecycle
- 状态: active
- 症状: <可观察表象>
- 根因: <已验证的真正原因>
- 证据: <命令输出 / 代码引用 / 复现步骤>
- 适用范围: <在什么条件下成立>
- 最后复核: 2026-06-16
- 关联: ADR-N / findings#N / feature-id
-->
```

- [ ] **Step 2: 把两文件登记为项目级活文档**

Modify `scripts/_aip_common.py`, `PROJECT_LIVING_FILES`:

```python
PROJECT_LIVING_FILES = [
    "STATUS.md",
    "canonical-assets.md",
    "decisions.md",
    "findings.md",
    "knowledge.md",
    "knowledge_index.md",
    "config.yaml",
]
```

- [ ] **Step 3: 提交**

```bash
git add templates/knowledge-template.md scripts/_aip_common.py
git commit -m "feat(aip): register knowledge.md/knowledge_index.md as living docs"
```

---

## Task 2: 索引生成器 `aip_knowledge.py`

**Files:**
- Create: `scripts/aip_knowledge.py`

- [ ] **Step 1: 写生成器**

Create `scripts/aip_knowledge.py`:

```python
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _aip_common import project_living_path, read_text, write_text

INDEX_HEADER = (
    "# 知识索引（自动生成，勿手改；运行 `aip knowledge` 重建）\n"
    "# 格式: ID | 分类 | 状态 | 标题 | 最后复核\n"
)

ENTRY_RE = re.compile(r"^## (K-\d+):\s*(.*)$")
FIELD_RE = re.compile(r"^- (\S+?):\s*(.*)$")


def parse_categories(text: str) -> list[str]:
    """读取顶部 '## 类目' 区声明的合法类目集。"""
    cats: list[str] = []
    capturing = False
    for line in text.splitlines():
        s = line.strip()
        if s == "## 类目":
            capturing = True
            continue
        if capturing and s.startswith("## "):
            break
        if capturing and s and not s.startswith("#"):
            cats.extend(t for t in re.split(r"[|,，\s]+", s) if t)
    return cats


def parse_entries(text: str) -> list[dict]:
    """解析所有 '## K-NNN: 标题' 条目及其 '- 字段: 值'。"""
    entries: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        s = line.strip()
        m = ENTRY_RE.match(s)
        if m:
            if cur:
                entries.append(cur)
            cur = {"id": m.group(1), "title": m.group(2).strip(), "fields": {}}
            continue
        if cur:
            fm = FIELD_RE.match(s)
            if fm:
                cur["fields"][fm.group(1)] = fm.group(2).strip()
    if cur:
        entries.append(cur)
    return entries


def render_index(entries: list[dict]) -> str:
    lines = [INDEX_HEADER]
    for e in entries:
        f = e["fields"]
        lines.append(
            f'{e["id"]} | {f.get("分类", "")} | {f.get("状态", "")} | {e["title"]} | {f.get("最后复核", "")}'
        )
    return "\n".join(lines).rstrip() + "\n"


def expected_index_text(target_repo: Path) -> str:
    kn = project_living_path(target_repo, "knowledge.md")
    text = read_text(kn) if kn.exists() else ""
    return render_index(parse_entries(text))


def rebuild_index(target_repo: Path) -> Path:
    dst = project_living_path(target_repo, "knowledge_index.md")
    write_text(dst, expected_index_text(target_repo))
    return dst


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild the AIP knowledge index from knowledge.md.")
    parser.add_argument("--repo-root", required=True, help="Target project root.")
    args = parser.parse_args()
    dst = rebuild_index(Path(args.repo_root).resolve())
    print(f"Knowledge index rebuilt: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: 手测幂等性**

Run:
```bash
python - <<'PY'
import tempfile, pathlib, sys
sys.path.insert(0, "scripts")
from aip_knowledge import render_index, parse_entries
txt = "## 类目\nprocess-lifecycle | ui\n\n## K-001: 杀进程后仍 running\n- 分类: process-lifecycle\n- 状态: active\n- 最后复核: 2026-06-16\n"
print(render_index(parse_entries(txt)))
PY
```
Expected: 输出含 `K-001 | process-lifecycle | active | 杀进程后仍 running | 2026-06-16`

- [ ] **Step 3: 提交**

```bash
git add scripts/aip_knowledge.py
git commit -m "feat(aip): knowledge index generator (single source from knowledge.md)"
```

---

## Task 3: `aip init` 生成知识库 + 索引进 must_read

**Files:**
- Modify: `scripts/aip_init.py`

- [ ] **Step 1: 改 init —— 模板映射、跳过无模板项、生成索引、must_read、README**

Modify `scripts/aip_init.py`:

(a) import 增 `rebuild_index`：
```python
from aip_knowledge import rebuild_index
```

(b) `LIVING_TEMPLATE_MAP` 增 knowledge.md（注意：knowledge_index.md 无模板，靠生成）：
```python
LIVING_TEMPLATE_MAP = {
    "STATUS.md": "status-template.md",
    "canonical-assets.md": "canonical-assets-template.md",
    "decisions.md": "decisions-template.md",
    "findings.md": "findings-template.md",
    "knowledge.md": "knowledge-template.md",
    "config.yaml": "config-template.yaml",
}
```

(c) living docs 生成循环改为跳过无模板项：
```python
    for name in PROJECT_LIVING_FILES:
        tpl_name = LIVING_TEMPLATE_MAP.get(name)
        if not tpl_name:
            continue  # 无模板的（knowledge_index.md）由生成器产出
        dest = project_living_path(target_repo, name)
        if dest.exists() and not args.force:
            continue
        tpl = template_root / "templates" / tpl_name
        write_text(dest, tpl.read_text(encoding="utf-8"))

    rebuild_index(target_repo)  # 由 knowledge.md 派生 knowledge_index.md
```

(d) `current_task["must_read"]` 增索引：
```python
        "must_read": [
            f"{AIP_DIR}/protocols/ai-implementation-protocol.md",
            f"{AIP_DIR}/STATUS.md",
            f"{AIP_DIR}/knowledge_index.md",
        ],
```

(e) README 文案在 `findings.md` 行后插入两行：
```python
        "- `findings.md`：侧发现收件箱（开发时撞见的无关问题，捕获别追）\n"
        "- `knowledge.md`：知识库（验证过的根因/坎/领域事实，append-only，先查后挖）\n"
        "- `knowledge_index.md`：知识索引（自动生成，勿手改，`aip knowledge` 重建）\n"
        "- `config.yaml`：本项目适配配置（真理源/机器闸门命令/适用 lens）\n"
```

- [ ] **Step 2: 手测 init**

Run:
```bash
python - <<'PY'
import tempfile, subprocess, sys, json, pathlib
d = tempfile.mkdtemp()
subprocess.check_call([sys.executable, "scripts/aip.py", "init", "--repo-root", d])
root = pathlib.Path(d, ".aip")
assert (root/"knowledge.md").exists(), "knowledge.md missing"
assert (root/"knowledge_index.md").exists(), "index missing"
ct = json.loads((root/"_runtime/current_task.json").read_text(encoding="utf-8"))
assert ".aip/knowledge_index.md" in ct["must_read"], ct["must_read"]
print("OK", d)
PY
```
Expected: 打印 `OK <tmp>`，无 AssertionError

- [ ] **Step 3: 提交**

```bash
git add scripts/aip_init.py
git commit -m "feat(aip): init scaffolds knowledge.md + generated index, adds index to must_read"
```

---

## Task 4: `aip knowledge` 子命令

**Files:**
- Modify: `scripts/aip.py`

- [ ] **Step 1: 加 knowledge 子命令**

Modify `scripts/aip.py`:

(a) 在 `check_parser` 之后加：
```python
    knowledge_parser = subparsers.add_parser("knowledge", help="Rebuild the knowledge index from knowledge.md.")
    add_repo_root(knowledge_parser)
```

(b) 在 `if args.command == "check":` 块之后加：
```python
    if args.command == "knowledge":
        return run_script("aip_knowledge.py", ["--repo-root", args.repo_root])
```

- [ ] **Step 2: 手测**

Run:
```bash
python - <<'PY'
import tempfile, subprocess, sys
d = tempfile.mkdtemp()
subprocess.check_call([sys.executable, "scripts/aip.py", "init", "--repo-root", d])
subprocess.check_call([sys.executable, "scripts/aip.py", "knowledge", "--repo-root", d])
print("OK")
PY
```
Expected: 打印 `Knowledge index rebuilt: ...` 与 `OK`

- [ ] **Step 3: 提交**

```bash
git add scripts/aip.py
git commit -m "feat(aip): add 'aip knowledge' subcommand to rebuild index"
```

---

## Task 5: `aip check` 知识库校验

**Files:**
- Modify: `scripts/aip_check.py`

- [ ] **Step 1: 加知识校验函数**

Modify `scripts/aip_check.py`:

(a) imports 顶部加：
```python
from datetime import date, datetime

from aip_knowledge import expected_index_text, parse_categories, parse_entries
```

(b) 加函数（放在 `done_gate_problems` 之后）：
```python
STALE_DAYS = 180


def knowledge_problems(target_repo: Path, status_done: bool) -> tuple[list[str], list[str]]:
    """知识库校验：索引一致性(恒/错误)、条目完整性+类目合法(done/错误)、过期(恒/告警)。"""
    errors: list[str] = []
    warnings: list[str] = []
    kn = project_living_path(target_repo, "knowledge.md")
    if not kn.exists():
        return errors, warnings

    text = read_text(kn)
    cats = set(parse_categories(text))
    for e in parse_entries(text):
        f = e["fields"]
        eid = e["id"]
        cat = f.get("分类", "")
        status = f.get("状态", "")
        last = f.get("最后复核", "")

        if status_done:
            if not cat:
                errors.append(f"knowledge.md {eid} missing 分类")
            elif cat not in cats:
                errors.append(f'knowledge.md {eid} 分类 "{cat}" not in declared ## 类目')
            for fld in ("状态", "症状", "根因", "最后复核"):
                if not f.get(fld):
                    errors.append(f"knowledge.md {eid} missing {fld}")

        if last:
            try:
                d = datetime.strptime(last, "%Y-%m-%d").date()
            except ValueError:
                warnings.append(f'knowledge.md {eid} 最后复核 "{last}" not YYYY-MM-DD')
            else:
                if status.startswith("active") and (date.today() - d).days > STALE_DAYS:
                    warnings.append(f"knowledge.md {eid} active but last verified {last} (>{STALE_DAYS}d) — review")

    idx = project_living_path(target_repo, "knowledge_index.md")
    if not idx.exists():
        errors.append("knowledge_index.md missing — run `aip knowledge`")
    elif read_text(idx).strip() != expected_index_text(target_repo).strip():
        errors.append("knowledge_index.md is stale — run `aip knowledge` to rebuild")

    return errors, warnings
```

(c) 在 `main()` 里接线。在 competing_artifacts 循环之后、活动 feature 校验之前插入：
```python
    warnings: list[str] = []
    done_flag = False
    tp = current_task_path(target_repo)
    if tp.exists():
        try:
            done_flag = read_json(tp).get("status") == "done"
        except Exception:
            done_flag = False
    k_err, k_warn = knowledge_problems(target_repo, done_flag)
    errors.extend(k_err)
    warnings.extend(k_warn)
```

(d) 在最后 `if errors:` 之前打印告警：
```python
    for w in warnings:
        print(f"warning: {w}")

    if errors:
```

- [ ] **Step 2: 手测三种情形**

Run:
```bash
python - <<'PY'
import tempfile, subprocess, sys, pathlib
d = tempfile.mkdtemp()
subprocess.check_call([sys.executable, "scripts/aip.py", "init", "--repo-root", d])
kn = pathlib.Path(d, ".aip/knowledge.md")
# 加一条过期 active 条目，但先不重建索引 → 期望 check 失败(索引不一致)
kn.write_text(kn.read_text(encoding="utf-8") +
  "\n## K-001: 旧真因\n- 分类: ui\n- 状态: active\n- 症状: x\n- 根因: y\n- 最后复核: 2000-01-01\n",
  encoding="utf-8")
r = subprocess.run([sys.executable, "scripts/aip.py", "check", "--repo-root", d], capture_output=True, text=True)
assert r.returncode == 1 and "stale" in r.stdout, r.stdout
# 重建索引后 → check 通过，但打印过期告警
subprocess.check_call([sys.executable, "scripts/aip.py", "knowledge", "--repo-root", d])
r = subprocess.run([sys.executable, "scripts/aip.py", "check", "--repo-root", d], capture_output=True, text=True)
assert r.returncode == 0, r.stdout
assert "warning:" in r.stdout and ">180d" in r.stdout, r.stdout
print("OK")
PY
```
Expected: 打印 `OK`

- [ ] **Step 3: 提交**

```bash
git add scripts/aip_check.py
git commit -m "feat(aip): check validates knowledge index consistency, completeness, staleness"
```

---

## Task 6: 自动化测试

**Files:**
- Create: `tests/test_root_cause_knowledge.py`

- [ ] **Step 1: 写 unittest**

Create `tests/test_root_cause_knowledge.py`:

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
    r = run("init", "--repo-root", str(d))
    assert r.returncode == 0, r.stderr
    return d


class KnowledgeMechanism(unittest.TestCase):
    def test_init_creates_knowledge_and_index_in_must_read(self):
        d = init_repo()
        self.assertTrue((d / ".aip/knowledge.md").exists())
        self.assertTrue((d / ".aip/knowledge_index.md").exists())
        ct = json.loads((d / ".aip/_runtime/current_task.json").read_text(encoding="utf-8"))
        self.assertIn(".aip/knowledge_index.md", ct["must_read"])

    def test_knowledge_rebuild_is_idempotent_and_indexes_entries(self):
        d = init_repo()
        kn = d / ".aip/knowledge.md"
        kn.write_text(
            kn.read_text(encoding="utf-8")
            + "\n## K-001: 杀进程后仍 running\n- 分类: process-lifecycle\n- 状态: active\n"
            "- 症状: x\n- 根因: y\n- 最后复核: 2026-06-16\n",
            encoding="utf-8",
        )
        self.assertEqual(run("knowledge", "--repo-root", str(d)).returncode, 0)
        idx = (d / ".aip/knowledge_index.md").read_text(encoding="utf-8")
        self.assertIn("K-001 | process-lifecycle | active | 杀进程后仍 running | 2026-06-16", idx)

    def test_check_fails_on_stale_index(self):
        d = init_repo()
        kn = d / ".aip/knowledge.md"
        kn.write_text(
            kn.read_text(encoding="utf-8")
            + "\n## K-001: t\n- 分类: ui\n- 状态: active\n- 症状: x\n- 根因: y\n- 最后复核: 2026-06-16\n",
            encoding="utf-8",
        )
        r = run("check", "--repo-root", str(d))
        self.assertEqual(r.returncode, 1)
        self.assertIn("stale", r.stdout)

    def test_check_warns_but_passes_on_old_entry(self):
        d = init_repo()
        kn = d / ".aip/knowledge.md"
        kn.write_text(
            kn.read_text(encoding="utf-8")
            + "\n## K-001: t\n- 分类: ui\n- 状态: active\n- 症状: x\n- 根因: y\n- 最后复核: 2000-01-01\n",
            encoding="utf-8",
        )
        run("knowledge", "--repo-root", str(d))
        r = run("check", "--repo-root", str(d))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("warning:", r.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试**

Run: `python -m unittest tests.test_root_cause_knowledge -v`
Expected: 4 tests, all OK

- [ ] **Step 3: 提交**

```bash
git add tests/test_root_cause_knowledge.py
git commit -m "test(aip): cover knowledge index/check mechanism"
```

---

## Task 7: root-cause skill（plugin-only）

**Files:**
- Create: `plugins/ai-implementation-protocol/skills/root-cause/SKILL.md`
- Modify: `plugins/ai-implementation-protocol/skills/aip/SKILL.md`

- [ ] **Step 1: 写 root-cause skill**

Create `plugins/ai-implementation-protocol/skills/root-cause/SKILL.md`:

```markdown
---
name: root-cause
description: Use when facing any bug, error, crash, unexpected behavior, "why does this happen", or a debugging/investigation request — before proposing any fix. Drives root-cause investigation (recall known causes, falsify, dig past the symptom) and deposits verified causes into the AIP knowledge base.
---

# 根因导向调查

遇到问题**先别打补丁**。表面修复只搬走症状，真正的价值在挖到能在代码/配置/环境里指出来的**根因**，再把判断交给用户。

## 核心循环（强制顺序）

0. **先查后挖（recall 优先）**
   - 读 `.aip/knowledge_index.md`，用当前症状/类目命中已知真因。
   - 命中条目是**先验假设，不是结论**：①用当前证据重新确认是否仍成立（看"最后复核"日期，过期项尤其重验）；②照样列出别的竞争假设，主动问"还有没有别的可能"。
   - 旧结论被证伪 → 在 `.aip/knowledge.md` 标 `状态: superseded(by K-00X)` 并写新条目。
   - 原则：**先验加速调查，但不豁免证伪。**
1. **禁止直接给修复** —— 先精确复述可观察症状。
2. **取证复现** —— 命令输出/日志/代码引用，不靠脑补。
3. **列 2–3 个竞争假设** —— 不认定第一个。
4. **证据判别** —— 用最便宜的探针逐层下沉，定位真正断裂那一层。
5. **区分症状 vs 根因** —— 挖到具体可指之物为止。
6. **交用户判断** —— 摆出【根因 + 证据 + 修复选项 + 各自取舍】，由用户决策（接 AIP Stop-and-ask），不擅自实施深层改动。
7. **沉淀** —— 验证过的真因写入 `.aip/knowledge.md`（按顶部 `## 类目` 选分类，填全字段），然后跑 `aip knowledge` 重建索引；属决策的进 `decisions.md`，无关侧发现进 `findings.md`。

## 时刻保持

- **警惕与证伪**：任何假设（含索引命中的旧条目）都要试图推翻，证据不足不下结论。
- **知识库正确可用**：沉淀后立即重建索引；过期/失配条目复核或标 superseded，不留腐烂。

## 与 superpowers 的关系

若仓库 `process_skills: superpowers`，方法深度让位给 `systematic-debugging`；但本 skill 的 AIP 残留物（knowledge 条目 + 交用户判断）仍由它拥有，落 `.aip/` slot，不另起平行位置。无 superpowers 时本 skill 独立完整运行。
```

- [ ] **Step 2: aip skill 的 debug 行加 fallback**

Modify `plugins/ai-implementation-protocol/skills/aip/SKILL.md`，把映射表 debug 行改为：

```markdown
| debug | `.aip/knowledge.md`（根因沉淀）+ 索引 | root-cause（AIP-native，先查后挖+证伪）；superpowers 在场时方法让位 systematic-debugging |
```

- [ ] **Step 3: 提交**

```bash
git add plugins/ai-implementation-protocol/skills/root-cause/SKILL.md plugins/ai-implementation-protocol/skills/aip/SKILL.md
git commit -m "feat(aip): add root-cause investigation skill; wire into aip debug phase"
```

---

## Task 8: 协议文档第 9 条机制

**Files:**
- Modify: `docs/protocol.md`

- [ ] **Step 1: 安全机制清单加第 9 条**

Modify `docs/protocol.md`，在第 8 条 Side-finding 之后加：

```markdown
9. **Root-cause-first investigation & knowledge sedimentation** — on any bug/unexpected
   behavior, don't patch the symptom: recall known causes from `.aip/knowledge_index.md`
   (a hit is a prior hypothesis to re-verify, not an answer), enumerate competing
   hypotheses, dig to a cause you can point at in code/config/environment, then hand the
   cause + evidence + options to the user. Verified causes are deposited (append-only) in
   `.aip/knowledge.md` under a declared `## 类目`; the derived `.aip/knowledge_index.md` is
   rebuilt via `aip knowledge`. `aip check` validates index consistency (always), entry
   completeness + legal category (done gate), and flags entries unverified for >180 days.
```

- [ ] **Step 2: 提交**

```bash
git add docs/protocol.md
git commit -m "docs(aip): add safeguard #9 root-cause-first investigation + knowledge"
```

---

## Task 9: 安装器装全部 skill

**Files:**
- Modify: `scripts/install_claude_plugin.py`
- Modify: `scripts/install_codex_plugin.py`

- [ ] **Step 1: Claude 安装器改为遍历 plugin/skills/**

Modify `scripts/install_claude_plugin.py`，把 `install_skill` 替换为遍历安装：

```python
def install_skills(source_plugin: Path, home: Path, force: bool) -> list[Path]:
    skills_root = source_plugin / "skills"
    installed: list[Path] = []
    if not skills_root.exists():
        raise SystemExit(f"Plugin skills dir not found: {skills_root}")
    for src in sorted(p for p in skills_root.iterdir() if (p / "SKILL.md").exists()):
        dest_dir = home / ".claude" / "skills" / src.name
        if dest_dir.exists():
            if not force:
                raise SystemExit(f"Skill destination exists: {dest_dir}. Re-run with --force to replace it.")
            shutil.rmtree(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / "SKILL.md", dest_dir / "SKILL.md")
        installed.append(dest_dir / "SKILL.md")
    return installed
```

并改 `main()`：
```python
    copy_plugin(source_plugin, destination_plugin, args.force)
    installed = install_skills(destination_plugin, home, args.force)

    print(f"Installed Claude Code plugin: {destination_plugin}")
    for p in installed:
        print(f"Installed skill: {p}")
    print("Restart Claude Code or open a new session for the skills to be picked up.")
    return 0
```

- [ ] **Step 2: Codex 安装器做等价改动**

先 Read `scripts/install_codex_plugin.py` 找到其安装 `aip` skill 的函数（dest 在 `~/.agents/skills/aip`）。按 Step 1 同样模式改为遍历 `source_plugin/skills/*`、dest 为 `home/".agents"/"skills"/src.name`，逐个 `print` 已装 skill。保留其 marketplace.json 逻辑不动。

- [ ] **Step 3: 手测 Claude 安装器到临时 home**

Run:
```bash
python - <<'PY'
import tempfile, subprocess, sys, pathlib
home = tempfile.mkdtemp()
subprocess.check_call([sys.executable, "scripts/install_claude_plugin.py", "--home", home, "--force"])
sk = pathlib.Path(home, ".claude/skills")
assert (sk/"aip/SKILL.md").exists(), "aip skill missing"
assert (sk/"root-cause/SKILL.md").exists(), "root-cause skill missing"
print("OK")
PY
```
Expected: 打印 `OK`（注意：本步依赖 Task 10 已把 root-cause 同步进 plugin；若先跑此步，root-cause 已直接在 plugin 内，无需 sync）

- [ ] **Step 4: 提交**

```bash
git add scripts/install_claude_plugin.py scripts/install_codex_plugin.py
git commit -m "feat(aip): installers install all plugin skills, not just aip"
```

---

## Task 10: 同步 plugin 副本 + 全量校验

**Files:**
- Modify: `plugins/ai-implementation-protocol/{scripts,docs,templates}/*`（由 sync 再生）

- [ ] **Step 1: 同步顶层规范源到 plugin**

Run: `python scripts/sync_plugin.py`
Expected: `synced: scripts` / `synced: docs` / `synced: templates` / `synced: schemas` / `Plugin sync complete.`

- [ ] **Step 2: 校验 plugin 副本里新机制齐全**

Run:
```bash
python - <<'PY'
import pathlib
p = pathlib.Path("plugins/ai-implementation-protocol")
for f in ["scripts/aip_knowledge.py", "templates/knowledge-template.md"]:
    assert (p/f).exists(), f
assert "knowledge.md" in (p/"scripts/_aip_common.py").read_text(encoding="utf-8")
assert "knowledge" in (p/"scripts/aip.py").read_text(encoding="utf-8")
assert (p/"skills/root-cause/SKILL.md").exists()
print("OK")
PY
```
Expected: 打印 `OK`

- [ ] **Step 3: 用 plugin 副本脚本对临时仓库跑端到端**

Run:
```bash
python - <<'PY'
import tempfile, subprocess, sys, pathlib
d = tempfile.mkdtemp()
aip = "plugins/ai-implementation-protocol/scripts/aip.py"
subprocess.check_call([sys.executable, aip, "init", "--repo-root", d])
r = subprocess.run([sys.executable, aip, "check", "--repo-root", d], capture_output=True, text=True)
assert r.returncode == 0, r.stdout
print("OK", d)
PY
```
Expected: 打印 `OK <tmp>`

- [ ] **Step 4: 全量单测**

Run: `python -m unittest discover -s tests -v`
Expected: all OK

- [ ] **Step 5: 提交**

```bash
git add plugins/ai-implementation-protocol
git commit -m "chore(aip): sync plugin package with knowledge mechanism"
```

---

## Self-Review 记录

- **Spec 覆盖**：AC1→Task3；AC2→Task7；AC3→Task2/4；AC4→Task5；AC5→Task10；AC6→Task7/8；AC7→既有行为不变（knowledge.md 不存在则 `knowledge_problems` 早返回；无 superpowers skill 独立运行）。
- **类型一致**：`rebuild_index`/`expected_index_text`/`parse_entries`/`parse_categories` 在 Task2 定义，Task3/5 按同名导入使用。
- **占位符**：无 TBD；每个代码步给出完整代码；Codex 安装器（Task9 Step2）要求先 Read 再按已给模式改（其源未在本仓库展示，实现时读取）。
```
