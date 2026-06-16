# AIP 上手体验 v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 AIP 上手改成对话式/自引导/对后续 AI 自暴露，并补齐协议完整性与健壮性缺口，Claude + Codex 双端平价。

**Architecture:** 单一 `aip.py` 仍是唯一逻辑源；新增薄命令层（`~/.claude/commands/aip/*.md` 子目录命名空间得 `/aip:*`）与 skill 路由只做转发。引导式 init / 对话式 start 写在 `aip` skill 指令里（方法让位 superpowers，缺则 AIP 原生回退）。发现机制由 init 向 `CLAUDE.md`+`AGENTS.md` 写幂等托管块。完整性由 `aip check` 读取 `config.yaml` gates 交叉核对实现。

**Tech Stack:** Python 3 标准库（无第三方）；测试 `unittest` + `subprocess`；skill/命令为 Markdown。

---

## 文件结构

顶层源（改后 `sync_plugin.py` 再生到 plugin；commands/ 需单独纳入分发，见 Task 9）：
- Modify `scripts/aip_start_feature.py` — must_read 补 knowledge_index（修复 B）
- Modify `scripts/aip_resume.py` — 未初始化友好提示（修复 D）
- Create `scripts/aip_done.py` — 置 done + 跑 check + 失败回滚（修复 E）
- Modify `scripts/aip.py` — 加 `done` 子命令
- Modify `scripts/aip_check.py` — config.yaml gates 交叉核对（修复 C）+ competing_artifacts 指纹（修复 F）
- Create `scripts/aip_discovery.py` — CLAUDE.md/AGENTS.md 托管块（M5）
- Modify `scripts/aip_init.py` — 调用 discovery 双写
- Modify `scripts/install_claude_plugin.py` — 安装 commands 到 ~/.claude/commands/aip
- Modify `scripts/sync_plugin.py` — 把 commands 纳入分发同步

Plugin-only（不被 sync 覆盖，直接编辑）：
- Create `plugins/ai-implementation-protocol/commands/aip/{init,start,resume,check,knowledge,done}.md`
- Modify `plugins/ai-implementation-protocol/skills/aip/SKILL.md` — 路由补 knowledge/done（修复 A）+ 引导式 init(M2) + 对话式 start(M3) + 回退(M4)

测试：
- Create `tests/test_onboarding.py`

---

## Task 1: start 的 must_read 补 knowledge_index（修复 B）

**Files:**
- Modify: `scripts/aip_start_feature.py`
- Test: `tests/test_onboarding.py`

- [ ] **Step 1: 写失败测试**

Create `tests/test_onboarding.py`:

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


class StartMustRead(unittest.TestCase):
    def test_start_keeps_knowledge_index_in_must_read(self):
        d = init_repo()
        assert run("start", "2026-06-16-x", "--title", "X", "--repo-root", str(d)).returncode == 0
        ct = json.loads((d / ".aip/_runtime/current_task.json").read_text(encoding="utf-8"))
        self.assertIn(".aip/knowledge_index.md", ct["must_read"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试看它失败**

Run: `python -m unittest tests.test_onboarding.StartMustRead -v`
Expected: FAIL（must_read 不含 knowledge_index）

- [ ] **Step 3: 修 must_read**

Modify `scripts/aip_start_feature.py`, `must_read` 列表加一行：

```python
        "must_read": [
            f"{AIP_DIR}/protocols/ai-implementation-protocol.md",
            f"{AIP_DIR}/STATUS.md",
            f"{AIP_DIR}/canonical-assets.md",
            f"{AIP_DIR}/knowledge_index.md",
            f"{AIP_DIR}/features/{args.feature_id}/spec.md",
            f"{AIP_DIR}/features/{args.feature_id}/handoff.md",
        ]
```

- [ ] **Step 4: 跑测试看它通过**

Run: `python -m unittest tests.test_onboarding.StartMustRead -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/aip_start_feature.py tests/test_onboarding.py
git commit -m "fix(aip): keep knowledge_index in must_read after start"
```

---

## Task 2: resume 未初始化友好提示（修复 D）

**Files:**
- Modify: `scripts/aip_resume.py`
- Test: `tests/test_onboarding.py`

- [ ] **Step 1: 加失败测试**

在 `tests/test_onboarding.py` 末尾（`if __name__` 之前）加：

```python
class ResumeGraceful(unittest.TestCase):
    def test_resume_without_init_is_friendly(self):
        d = Path(tempfile.mkdtemp())  # 未 init
        r = run("resume", "--repo-root", str(d))
        self.assertEqual(r.returncode, 1)
        self.assertIn("aip init", r.stdout)
        self.assertNotIn("Traceback", r.stderr)
```

- [ ] **Step 2: 跑测试看它失败**

Run: `python -m unittest tests.test_onboarding.ResumeGraceful -v`
Expected: FAIL（抛 traceback / 无友好文案）

- [ ] **Step 3: 改 resume 容错**

Modify `scripts/aip_resume.py` 的 `main()`，把读取 current_task 改为先判存在：

```python
    target_repo = Path(args.repo_root).resolve()
    ct_path = current_task_path(target_repo)
    if not ct_path.exists():
        print("AIP 未初始化（缺 .aip/_runtime/current_task.json）。请先运行 `$aip init`。")
        return 1
    current_task = read_json(ct_path)
```

(import 已有 `current_task_path`；无需新增。)

- [ ] **Step 4: 跑测试看它通过**

Run: `python -m unittest tests.test_onboarding.ResumeGraceful -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/aip_resume.py tests/test_onboarding.py
git commit -m "fix(aip): friendly message when resume runs before init"
```

---

## Task 3: `aip done` 命令（修复 E）

**Files:**
- Create: `scripts/aip_done.py`
- Modify: `scripts/aip.py`
- Test: `tests/test_onboarding.py`

- [ ] **Step 1: 加失败测试**

在 `tests/test_onboarding.py` 末尾加：

```python
class DoneCommand(unittest.TestCase):
    def test_done_rolls_back_when_check_fails(self):
        d = init_repo()
        run("start", "2026-06-16-x", "--title", "X", "--repo-root", str(d))
        # spec/verification 未完成 → check 失败 → status 应回滚不为 done
        r = run("done", "--repo-root", str(d))
        self.assertEqual(r.returncode, 1)
        ct = json.loads((d / ".aip/_runtime/current_task.json").read_text(encoding="utf-8"))
        self.assertNotEqual(ct["status"], "done")
```

- [ ] **Step 2: 跑测试看它失败**

Run: `python -m unittest tests.test_onboarding.DoneCommand -v`
Expected: FAIL（aip.py 无 done 子命令，returncode=2）

- [ ] **Step 3: 写 aip_done.py**

Create `scripts/aip_done.py`:

```python
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from _aip_common import current_task_path, iso_now, read_json, write_json

SCRIPT_DIR = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Mark the active AIP feature done (gated by aip check).")
    parser.add_argument("--repo-root", required=True, help="Target project root.")
    args = parser.parse_args()

    target_repo = Path(args.repo_root).resolve()
    ct_path = current_task_path(target_repo)
    if not ct_path.exists():
        print("AIP 未初始化。请先运行 `$aip init`。")
        return 1

    current_task = read_json(ct_path)
    prev_status = current_task.get("status", "in_progress")
    current_task["status"] = "done"
    current_task["last_updated"] = iso_now()
    write_json(ct_path, current_task)

    check = subprocess.call([sys.executable, str(SCRIPT_DIR / "aip_check.py"), "--repo-root", str(target_repo)])
    if check != 0:
        current_task["status"] = prev_status
        current_task["last_updated"] = iso_now()
        write_json(ct_path, current_task)
        print(f"完成闸门未通过；status 已回滚为 '{prev_status}'。修复上面的问题后重试 `$aip done`。")
        return 1

    print("Feature marked done; AIP check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: aip.py 加 done 子命令**

Modify `scripts/aip.py`：在 `knowledge_parser` 之后加

```python
    done_parser = subparsers.add_parser("done", help="Mark the active feature done (runs aip check; rolls back on fail).")
    add_repo_root(done_parser)
```

在 `if args.command == "knowledge":` 块之后加

```python
    if args.command == "done":
        return run_script("aip_done.py", ["--repo-root", args.repo_root])
```

- [ ] **Step 5: 跑测试看它通过**

Run: `python -m unittest tests.test_onboarding.DoneCommand -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add scripts/aip_done.py scripts/aip.py tests/test_onboarding.py
git commit -m "feat(aip): add 'aip done' command (gated by check, rolls back on fail)"
```

---

## Task 4: check 读取 config.yaml gates 交叉核对（修复 C）

**Files:**
- Modify: `scripts/aip_check.py`
- Test: `tests/test_onboarding.py`

- [ ] **Step 1: 加失败测试**

在 `tests/test_onboarding.py` 末尾加：

```python
class ConfigGates(unittest.TestCase):
    def _set_done_with_full_feature(self, d: Path, verification_extra: str):
        run("start", "2026-06-16-x", "--title", "X", "--repo-root", str(d))
        fd = d / ".aip/features/2026-06-16-x"
        (fd / "spec.md").write_text("## Goal\ng\n## Scope\ns\n## Acceptance Criteria\n1. a\n", encoding="utf-8")
        (fd / "verification.md").write_text(
            "## Machine Gates\n| gate | result | evidence |\n|--|--|--|\n" + verification_extra
            + "\n## Independent Review\nreviewer=other\n", encoding="utf-8")
        ct = json.loads((d / ".aip/_runtime/current_task.json").read_text(encoding="utf-8"))
        ct["status"] = "done"
        (d / ".aip/_runtime/current_task.json").write_text(json.dumps(ct, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_done_fails_when_declared_gate_not_covered(self):
        d = init_repo()
        cfg = d / ".aip/config.yaml"
        cfg.write_text("gates:\n  tests:\n    cmd: \"pytest -q\"\n", encoding="utf-8")
        self._set_done_with_full_feature(d, "| build | pass | log |")  # 覆盖 build，没覆盖 tests
        r = run("check", "--repo-root", str(d))
        self.assertEqual(r.returncode, 1)
        self.assertIn("tests", r.stdout)

    def test_warns_when_no_gates_declared(self):
        d = init_repo()
        r = run("check", "--repo-root", str(d))  # 模板 gates 全空
        self.assertIn("未声明任何机器闸门", r.stdout)
```

- [ ] **Step 2: 跑测试看它失败**

Run: `python -m unittest tests.test_onboarding.ConfigGates -v`
Expected: FAIL（check 当前不读 config gates）

- [ ] **Step 3: 加 gates 解析与核对**

Modify `scripts/aip_check.py`：

(a) 加解析函数（放在 `knowledge_problems` 之后）：

```python
def parse_declared_gates(config_text: str) -> list[str]:
    """从 config.yaml 的 gates: 块取出声明了非空 cmd 的闸门名（标准库轻量解析）。"""
    lines = config_text.splitlines()
    in_gates = False
    current_gate = None
    declared: list[str] = []
    for raw in lines:
        if raw.strip().startswith("#"):
            continue
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip())
        stripped = raw.strip()
        if indent == 0:
            in_gates = stripped.startswith("gates:")
            current_gate = None
            continue
        if not in_gates:
            continue
        if indent == 2 and stripped.endswith(":"):
            current_gate = stripped[:-1].strip()
        elif indent >= 4 and stripped.startswith("cmd:") and current_gate:
            val = stripped[len("cmd:"):].strip().strip('"').strip("'")
            if val:
                declared.append(current_gate)
                current_gate = None
    return declared


def gate_coverage_problems(target_repo: Path, verification_text: str, status_done: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    cfg = project_living_path(target_repo, "config.yaml")
    declared = parse_declared_gates(read_text(cfg)) if cfg.exists() else []
    if not declared:
        warnings.append("config.yaml 未声明任何机器闸门（gates.*.cmd 全空）——证据绑定弱")
        return errors, warnings
    if status_done:
        for name in declared:
            if name not in verification_text:
                errors.append(f"verification.md 未覆盖 config 声明的 gate: {name}")
    return errors, warnings
```

(b) 在 `main()` 的活动 feature done 闸门里接线。找到 done 分支：

```python
                if current_task.get("status") == "done":
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

(c) 非 done 时也给"未声明闸门"软告警。在 knowledge 接线块之后加：

```python
    if not (ct_path.exists() and done_flag):
        _, g_warn = gate_coverage_problems(target_repo, "", False)
        warnings.extend(g_warn)
```

- [ ] **Step 4: 跑测试看它通过**

Run: `python -m unittest tests.test_onboarding.ConfigGates -v`
Expected: PASS（两条都过）

- [ ] **Step 5: 提交**

```bash
git add scripts/aip_check.py tests/test_onboarding.py
git commit -m "feat(aip): check cross-verifies config.yaml gates against verification"
```

---

## Task 5: competing_artifacts 指纹去误报（修复 F）

**Files:**
- Modify: `scripts/aip_check.py`
- Test: `tests/test_onboarding.py`

- [ ] **Step 1: 加失败测试**

在 `tests/test_onboarding.py` 末尾加：

```python
class CompetingArtifacts(unittest.TestCase):
    def test_non_aip_file_with_slot_name_not_flagged(self):
        d = init_repo()
        docs = d / "docs"
        docs.mkdir()
        (docs / "verification.md").write_text("# 验收说明\n普通文档，不是 AIP 槽位\n", encoding="utf-8")
        r = run("check", "--repo-root", str(d))
        self.assertNotIn("Competing AIP artifact", r.stdout)

    def test_real_slot_outside_aip_is_flagged(self):
        d = init_repo()
        bad = d / "docs"
        bad.mkdir()
        (bad / "verification.md").write_text("## Machine Gates\n| g | pass | e |\n", encoding="utf-8")
        r = run("check", "--repo-root", str(d))
        self.assertIn("Competing AIP artifact", r.stdout)
```

- [ ] **Step 2: 跑测试看它失败**

Run: `python -m unittest tests.test_onboarding.CompetingArtifacts -v`
Expected: FAIL（第一条误报）

- [ ] **Step 3: 给 competing_artifacts 加内容指纹**

Modify `scripts/aip_check.py` 的 `competing_artifacts`：

```python
# AIP 槽位文件的内容指纹：命中文件名后还需含对应标记，才判为真槽位（降误报）。
SLOT_MARKERS = {
    "current_task.json": '"must_read"',
    "handoff.md": "## Next Action",
    "verification.md": "## Machine Gates",
    "session_log.md": "# Session Log",
    "task_board.yaml": "status:",
}


def competing_artifacts(target_repo: Path) -> list[str]:
    """扫 .aip 之外是否漏出真正的 AIP 槽位文件（文件名命中 + 内容指纹命中）= 并行产物/漂移。"""
    hits: list[str] = []
    slots = set(AIP_SLOT_FILENAMES)
    for root, dirs, files in os.walk(target_repo):
        dirs[:] = [d for d in dirs if d not in SCAN_PRUNE_DIRS]
        for name in files:
            if name not in slots:
                continue
            marker = SLOT_MARKERS.get(name)
            try:
                text = (Path(root) / name).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if marker and marker not in text:
                continue
            hits.append(str(Path(root) / name))
    return hits
```

- [ ] **Step 4: 跑测试看它通过**

Run: `python -m unittest tests.test_onboarding.CompetingArtifacts -v`
Expected: PASS（误报消失、真槽位仍报）

- [ ] **Step 5: 提交**

```bash
git add scripts/aip_check.py tests/test_onboarding.py
git commit -m "fix(aip): competing-artifact scan uses content fingerprint to cut false positives"
```

---

## Task 6: CLAUDE.md + AGENTS.md 托管引导块（M5）

**Files:**
- Create: `scripts/aip_discovery.py`
- Modify: `scripts/aip_init.py`
- Test: `tests/test_onboarding.py`

- [ ] **Step 1: 加失败测试**

在 `tests/test_onboarding.py` 末尾加：

```python
class DiscoveryBlocks(unittest.TestCase):
    def test_init_writes_idempotent_blocks_to_both_files(self):
        d = init_repo()
        for fn in ("CLAUDE.md", "AGENTS.md"):
            txt = (d / fn).read_text(encoding="utf-8")
            self.assertIn("BEGIN AIP (managed)", txt)
            self.assertIn(".aip/knowledge_index.md", txt)
        # 用户内容 + 重跑 init 不破坏、不重复
        (d / "CLAUDE.md").write_text("# 我的项目\n保留我\n\n" + (d / "CLAUDE.md").read_text(encoding="utf-8"), encoding="utf-8")
        assert run("init", "--repo-root", str(d)).returncode == 0
        txt = (d / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("保留我", txt)
        self.assertEqual(txt.count("BEGIN AIP (managed)"), 1)
```

- [ ] **Step 2: 跑测试看它失败**

Run: `python -m unittest tests.test_onboarding.DiscoveryBlocks -v`
Expected: FAIL（init 不写 CLAUDE.md/AGENTS.md）

- [ ] **Step 3: 写 aip_discovery.py**

Create `scripts/aip_discovery.py`:

```python
from __future__ import annotations

from pathlib import Path

BEGIN = "<!-- BEGIN AIP (managed) -->"
END = "<!-- END AIP (managed) -->"

BLOCK_BODY = (
    "## AI Implementation Protocol\n"
    "本仓库用 AIP 管理实现工作。后续 AI 会话请先读：\n"
    "- `.aip/STATUS.md` 现状真理源\n"
    "- `.aip/_runtime/current_task.json` 当前任务指针 + must_read\n"
    "- `.aip/knowledge_index.md` 已沉淀真因索引（遇问题先查）\n"
    "命令：`$aip resume` 续作 / `$aip check` 校验 / 详见 `.aip/protocols/`。\n"
)


def managed_block() -> str:
    return f"{BEGIN}\n{BLOCK_BODY}{END}\n"


def upsert_managed_block(path: Path) -> None:
    """幂等写入托管块：不存在则建；有标记则只替换标记区；否则末尾追加。保持文件原换行。"""
    block = managed_block()
    if not path.exists():
        path.write_text(block, encoding="utf-8", newline="\n")
        return
    text = path.read_text(encoding="utf-8")
    if BEGIN in text and END in text:
        pre = text[: text.index(BEGIN)]
        post = text[text.index(END) + len(END):]
        new = pre + block.rstrip("\n") + post
    else:
        sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
        new = text + sep + block
    path.write_text(new, encoding="utf-8")
```

- [ ] **Step 4: init 调用双写**

Modify `scripts/aip_init.py`：

(a) import 加：
```python
from aip_discovery import upsert_managed_block
```

(b) 在写 README（`write_text(root / "README.md", readme)`）之后加：
```python
    upsert_managed_block(target_repo / "CLAUDE.md")
    upsert_managed_block(target_repo / "AGENTS.md")
```

- [ ] **Step 5: 跑测试看它通过**

Run: `python -m unittest tests.test_onboarding.DiscoveryBlocks -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add scripts/aip_discovery.py scripts/aip_init.py tests/test_onboarding.py
git commit -m "feat(aip): init writes idempotent AIP discovery block to CLAUDE.md and AGENTS.md"
```

---

## Task 7: 命令可见性层（commands/aip/*.md）

**Files:**
- Create: `plugins/ai-implementation-protocol/commands/aip/{init,start,resume,check,knowledge,done}.md`

每个文件用 frontmatter `description` + 调用 `aip.py`。子目录 `aip/` 即命名空间，安装到 `~/.claude/commands/aip/init.md` → `/aip:init`。

- [ ] **Step 1: 建六个命令文件**

Create `plugins/ai-implementation-protocol/commands/aip/init.md`:
```markdown
---
description: 初始化 AIP（建 .aip/、引导填 config.yaml、写 CLAUDE.md/AGENTS.md 引导块）
---
运行 AIP 初始化，然后按 `aip` skill 的「引导式 init」访谈用户填好 `.aip/config.yaml`：
`python <plugin-root>/scripts/aip.py init --repo-root .`
```

Create `plugins/ai-implementation-protocol/commands/aip/start.md`:
```markdown
---
description: 对话式开始一个新特性（口述需求→头脑风暴→自动生成 id/title/spec 初稿）
---
不要让用户手敲 id/--title。按 `aip` skill 的「对话式 start」与用户对话形成任务描述，再调用：
`python <plugin-root>/scripts/aip.py start <生成的id> --title "<生成的title>" --repo-root .`
```

Create `plugins/ai-implementation-protocol/commands/aip/resume.md`:
```markdown
---
description: 续作当前 AIP 任务（读 current_task + must_read 后再动手）
---
`python <plugin-root>/scripts/aip.py resume --repo-root .`
```

Create `plugins/ai-implementation-protocol/commands/aip/check.md`:
```markdown
---
description: 校验 AIP 交接完整性（活文档/槽位/闸门/知识索引/反漂移）
---
`python <plugin-root>/scripts/aip.py check --repo-root .`
```

Create `plugins/ai-implementation-protocol/commands/aip/knowledge.md`:
```markdown
---
description: 由 knowledge.md 重建知识索引 knowledge_index.md
---
`python <plugin-root>/scripts/aip.py knowledge --repo-root .`
```

Create `plugins/ai-implementation-protocol/commands/aip/done.md`:
```markdown
---
description: 收尾：把当前特性置 done 并跑 check（不过则回滚）
---
`python <plugin-root>/scripts/aip.py done --repo-root .`
```

- [ ] **Step 2: 验证文件齐全**

Run:
```bash
python - <<'PY'
import pathlib
c = pathlib.Path("plugins/ai-implementation-protocol/commands/aip")
need = {"init","start","resume","check","knowledge","done"}
have = {p.stem for p in c.glob("*.md")}
assert need == have, (need, have)
for p in c.glob("*.md"):
    assert "description:" in p.read_text(encoding="utf-8"), p
print("commands OK")
PY
```
Expected: `commands OK`

- [ ] **Step 3: 提交**

```bash
git add plugins/ai-implementation-protocol/commands/
git commit -m "feat(aip): per-command visibility layer (/aip:* commands)"
```

---

## Task 8: 安装器装 commands + sync 纳入 commands

**Files:**
- Modify: `scripts/install_claude_plugin.py`
- Modify: `scripts/sync_plugin.py`
- Test: `tests/test_onboarding.py`

- [ ] **Step 1: 加失败测试**

在 `tests/test_onboarding.py` 末尾加：

```python
class InstallCommands(unittest.TestCase):
    def test_claude_installer_installs_commands(self):
        home = Path(tempfile.mkdtemp())
        r = subprocess.run([sys.executable, str(REPO / "scripts/install_claude_plugin.py"),
                            "--home", str(home), "--force"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((home / ".claude/commands/aip/init.md").exists())
        self.assertTrue((home / ".claude/commands/aip/done.md").exists())
```

- [ ] **Step 2: 跑测试看它失败**

Run: `python -m unittest tests.test_onboarding.InstallCommands -v`
Expected: FAIL（安装器不装 commands）

- [ ] **Step 3: install_claude_plugin 安装 commands**

Modify `scripts/install_claude_plugin.py`，加函数：

```python
def install_commands(source_plugin: Path, home: Path, force: bool) -> list[Path]:
    src_root = source_plugin / "commands"
    if not src_root.exists():
        return []
    installed: list[Path] = []
    for src in sorted(src_root.rglob("*.md")):
        rel = src.relative_to(src_root)
        dest = home / ".claude" / "commands" / rel
        if dest.exists() and not force:
            raise SystemExit(f"Command exists: {dest}. Re-run with --force to replace it.")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        installed.append(dest)
    return installed
```

并在 `main()` 调用（install_skills 之后）：

```python
    installed = install_skills(destination_plugin, home, args.force)
    installed_cmds = install_commands(destination_plugin, home, args.force)

    print(f"Installed Claude Code plugin: {destination_plugin}")
    for path in installed:
        print(f"Installed skill: {path}")
    for path in installed_cmds:
        print(f"Installed command: {path}")
    print("Restart Claude Code or open a new session for the skills to be picked up.")
    return 0
```

- [ ] **Step 4: sync_plugin 纳入 commands（top-level → plugin 不适用，commands 是 plugin-only，无需 sync；但确保 sync 不误删）**

确认 `scripts/sync_plugin.py` 的 `SYNCED_DIRS = ["scripts", "docs", "templates", "schemas"]` **不含 commands**，故 sync 不会删除 plugin 的 commands/（commands 是 plugin-only 手写资产，类比 skills）。无需改动；此步仅为确认。

- [ ] **Step 5: 跑测试看它通过**

Run: `python -m unittest tests.test_onboarding.InstallCommands -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add scripts/install_claude_plugin.py tests/test_onboarding.py
git commit -m "feat(aip): claude installer installs /aip:* commands"
```

---

## Task 9: aip skill —— 路由补全 + 引导式 init + 对话式 start

**Files:**
- Modify: `plugins/ai-implementation-protocol/skills/aip/SKILL.md`

- [ ] **Step 1: 描述与 Supported forms 补 knowledge/done**

Modify frontmatter `description` 末尾追加：`，重建知识索引（$aip knowledge），收尾置 done（$aip done）。`

把 Supported forms 代码块改为：
```text
$aip init
$aip start 2026-04-26-my-feature --title "My feature"
$aip resume
$aip check
$aip knowledge
$aip done
$aip help
```

- [ ] **Step 2: Routing Rules 补两条**

在 `- $aip check:` 行之后加：
```markdown
- `$aip knowledge`: run `python <plugin-root>/scripts/aip.py knowledge --repo-root .`.
- `$aip done`: run `python <plugin-root>/scripts/aip.py done --repo-root .`.
```

- [ ] **Step 3: 加「引导式 init」小节（M2）**

在 `## Working Rules` 之前插入：

```markdown
## Guided Init (after `$aip init` scaffolds files)

`aip init` 只负责脚手架。脚手架后**由你引导用户填 `.aip/config.yaml`**，逐项 Stop-and-ask，不替用户臆断：

1. **truth_sources**：扫描仓库（README/docs/约定文件）提候选，请用户确认权威文档。
2. **gates**：探测技术栈（package.json / pyproject.toml / *.sln / go.mod 等），为 tests/build/lint_or_drift/e2e 建议真实命令，逐条确认后写入 `cmd`。
3. **lenses**：按改动域（前端/客户端等）建议，可选。
4. **iron_rules**：问项目硬约束（编码要求、契约重生成、未授权不提交等）。
5. **process_skills**：检测到 superpowers 则建议设 `superpowers`，否则留空。

每写一项就更新 `.aip/config.yaml`。完成后跑 `$aip check` 自检。
```

- [ ] **Step 4: 加「对话式 start」小节（M3）**

紧接其后插入：

```markdown
## Conversational Start (user just describes a need)

用户**口述需求**即可，不要求其先给 id/title：

1. **方法层**：若 `.aip/config.yaml` `process_skills: superpowers`，让位 superpowers **brainstorming** 把需求探清并形成设计；否则走 AIP 原生轻量访谈（目的/范围/验收/约束几问）。
2. **生成**：从对话收敛出 `feature_id = <今天日期>-<标题派生的 kebab slug>`、`title`、以及 `spec.md` 初稿（Goal/Scope/Acceptance Criteria 用对话内容预填）。
3. **脚手架**：调用 `python <plugin-root>/scripts/aip.py start <feature_id> --title "<title>" --repo-root .`，随后把 spec 初稿写入该 feature 的 `spec.md`。

用户全程不手敲 id/`--title`。
```

- [ ] **Step 5: 验证 skill 内容**

Run:
```bash
python - <<'PY'
t = open("plugins/ai-implementation-protocol/skills/aip/SKILL.md", encoding="utf-8").read()
for need in ["$aip knowledge", "$aip done", "Guided Init", "Conversational Start", "brainstorming"]:
    assert need in t, need
print("skill OK")
PY
```
Expected: `skill OK`

- [ ] **Step 6: 提交**

```bash
git add plugins/ai-implementation-protocol/skills/aip/SKILL.md
git commit -m "feat(aip): skill routes knowledge/done; adds guided init + conversational start"
```

---

## Task 10: schemas 处置（修复 G）+ 协议文档

**Files:**
- Modify: `docs/protocol.md`

- [ ] **Step 1: 在协议文档标注 schemas 为参考**

Modify `docs/protocol.md` 的 `## Optional Knowledge Sources` 之前或合适处加一句：

```markdown
### Schemas are reference-only
`schemas/*.json` document the shape of `current_task.json` / `task_board.yaml` for humans
and tooling. `aip check` does **not** validate against them (no third-party dependency);
they are guidance, not an enforced gate.
```

- [ ] **Step 2: 提交**

```bash
git add docs/protocol.md
git commit -m "docs(aip): clarify schemas are reference-only, not enforced"
```

---

## Task 11: 同步 plugin 副本 + 全量验证（双端）

**Files:**
- Modify: `plugins/ai-implementation-protocol/{scripts,docs}/*`（由 sync 再生）

- [ ] **Step 1: 同步**

Run: `python scripts/sync_plugin.py`
Expected: `synced: scripts` / `synced: docs` / … / `Plugin sync complete.`

- [ ] **Step 2: 全量单测**

Run: `python -m unittest discover -s tests -v`
Expected: 全部 OK（含上一特性的 knowledge 测试 + 本次 onboarding 测试）

- [ ] **Step 3: plugin 副本端到端（init→start→knowledge→check→done）**

Run:
```bash
python - <<'PY'
import tempfile, subprocess, sys, pathlib, json
aip = "plugins/ai-implementation-protocol/scripts/aip.py"
d = tempfile.mkdtemp()
def call(*a): 
    r = subprocess.run([sys.executable, aip, *a, "--repo-root", d], capture_output=True, text=True); return r
assert call("init").returncode == 0
# 双写发现块
for fn in ("CLAUDE.md","AGENTS.md"):
    assert "BEGIN AIP (managed)" in pathlib.Path(d, fn).read_text(encoding="utf-8")
assert call("start", "2026-06-16-x", "--title", "X").returncode == 0
assert call("knowledge").returncode == 0
assert call("check").returncode == 0
print("plugin e2e OK")
PY
```
Expected: `plugin e2e OK`

- [ ] **Step 4: 双端安装器（Claude 装 skills+commands，Codex 装 skills）**

Run:
```bash
python - <<'PY'
import tempfile, subprocess, sys, pathlib
for script, base, want_cmds in [
    ("scripts/install_claude_plugin.py", ".claude", True),
    ("scripts/install_codex_plugin.py", ".agents", False),
]:
    home = tempfile.mkdtemp()
    r = subprocess.run([sys.executable, script, "--home", home, "--force"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    sk = pathlib.Path(home, base, "skills")
    assert (sk/"aip/SKILL.md").exists() and (sk/"root-cause/SKILL.md").exists(), base
    if want_cmds:
        assert pathlib.Path(home, base, "commands/aip/init.md").exists(), "claude commands missing"
print("installers OK (claude: skills+commands, codex: skills)")
PY
```
Expected: `installers OK (claude: skills+commands, codex: skills)`

- [ ] **Step 5: 提交**

```bash
git add plugins/ai-implementation-protocol
git commit -m "chore(aip): sync plugin package with onboarding-ux v2"
```

---

## Self-Review 记录

- **Spec 覆盖**：M1→Task3/9（done/路由）+Task7/8（commands）；M2→Task9；M3→Task9+Task1（must_read）；M4→Task9（回退）；M5→Task6；M6→Task4；M7→Task5（误报）+Task10（schemas）；修复 A→Task9，B→Task1，C→Task4，D→Task2，E→Task3，F→Task5，G→Task10。Codex 平价→Task11 Step4 + AGENTS.md(Task6) + 原生回退(Task9)。
- **占位符**：无 TBD；每个代码步给完整代码；命令/ skill 为完整 Markdown。
- **类型/命名一致**：`upsert_managed_block`(Task6) 在 init 调用名一致；`parse_declared_gates`/`gate_coverage_problems`(Task4)、`competing_artifacts`+`SLOT_MARKERS`(Task5)、`install_commands`(Task8) 定义即被同任务使用；`aip_done.py`(Task3) 子命令名 `done` 与 commands/skill 一致。
- **待实现期细节**：插件不改名（命令呈 `/ai-implementation-protocol:aip:*`？——注：子目录命名空间用的是 `~/.claude/commands/aip/`，得 `/aip:*`，与插件名无关）；config 解析用标准库行解析（Task4）；schemas 取参考标注（Task10）。
```
