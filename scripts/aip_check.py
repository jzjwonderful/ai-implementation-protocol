from __future__ import annotations

import argparse
import os
from datetime import date, datetime
from pathlib import Path

from _aip_common import (
    AIP_DIR,
    AIP_SLOT_FILENAMES,
    PROJECT_LIVING_FILES,
    REQUIRED_FEATURE_FILES,
    SCAN_PRUNE_DIRS,
    aip_root,
    current_task_path,
    feature_dir,
    project_living_path,
    read_json,
    read_text,
)
from aip_knowledge import expected_index_text, parse_categories, parse_entries

STALE_DAYS = 180

SPEC_REQUIRED_HEADINGS = ["## Goal", "## Scope", "## Acceptance Criteria"]
HANDOFF_REQUIRED = [
    "## Current Phase", "## Current Task", "## Completed Work", "## Remaining Work",
    "## Blockers", "## Next Action", "## Files Touched", "## Verification Status",
]


def count_in_progress(task_board_text: str) -> int:
    return sum(
        1 for line in task_board_text.splitlines()
        if line.strip().startswith("status:") and "in_progress" in line
    )


def missing(items: list[str], text: str) -> list[str]:
    return [i for i in items if i not in text]


def section_body(text: str, heading: str) -> str:
    """返回某 '## 标题' 与下一个 '## ' 之间的正文（判断是否被填）。"""
    lines = text.splitlines()
    out: list[str] = []
    capturing = False
    for line in lines:
        if line.strip() == heading:
            capturing = True
            continue
        if capturing and line.startswith("## "):
            break
        if capturing:
            out.append(line)
    return "\n".join(out).strip()


def unclassified_findings(findings_text: str) -> int:
    """真实条目状态行含 '待分类' 且不含 '|'（'|' 是模板菜单行）。"""
    return sum(
        1 for line in findings_text.splitlines()
        if line.strip().startswith("- 发现") and "待分类" in line and "|" not in line
    )


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


def done_gate_problems(verification_text: str, spec_text: str) -> list[str]:
    """status==done 时的残渣校验：闸门绑真证据、spec/verification 真被填。"""
    problems: list[str] = []
    if "## Machine Gates" not in verification_text:
        problems.append("verification.md missing '## Machine Gates' section")
    if "| fail |" in verification_text:
        problems.append("verification.md has a gate with result 'fail'")
    if "| <" in verification_text:
        problems.append("verification.md still has unfilled placeholder gate rows ('| <...')")
    if "## Independent Review" not in verification_text:
        problems.append("verification.md missing '## Independent Review' (fresh-eyes) section")
    if not section_body(spec_text, "## Acceptance Criteria"):
        problems.append("spec.md '## Acceptance Criteria' is empty")
    return problems


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


def parse_declared_gates(config_text: str) -> list[str]:
    """从 config.yaml 的 gates: 块取出声明了非空 cmd 的闸门名（标准库轻量解析）。"""
    in_gates = False
    current_gate = None
    declared: list[str] = []
    for raw in config_text.splitlines():
        if raw.strip().startswith("#") or not raw.strip():
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AIP: living docs, slots, gates, anti-drift.")
    parser.add_argument("--repo-root", required=True, help="Target project root.")
    args = parser.parse_args()

    target_repo = Path(args.repo_root).resolve()
    errors: list[str] = []

    # --- 始终校验：AIP 目录与项目级活文档 ---
    if not aip_root(target_repo).exists():
        print(f"AIP check failed:\n- Missing AIP directory: {aip_root(target_repo)} (run `aip init`)")
        return 1

    for name in PROJECT_LIVING_FILES:
        if not project_living_path(target_repo, name).exists():
            errors.append(f"Missing project living doc: {project_living_path(target_repo, name)}")

    findings = project_living_path(target_repo, "findings.md")
    if findings.exists():
        n = unclassified_findings(read_text(findings))
        if n:
            errors.append(f"findings.md has {n} unclassified (待分类) side-finding(s) — classify before completion")

    # --- 始终校验：无并行产物（AIP 槽位文件漏出 .aip 之外）---
    for hit in competing_artifacts(target_repo):
        errors.append(f"Competing AIP artifact outside {AIP_DIR}/: {hit} (AIP state must live only under {AIP_DIR}/)")

    # --- 知识库校验：索引一致性(恒)、条目完整性(done)、过期(软告警) ---
    warnings: list[str] = []
    done_flag = False
    ct_path = current_task_path(target_repo)
    if ct_path.exists():
        try:
            done_flag = read_json(ct_path).get("status") == "done"
        except Exception:
            done_flag = False
    k_err, k_warn = knowledge_problems(target_repo, done_flag)
    errors.extend(k_err)
    warnings.extend(k_warn)

    # --- 机器闸门覆盖：非 done 时给"未声明闸门"软告警（done 时在下方带 verification 核对）---
    if not done_flag:
        _, g_warn = gate_coverage_problems(target_repo, "", False)
        warnings.extend(g_warn)

    # --- 活动 feature 校验（无 active feature 则跳过，使其可当提交闸门）---
    task_path = current_task_path(target_repo)
    if task_path.exists():
        current_task = read_json(task_path)
        fid = current_task.get("feature_id", "")
        if fid:
            fd = feature_dir(target_repo, fid)
            if not fd.exists():
                errors.append(f"Missing feature directory: {fd}")
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

                # --- 完成闸门：残渣校验只在 status==done ---
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

    for w in warnings:
        print(f"warning: {w}")

    if errors:
        print("AIP check failed:")
        for item in errors:
            print(f"- {item}")
        return 1

    print("AIP check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
