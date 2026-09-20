from __future__ import annotations

"""aip brainstorm —— 多 AI 文档讨论的确定性状态机。

议题文档落 `.aip/brainstorm/<slug>.md`，全部改动只走本脚本（AI 不直接编辑文档），
脚本负责：轮流推进（`当前轮到`）、轮次计数、收敛判定（共识/升级用户/轮次保险丝）、
文档结构检查（status 子命令）。AI 只负责读文档、写观点文本、调脚本。

文档格式（脚本自持的契约，status 按此校验）：

    # 议题：<标题>
    - 状态: discussing | converged | need-user | aborted
    - 当前轮到: <代号>
    - 轮次: N / 上限: M
    - 参与者: [甲（发起者）, 乙]
    ## 讨论记录
    ### [轮次N] <代号> · <iso时间>
    <观点>
    立场: 继续 | 同意收敛 | 需要用户裁决
    ### 【用户】 · <iso时间>
    <用户输入>
"""

import argparse
import re
import sys
from pathlib import Path

from _aip_common import aip_root, force_utf8, iso_now, read_text, repo_path, write_text

BRAINSTORM_DIR = "brainstorm"
STATUSES = ["discussing", "converged", "need-user", "aborted"]
STANCES = ["继续", "同意收敛", "需要用户裁决"]
DEFAULT_MAX_ROUNDS = 5

HEADER_PATTERNS = {
    "状态": r"^- 状态: *(\S+) *$",
    "当前轮到": r"^- 当前轮到: *(\S+) *$",
    "轮次": r"^- 轮次: *(\d+) */ *上限: *(\d+) *$",
    "参与者": r"^- 参与者: *\[(.+)\] *$",
}
ENTRY_RE = re.compile(r"^### \[轮次(\d+)\] (\S+) · (\S+) *$", re.M)
USER_ENTRY_RE = re.compile(r"^### 【(.+?)】 · (\S+) *$", re.M)


class DocError(Exception):
    """文档缺失或结构不合法时抛出，main 转成退出码 2。"""


# 自由文本（发言/插话/结论正文）里禁止出现的行：这些都是文档的控制格式，
# 正文里出现会被解析器当成结构标记（伪造立场、幽灵发言、假头部字段）。
CONTROL_LINE_RE = re.compile(r"#{1,3} |^立场 *:|^- (?:状态|当前轮到|轮次|参与者) *:")

# 参与者代号会写进 `### [轮次N] <代号> · <时间>` 条目头，空格/·/（）都会让条目解析不了。
CODE_RE = re.compile(r"^[^\s·（）]+$")


def check_free_text(text: str, what: str) -> None:
    for line in text.splitlines():
        if CONTROL_LINE_RE.match(line):
            raise DocError(
                f"{what}含有结构标记行「{line.strip()[:30]}」，会被当成控制格式解析；"
                f"请换个写法（行首加 > 或空格、去掉行首的 #）")


def validate_participants(participants: list[str]) -> None:
    if len(set(participants)) != len(participants):
        raise DocError(f"参与者代号有重复：{participants}（重名会让轮流和收敛判定错乱）")
    for p in participants:
        if not CODE_RE.match(p):
            raise DocError(f"参与者代号 {p!r} 不合法：不能含空格、·、（），否则讨论条目解析不了")


def find_doc(repo: Path, name: str) -> Path:
    """接受 slug（brainstorm 目录下找）或显式路径。"""
    p = Path(name)
    if p.suffix == ".md" or p.is_absolute() or "/" in name:
        path = p if p.is_absolute() else repo / p
    else:
        # slug 分支同样过 slugify，与 start 建档时的归一化一致（议题标题可直接当 --doc 传）
        path = aip_root(repo) / BRAINSTORM_DIR / f"{slugify(name)}.md"
    if not path.exists():
        raise DocError(f"议题文档不存在：{path}")
    return path


def slugify(topic: str) -> str:
    slug = re.sub(r"\s+", "-", topic.strip())
    return re.sub(r'[/\\:*?"<>|]', "", slug) or "untitled"


def parse_doc(text: str) -> dict:
    """解析议题文档；结构问题收进 problems（不抛异常，留给 status 展示）。"""
    problems: list[str] = []
    doc: dict = {"problems": problems, "entries": [], "user_entries": []}
    m = re.search(r"^# 议题：(.+)$", text, re.M)
    if m:
        doc["议题"] = m.group(1).strip()
    else:
        problems.append("缺 `# 议题：` 标题行")
    for field, pat in HEADER_PATTERNS.items():
        mm = re.search(pat, text, re.M)
        if not mm:
            problems.append(f"缺头部字段 `- {field}:`")
            doc[field] = None
            continue
        doc[field] = mm.groups() if field == "轮次" else mm.group(1)
    if doc["状态"] and doc["状态"] not in STATUSES:
        problems.append(f"状态值非法：{doc['状态']}（合法：{'/'.join(STATUSES)}）")
    if doc["参与者"]:
        doc["参与者列表"] = [p.strip() for p in doc["参与者"].split(",") if p.strip()]
        # 参与者条目允许带「（发起者）」标注，代号取标注前的部分
        doc["代号列表"] = [re.sub(r"（.*?）", "", p).strip() for p in doc["参与者列表"]]
    else:
        doc["参与者列表"] = doc["代号列表"] = []
    if doc["当前轮到"] and doc["代号列表"] and doc["当前轮到"] not in doc["代号列表"]:
        problems.append(f"当前轮到「{doc['当前轮到']}」不在参与者里：{doc['代号列表']}")
    if doc["轮次"]:
        doc["轮次N"], doc["上限"] = int(doc["轮次"][0]), int(doc["轮次"][1])
    else:
        doc["轮次N"] = doc["上限"] = None
    # 讨论记录条目：### [轮次N] 代号 · 时间 ... 立场: X
    for m in ENTRY_RE.finditer(text):
        seg = text[m.end():]
        nxt = re.search(r"^### ", seg, re.M)
        body = seg[: nxt.start()] if nxt else seg
        stance_m = re.search(r"^立场: *(\S+) *$", body, re.M)
        entry = {"round": int(m.group(1)), "who": m.group(2), "time": m.group(3),
                 "stance": stance_m.group(1) if stance_m else None}
        if entry["who"] not in doc["代号列表"]:
            problems.append(f"发言者「{entry['who']}」不在参与者里")
        if entry["stance"] is None:
            problems.append(f"{entry['who']} 的轮次{entry['round']} 发言缺 `立场:` 行")
        elif entry["stance"] not in STANCES:
            problems.append(f"{entry['who']} 的立场值非法：{entry['stance']}")
        doc["entries"].append(entry)
    for m in USER_ENTRY_RE.finditer(text):
        doc["user_entries"].append({"who": m.group(1), "time": m.group(2)})
    return doc


def load(repo: Path, name: str) -> tuple[Path, str, dict]:
    path = find_doc(repo, name)
    text = read_text(path)
    return path, text, parse_doc(text)


def require_discussing(doc: dict) -> None:
    if doc["problems"]:
        raise DocError("文档结构有问题，先跑 status 看详情：" + "；".join(doc["problems"]))
    if doc["状态"] != "discussing":
        raise DocError(f"议题已关闭（状态: {doc['状态']}），不能再发言")


def set_header(text: str, field: str, value: str) -> str:
    """整行替换头部字段；value 已是完整行内容（不含 `- 字段: ` 前缀）。"""
    new, n = re.subn(rf"^- {re.escape(field)}:.*$", f"- {field}: {value}",
                     text, count=1, flags=re.M)
    if n != 1:
        raise DocError(f"改头部字段失败：{field}")
    return new


def latest_stances(doc: dict) -> dict[str, str]:
    """每个参与者全部发言里的最新立场。"""
    out: dict[str, str] = {}
    for e in doc["entries"]:
        if e["stance"]:
            out[e["who"]] = e["stance"]
    return out


def evaluate(doc: dict) -> str | None:
    """收敛判定：返回新状态（need-user/converged）或 None（继续讨论）。

    - 任何发言立场「需要用户裁决」→ 立即 need-user
    - 全员最新立场都是「同意收敛」（可跨轮次，后发言覆盖旧立场）→ converged
    - 发言后进入的轮次超过上限 → need-user（保险丝）
    """
    last = doc["entries"][-1]
    if last["stance"] == "需要用户裁决":
        return "need-user"
    stances = latest_stances(doc)
    if len(stances) == len(doc["代号列表"]) and all(s == "同意收敛" for s in stances.values()):
        return "converged"
    if doc["轮次N"] is not None and doc["轮次N"] > doc["上限"]:
        return "need-user"
    return None


def print_status(path: Path, doc: dict, me: str | None = None) -> None:
    print(f"文档: {path}")
    print(f"议题: {doc.get('议题', '?')}")
    print(f"状态: {doc['状态']}")
    print(f"轮次: {doc['轮次'][0]} / 上限: {doc['轮次'][1]}" if doc["轮次"] else "轮次: ?")
    turn = doc["当前轮到"]
    if me:
        mark = "← 轮到你" if turn == me else f"← 没轮到你（你是 {me}）"
        print(f"当前轮到: {turn}  {mark}")
    else:
        print(f"当前轮到: {turn}")
    print(f"参与者: {doc['参与者']}")
    stances = latest_stances(doc)
    if stances:
        parts = [f"{w}={stances.get(w, '（未发言）')}" for w in doc["代号列表"]]
        print("各参与者最新立场: " + "  ".join(parts))
    if doc["user_entries"]:
        print(f"用户插话: {len(doc['user_entries'])} 条（最近 {doc['user_entries'][-1]['time']}）")
    if doc["problems"]:
        print("结构检查: 有问题 ——")
        for p in doc["problems"]:
            print(f"  - {p}")
    else:
        print("结构检查: 正常")


def cmd_start(repo: Path, args: argparse.Namespace) -> int:
    participants = [p.strip() for p in args.participants.split(",") if p.strip()]
    if len(participants) < 1:
        raise DocError("--participants 至少一个代号（逗号分隔，第一个是发起者）")
    validate_participants(participants)
    if args.max_rounds < 1:
        raise DocError("--max-rounds 至少为 1")
    if args.as_ != participants[0]:
        raise DocError(f"发起者代号 {args.as_!r} 必须是 --participants 的第一个 {participants[0]!r}")
    check_free_text(args.opening, "开场立场")
    slug = slugify(args.slug) if args.slug else slugify(args.topic)
    path = aip_root(repo) / BRAINSTORM_DIR / f"{slug}.md"
    if path.exists():
        raise DocError(f"议题文档已存在：{path}（换议题名或 --slug）")
    roster = ", ".join([f"{participants[0]}（发起者）", *participants[1:]])
    nxt = participants[1] if len(participants) > 1 else participants[0]
    text = (
        f"# 议题：{args.topic}\n\n"
        f"- 状态: discussing\n"
        f"- 当前轮到: {nxt}\n"
        f"- 轮次: 1 / 上限: {args.max_rounds}\n"
        f"- 参与者: [{roster}]\n\n"
        f"## 讨论记录\n\n"
        f"### [轮次1] {participants[0]} · {iso_now()}\n\n"
        f"{args.opening.rstrip()}\n\n"
        f"立场: {args.stance}\n"
    )
    # 开场也是一次发言，同样过收敛判定（单人同意收敛即收敛、需要用户裁决即升级）
    verdict = evaluate(parse_doc(text))
    if verdict:
        text = set_header(text, "状态", verdict)
    write_text(path, text)
    print(f"已建议题文档: {path}")
    if verdict == "converged":
        print("→ 单人议题且开场即同意收敛，状态已转 converged。请用 conclude 写入「结论」。")
    elif verdict == "need-user":
        print("→ 开场立场即要求用户裁决，状态已转 need-user。请用 escalate 写「待用户裁决」。")
    print_status(path, parse_doc(text))
    return 0


def cmd_say(repo: Path, args: argparse.Namespace) -> int:
    path, text, doc = load(repo, args.doc)
    require_discussing(doc)
    if args.as_ not in doc["代号列表"]:
        raise DocError(f"{args.as_!r} 不是参与者：{doc['代号列表']}")
    if doc["当前轮到"] != args.as_:
        raise DocError(f"没轮到你（当前轮到 {doc['当前轮到']}）。请等对方发言后再来")
    check_free_text(args.text, "发言正文")
    order = doc["代号列表"]
    nxt = order[(order.index(args.as_) + 1) % len(order)]
    round_n = doc["轮次N"] + (1 if nxt == order[0] else 0)
    entry = f"\n### [轮次{doc['轮次N']}] {args.as_} · {iso_now()}\n\n{args.text.rstrip()}\n\n立场: {args.stance}\n"
    text = text.rstrip("\n") + "\n" + entry
    text = set_header(text, "当前轮到", nxt)
    text = set_header(text, "轮次", f"{round_n} / 上限: {doc['上限']}")
    new_doc = parse_doc(text)
    verdict = evaluate(new_doc)
    if verdict:
        text = set_header(text, "状态", verdict)
    write_text(path, text)
    print("发言已记录。")
    if verdict == "converged":
        print("→ 全员同意收敛，状态已转 converged。请用 conclude 子命令写入「结论」。")
    elif verdict == "need-user":
        print("→ 状态已转 need-user。请用 escalate 子命令写入「待用户裁决」问题清单；"
              "用户回答后用 note --resume 恢复讨论。")
    print_status(path, parse_doc(text), me=nxt)
    return 0


def cmd_note(repo: Path, args: argparse.Namespace) -> int:
    path, text, doc = load(repo, args.doc)
    if doc["状态"] in ("converged", "aborted"):
        raise DocError(f"议题已关闭（状态: {doc['状态']}），不能再记用户插话")
    check_free_text(args.text, "用户插话")
    entry = f"\n### 【{args.by}】 · {iso_now()}\n\n{args.text.rstrip()}\n"
    text = text.rstrip("\n") + "\n" + entry
    if args.resume:
        if doc["状态"] != "need-user":
            raise DocError(f"--resume 只在状态 need-user 时用（当前 {doc['状态']}）")
        text = set_header(text, "状态", "discussing")
        if doc["轮次N"] > doc["上限"]:
            # 保险丝（超轮次）升级的：把上限抬到当前轮次，让本轮能走完；
            # 本轮走完仍无共识，保险丝会在进入下一轮时再次触发，回到用户手里
            text = set_header(text, "轮次", f"{doc['轮次N']} / 上限: {doc['轮次N']}")
    write_text(path, text)
    print("用户输入已记入文档，其他 AI 下次读文档即可看到。")
    print_status(path, parse_doc(text))
    return 0


def _append_section(path: Path, text: str, title: str, body: str) -> dict:
    text = text.rstrip("\n") + f"\n\n## {title}\n\n{body.rstrip()}\n"
    write_text(path, text)
    return parse_doc(text)


def cmd_conclude(repo: Path, args: argparse.Namespace) -> int:
    path, text, doc = load(repo, args.doc)
    if doc["状态"] != "converged":
        raise DocError(f"只有 converged 状态能写结论（当前 {doc['状态']}）")
    if re.search(r"^## 结论 *$", text, re.M):
        raise DocError("已有「结论」章节，不能重复写（要改请直接编辑该章节）")
    check_free_text(args.text, "结论")
    print("结论已写入，议题关闭。可按 AIP 捕获纪律把结论沉淀进 decisions.md / knowledge.md。")
    print_status(path, _append_section(path, text, "结论", args.text))
    return 0


def cmd_escalate(repo: Path, args: argparse.Namespace) -> int:
    path, text, doc = load(repo, args.doc)
    if doc["状态"] != "need-user":
        raise DocError(f"只有 need-user 状态能写待裁决清单（当前 {doc['状态']}）")
    if re.search(r"^## 待用户裁决 *$", text, re.M):
        raise DocError("已有「待用户裁决」章节，不能重复写（要改请直接编辑该章节）")
    check_free_text(args.text, "待裁决清单")
    print("待裁决问题已写入。请用户回答；听到的 AI 用 note --resume 记录并恢复讨论。")
    print_status(path, _append_section(path, text, "待用户裁决", args.text))
    return 0


def cmd_abort(repo: Path, args: argparse.Namespace) -> int:
    path, text, doc = load(repo, args.doc)
    if doc["状态"] not in ("discussing", "need-user"):
        raise DocError(f"只有 discussing / need-user 状态能终止（当前 {doc['状态']}）")
    if args.reason:
        check_free_text(args.reason, "终止原因")
    text = set_header(text, "状态", "aborted")
    if args.reason:
        text = text.rstrip("\n") + f"\n\n## 终止原因\n\n{args.reason.rstrip()}\n"
    write_text(path, text)
    print("议题已终止。")
    print_status(path, parse_doc(text))
    return 0


def cmd_status(repo: Path, args: argparse.Namespace) -> int:
    path, _, doc = load(repo, args.doc)
    print_status(path, doc, me=args.as_)
    return 2 if doc["problems"] else 0


def main() -> int:
    force_utf8()
    ap = argparse.ArgumentParser(description="AIP brainstorm：多 AI 文档讨论状态机。")
    ap.add_argument("--repo-root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("start", help="发起议题：建档 + 写发起者开场立场")
    p.add_argument("--topic", required=True, help="议题标题")
    p.add_argument("--as", dest="as_", required=True, help="发起者代号（须为参与者第一个）")
    p.add_argument("--participants", required=True, help="全部参与者代号，逗号分隔，第一个是发起者")
    p.add_argument("--opening", required=True, help="发起者开场立场全文")
    p.add_argument("--stance", default="继续", choices=STANCES)
    p.add_argument("--max-rounds", type=int, default=DEFAULT_MAX_ROUNDS)
    p.add_argument("--slug", default=None, help="文档文件名（默认由议题标题生成）")

    p = sub.add_parser("say", help="发言：仅当前轮到者可用，自动推进轮流并做收敛判定")
    p.add_argument("--doc", required=True, help="slug 或文档路径")
    p.add_argument("--as", dest="as_", required=True)
    p.add_argument("--text", required=True, help="发言全文")
    p.add_argument("--stance", required=True, choices=STANCES)

    p = sub.add_parser("note", help="记用户插话：不占轮次、不改当前轮到")
    p.add_argument("--doc", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--by", default="用户")
    p.add_argument("--resume", action="store_true", help="用户已回答裁决问题，恢复 discussing")

    p = sub.add_parser("conclude", help="converged 后写入「结论」")
    p.add_argument("--doc", required=True)
    p.add_argument("--text", required=True)

    p = sub.add_parser("escalate", help="need-user 后写入「待用户裁决」问题清单")
    p.add_argument("--doc", required=True)
    p.add_argument("--text", required=True)

    p = sub.add_parser("abort", help="发起者终止议题")
    p.add_argument("--doc", required=True)
    p.add_argument("--reason", default=None)

    p = sub.add_parser("status", help="检查文档状态与结构（只读）")
    p.add_argument("--doc", required=True)
    p.add_argument("--as", dest="as_", default=None, help="带上代号会告诉你是否轮到你")

    args = ap.parse_args()
    repo = repo_path(args.repo_root)
    handlers = {"start": cmd_start, "say": cmd_say, "note": cmd_note,
                "conclude": cmd_conclude, "escalate": cmd_escalate,
                "abort": cmd_abort, "status": cmd_status}
    try:
        return handlers[args.cmd](repo, args)
    except DocError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
