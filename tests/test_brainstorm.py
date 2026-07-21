import argparse
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import aip_brainstorm as bs


def ns(**kw):
    return argparse.Namespace(**kw)


class BrainstormCase(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())

    def start(self, participants="甲,乙", max_rounds=2, stance="继续"):
        bs.cmd_start(self.repo, ns(topic="测试议题", as_="甲", participants=participants,
                                   opening="我的开场观点", stance=stance,
                                   max_rounds=max_rounds, slug=None))

    def say(self, who, stance, text="我的看法"):
        return bs.cmd_say(self.repo, ns(doc="测试议题", as_=who, text=text, stance=stance))

    def doc(self):
        path, text, doc = bs.load(self.repo, "测试议题")
        return path, text, doc


class Start(BrainstormCase):
    def test_creates_doc_with_opening_and_turn_on_second(self):
        self.start()
        path, text, doc = self.doc()
        self.assertTrue(path.exists())
        self.assertEqual(doc["状态"], "discussing")
        self.assertEqual(doc["当前轮到"], "乙")  # 开场算甲的轮次1发言，轮到乙
        self.assertEqual(doc["轮次N"], 1)
        self.assertEqual(doc["上限"], 2)
        self.assertEqual(doc["代号列表"], ["甲", "乙"])
        self.assertEqual(doc["entries"][0]["who"], "甲")
        self.assertEqual(doc["problems"], [])

    def test_existing_doc_rejected(self):
        self.start()
        with self.assertRaises(bs.DocError):
            self.start()

    def test_initiator_must_be_first_participant(self):
        with self.assertRaises(bs.DocError):
            bs.cmd_start(self.repo, ns(topic="x", as_="乙", participants="甲,乙",
                                       opening="o", stance="继续", max_rounds=2, slug=None))


class Say(BrainstormCase):
    def test_turn_enforced(self):
        self.start()
        with self.assertRaises(bs.DocError):
            self.say("甲", "继续")  # 当前轮到乙

    def test_turn_advances_and_round_wraps(self):
        self.start()
        self.say("乙", "继续")
        _, _, doc = self.doc()
        self.assertEqual(doc["当前轮到"], "甲")
        self.assertEqual(doc["轮次N"], 2)  # 末位发完言 → 轮次+1，首位开始新一轮
        self.say("甲", "继续")
        _, _, doc = self.doc()
        self.assertEqual(doc["当前轮到"], "乙")
        self.assertEqual(doc["轮次N"], 2)

    def test_unknown_speaker_rejected(self):
        self.start()
        with self.assertRaises(bs.DocError):
            bs.cmd_say(self.repo, ns(doc="测试议题", as_="丙", text="x", stance="继续"))

    def test_closed_doc_rejects_say(self):
        self.start(participants="甲,乙", stance="同意收敛")
        self.say("乙", "同意收敛")  # 全员同意 → converged
        with self.assertRaises(bs.DocError):
            self.say("甲", "继续")


class Convergence(BrainstormCase):
    def test_all_agree_converges(self):
        self.start(stance="同意收敛")
        self.assertEqual(self.say("乙", "同意收敛"), 0)
        _, _, doc = self.doc()
        self.assertEqual(doc["状态"], "converged")
        bs.cmd_conclude(self.repo, ns(doc="测试议题", text="共识：就这么干"))
        _, text, _ = self.doc()
        self.assertIn("## 结论", text)
        self.assertIn("共识：就这么干", text)

    def test_cross_round_agree_converges(self):
        # 甲轮次1说「继续」、轮次2改口「同意收敛」，乙轮次1已「同意收敛」→ 按最新立场收敛
        self.start()
        self.say("乙", "同意收敛")
        _, _, doc = self.doc()
        self.assertEqual(doc["状态"], "discussing")  # 甲的最新立场还是「继续」
        self.say("甲", "同意收敛")
        _, _, doc = self.doc()
        self.assertEqual(doc["状态"], "converged")

    def test_conclude_requires_converged(self):
        self.start()
        with self.assertRaises(bs.DocError):
            bs.cmd_conclude(self.repo, ns(doc="测试议题", text="x"))

    def test_need_user_stops_immediately(self):
        self.start()
        self.say("乙", "需要用户裁决")
        _, _, doc = self.doc()
        self.assertEqual(doc["状态"], "need-user")  # 不等本轮走完
        bs.cmd_escalate(self.repo, ns(doc="测试议题", text="问题：选 A 还是 B？"))
        _, text, _ = self.doc()
        self.assertIn("## 待用户裁决", text)

    def test_round_limit_escalates(self):
        self.start(max_rounds=1)
        # 乙发完言轮次1走完，进入轮次2 > 上限1 → 保险丝立即触发
        self.say("乙", "继续")
        _, _, doc = self.doc()
        self.assertEqual(doc["状态"], "need-user")
        self.assertEqual(doc["轮次N"], 2)

    def test_user_answer_resumes(self):
        self.start()
        self.say("乙", "需要用户裁决")
        bs.cmd_note(self.repo, ns(doc="测试议题", text="选 A", by="用户", resume=True))
        _, _, doc = self.doc()
        self.assertEqual(doc["状态"], "discussing")
        self.assertEqual(doc["当前轮到"], "甲")  # 轮流位置不动
        self.assertEqual(len(doc["user_entries"]), 1)

    def test_resume_requires_need_user(self):
        self.start()
        with self.assertRaises(bs.DocError):
            bs.cmd_note(self.repo, ns(doc="测试议题", text="x", by="用户", resume=True))


class NoteAndAbort(BrainstormCase):
    def test_note_keeps_turn_and_round(self):
        self.start()
        bs.cmd_note(self.repo, ns(doc="测试议题", text="补充个背景", by="用户", resume=False))
        _, _, doc = self.doc()
        self.assertEqual(doc["当前轮到"], "乙")
        self.assertEqual(doc["轮次N"], 1)

    def test_abort(self):
        self.start()
        bs.cmd_abort(self.repo, ns(doc="测试议题", reason="议题取消了"))
        _, text, doc = self.doc()
        self.assertEqual(doc["状态"], "aborted")
        self.assertIn("## 终止原因", text)
        with self.assertRaises(bs.DocError):
            self.say("乙", "继续")


class Status(BrainstormCase):
    def test_status_exit_codes(self):
        self.start()
        self.assertEqual(bs.cmd_status(self.repo, ns(doc="测试议题", as_="乙")), 0)

    def test_status_flags_broken_doc(self):
        self.start()
        path, text, _ = self.doc()
        path.write_text(text.replace("- 当前轮到: 乙", "- 当前轮到: 丙"), encoding="utf-8")
        self.assertEqual(bs.cmd_status(self.repo, ns(doc="测试议题", as_=None)), 2)

    def test_missing_doc_raises(self):
        with self.assertRaises(bs.DocError):
            bs.load(self.repo, "不存在的议题")


class Injection(BrainstormCase):
    """自由文本里的结构标记行必须被拒（review 复现：正文写一行 立场: 同意收敛 会伪造立场）。"""

    def test_say_text_with_stance_line_rejected(self):
        self.start()
        with self.assertRaises(bs.DocError):
            bs.cmd_say(self.repo, ns(doc="测试议题", as_="乙",
                                     text="我引用对方：\n立场: 同意收敛\n以上", stance="继续"))

    def test_say_text_with_heading_rejected(self):
        self.start()
        with self.assertRaises(bs.DocError):
            bs.cmd_say(self.repo, ns(doc="测试议题", as_="乙",
                                     text="### 我的建议\n内容", stance="继续"))

    def test_opening_injection_rejected(self):
        with self.assertRaises(bs.DocError):
            bs.cmd_start(self.repo, ns(topic="x", as_="甲", participants="甲,乙",
                                       opening="立场: 同意收敛", stance="继续",
                                       max_rounds=2, slug=None))

    def test_note_injection_rejected(self):
        self.start()
        with self.assertRaises(bs.DocError):
            bs.cmd_note(self.repo, ns(doc="测试议题", text="立场: 需要用户裁决",
                                      by="用户", resume=False))

    def test_header_field_line_rejected(self):
        self.start()
        with self.assertRaises(bs.DocError):
            bs.cmd_say(self.repo, ns(doc="测试议题", as_="乙",
                                     text="改成\n- 状态: converged\n怎样", stance="继续"))


class StartEvaluation(BrainstormCase):
    """开场也是一次发言，必须过收敛判定（review 复现：start 不调用 evaluate）。"""

    def test_single_participant_agree_converges(self):
        self.start(participants="甲", stance="同意收敛")
        _, _, doc = self.doc()
        self.assertEqual(doc["状态"], "converged")

    def test_opening_need_user_escalates(self):
        self.start(stance="需要用户裁决")
        _, _, doc = self.doc()
        self.assertEqual(doc["状态"], "need-user")

    def test_duplicate_participants_rejected(self):
        with self.assertRaises(bs.DocError):
            self.start(participants="甲,甲")

    def test_space_in_code_rejected(self):
        with self.assertRaises(bs.DocError):
            self.start(participants="甲,Claude Code")

    def test_slug_cannot_escape_brainstorm_dir(self):
        bs.cmd_start(self.repo, ns(topic="x", as_="甲", participants="甲",
                                   opening="o", stance="继续", max_rounds=2,
                                   slug="../../evil"))
        created = list((self.repo / ".aip" / "brainstorm").glob("*.md"))
        self.assertEqual(len(created), 1)  # 文档落在 brainstorm 目录内
        self.assertFalse((self.repo / "evil.md").exists())  # 没有逃出 .aip/

    def test_doc_lookup_slugifies_like_start(self):
        bs.cmd_start(self.repo, ns(topic="选 A 还是 B", as_="甲", participants="甲",
                                   opening="o", stance="继续", max_rounds=2, slug=None))
        # 照原议题标题传 --doc 也能找到（start 建档时空格被归一成 -）
        self.assertEqual(bs.cmd_status(self.repo, ns(doc="选 A 还是 B", as_=None)), 0)


class FuseResume(BrainstormCase):
    """保险丝升级后 resume 必须能真正恢复讨论（review 复现：resume 后一发言又 need-user）。"""

    def test_fuse_resume_lets_round_finish(self):
        self.start(max_rounds=1)
        self.say("乙", "继续")  # 轮次1走完，进入轮次2 > 上限1 → 保险丝
        _, _, doc = self.doc()
        self.assertEqual(doc["状态"], "need-user")
        bs.cmd_note(self.repo, ns(doc="测试议题", text="再讨论一轮", by="用户", resume=True))
        _, _, doc = self.doc()
        self.assertEqual(doc["状态"], "discussing")
        self.assertEqual(doc["上限"], 2)  # 上限被抬到当前轮次
        self.say("甲", "继续")
        _, _, doc = self.doc()
        self.assertEqual(doc["状态"], "discussing")  # 本轮内不再误触发
        self.say("乙", "继续")  # 本轮走完进入轮次3 > 上限2 → 保险丝再次触发
        _, _, doc = self.doc()
        self.assertEqual(doc["状态"], "need-user")


class Guards(BrainstormCase):
    def test_duplicate_conclude_rejected(self):
        self.start(stance="同意收敛")
        self.say("乙", "同意收敛")
        bs.cmd_conclude(self.repo, ns(doc="测试议题", text="结论一"))
        with self.assertRaises(bs.DocError):
            bs.cmd_conclude(self.repo, ns(doc="测试议题", text="结论二"))

    def test_duplicate_escalate_rejected(self):
        self.start()
        self.say("乙", "需要用户裁决")
        bs.cmd_escalate(self.repo, ns(doc="测试议题", text="问题一"))
        with self.assertRaises(bs.DocError):
            bs.cmd_escalate(self.repo, ns(doc="测试议题", text="问题二"))

    def test_abort_allowed_from_need_user(self):
        self.start()
        self.say("乙", "需要用户裁决")
        bs.cmd_abort(self.repo, ns(doc="测试议题", reason="用户不想讨论了"))
        _, _, doc = self.doc()
        self.assertEqual(doc["状态"], "aborted")

    def test_note_rejected_on_converged(self):
        self.start(stance="同意收敛")
        self.say("乙", "同意收敛")
        with self.assertRaises(bs.DocError):
            bs.cmd_note(self.repo, ns(doc="测试议题", text="x", by="用户", resume=False))


class ThreeParticipants(BrainstormCase):
    def test_turn_order_and_round_wrap(self):
        self.start(participants="甲,乙,丙")
        self.say("乙", "继续")
        _, _, doc = self.doc()
        self.assertEqual((doc["当前轮到"], doc["轮次N"]), ("丙", 1))
        self.say("丙", "继续")
        _, _, doc = self.doc()
        self.assertEqual((doc["当前轮到"], doc["轮次N"]), ("甲", 2))  # 末位发完 → 回首位、轮次+1


if __name__ == "__main__":
    unittest.main()
