"""0.9.0：压缩前给写摘要的指示、入口不再强制整篇读技能、旁路问题能结案、Codex 仓库技能归位。"""
import json, subprocess, sys, unittest
from datetime import date, timedelta
from pathlib import Path
from _engine import ENGINE, SCRIPTS
sys.path.insert(0, str(SCRIPTS))
import aip_after_edit as ae, aip_check as chk, aip_discovery as disc, aip_init, aip_item as it
import aip_precompact as pc, aip_subagent as sa
import aip_size as size, aip_upkeep as up, install_hooks as ih
from test_fix081 import make_repo


def track(d: Path, body: str = "- 目标: 把 X 做完\n- 卡在哪: 无\n- 下一步: 接着写 Y\n- 先读: `src/a.py`\n") -> it.Item:
    return it.new_item(d, "track", "在做的线", "active", stamp="20261121-100000", body=body)


class PreCompact(unittest.TestCase):
    def test_instructions_carry_the_track_and_the_must_keeps(self):
        d = make_repo()
        track(d)
        text = pc.instructions(d)
        self.assertIn("接着写 Y", text)                      # 在建线原文
        self.assertIn("还没写回在建线文件", text)              # 没落盘的进展要点明
        self.assertIn("验证命令", text)
        self.assertIn("用户明确提出的要求", text)

    def test_no_track_still_says_what_to_keep(self):
        d = make_repo()
        text = pc.instructions(d)
        self.assertIn("没有在建线", text)
        self.assertIn("验证命令", text)

    def test_output_stays_under_the_hook_limit(self):
        d = make_repo()
        track(d, body="- 目标: " + "很长的目标" * 3000 + "\n")
        text = pc.instructions(d)
        self.assertLessEqual(len(text), pc.OUTPUT_LIMIT)
        self.assertIn("截断", text)

    def test_repo_without_aip_says_nothing(self):
        d = Path(make_repo())
        (d / ".aip" / "config.yaml").unlink()
        r = subprocess.run([sys.executable, str(SCRIPTS / "aip_precompact.py"), "--repo-root", str(d)],
                           capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, ""))


class Hook(unittest.TestCase):
    def commands(self, d: Path, event: str) -> list[str]:
        data = json.loads((d / ".claude" / "settings.json").read_text(encoding="utf-8"))
        return [h["command"] for g in data["hooks"][event] for h in g["hooks"]]

    def test_installs_alongside_session_start_and_is_idempotent(self):
        d = make_repo()
        engine = d / ".claude" / "skills" / "aip"
        ih.install_claude_session_start(d, engine)
        ih.install_claude_pre_compact(d, engine)
        ih.install_claude_pre_compact(d, engine)
        self.assertEqual(len(self.commands(d, "PreCompact")), 1)
        self.assertIn("aip_precompact.py", self.commands(d, "PreCompact")[0])
        self.assertEqual(len(self.commands(d, "SessionStart")), 1)
        self.assertIn("aip_session_start.py", self.commands(d, "SessionStart")[0])

    def test_init_installs_both_claude_hooks(self):
        d = make_repo(git_init=True)
        aip_init.main_argv = None
        sys.argv = ["aip_init.py", "--repo-root", str(d), "--engine-root", str(ENGINE)]
        aip_init.main()
        for event, script in (("SessionStart", "aip_session_start.py"), ("PreCompact", "aip_precompact.py")):
            self.assertTrue(any(script in c for c in self.commands(d, event)), event)


class Entry(unittest.TestCase):
    def test_block_asks_for_the_skill_only_when_aip_work_starts(self):
        b = disc.managed_block()
        self.assertNotIn("再做任何其他事", b)          # 不再要求每个会话先整篇读技能
        self.assertIn("先调 `aip` 技能", b)
        self.assertIn("压缩", b)                       # 压缩后以在建线为准

    def test_skill_body_fits_the_cap_with_room(self):
        body = (ENGINE / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(body), size.SKILL_LIMIT * size.NEAR_RATIO)


class Inbox(unittest.TestCase):
    def test_wontfix_is_a_real_status(self):
        d = make_repo()
        i = it.new_item(d, "inbox", "决定不做的事", stamp="20261101-100000")
        moved = it.set_status(d, i.id, "wontfix")
        self.assertTrue(moved.path.exists())
        self.assertIn("_inbox_wontfix_", moved.path.name)
        self.assertEqual(chk.check_items(d) + chk.check_item_names(d), [])

    def test_old_open_gets_a_reminder_and_wontfix_does_not(self):
        d = make_repo()
        old = (date.today() - timedelta(days=up.INBOX_STALE_DAYS + 10)).strftime("%Y%m%d-%H%M%S")
        it.new_item(d, "inbox", "搁了很久的问题", stamp=old)
        due = [x for x in up.reminders(d, limit=None) if "open 了" in x]
        self.assertEqual(len(due), 1, due)
        self.assertIn("wontfix", due[0])
        it.set_status(d, [i for i in it.list_items(d, "inbox")][0].id, "wontfix")
        self.assertEqual([x for x in up.reminders(d, limit=None) if "open 了" in x], [])

    def test_fresh_open_is_not_nagged(self):
        d = make_repo()
        it.new_item(d, "inbox", "刚记的问题", stamp=date.today().strftime("%Y%m%d-%H%M%S"))
        self.assertEqual([x for x in up.reminders(d, limit=None) if "open 了" in x], [])


class SizeInTokens(unittest.TestCase):
    def test_whole_file_messages_estimate_tokens(self):
        m = size.Measure("x.md", "有", 31000, size.ON_DEMAND_LIMIT, "字", "拆开")
        self.assertIn("token", m.over_text())
        near = size.Measure("x.md", "有", 28000, size.ON_DEMAND_LIMIT, "字", "拆开")
        self.assertIn("token", near.near_text())

    def test_line_and_table_messages_do_not(self):
        line = size.Measure("x.md", "第 3 行有", 1200, size.LINE_LIMIT, "字", "拆句", warn_near=False)
        self.assertNotIn("token", line.over_text())


def hook_out(script: str, payload: dict) -> str:
    r = subprocess.run([sys.executable, str(SCRIPTS / script)], input=json.dumps(payload),
                       capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip()


class AfterEdit(unittest.TestCase):
    """Edit / Write 之后自动反查：原来「改代码前跑 relevant」只能靠自觉。"""

    def repo(self) -> Path:
        d = make_repo()
        (d / "src").mkdir()
        (d / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        it.new_item(d, "knowledge", "这个文件的坑", "active", stamp="20261101-100000",
                    meta={"category": "c", "scope": "s", "paths": "src/a.py"})
        return d

    def payload(self, d: Path, rel: str, session: str = "s1") -> dict:
        return {"session_id": session, "cwd": str(d), "tool_name": "Edit",
                "tool_input": {"file_path": str(d / rel)}}

    def test_emits_nested_additional_context(self):
        d = self.repo()
        out = json.loads(hook_out("aip_after_edit.py", self.payload(d, "src/a.py")))
        spec = out["hookSpecificOutput"]
        self.assertEqual(spec["hookEventName"], "PostToolUse")
        self.assertIn("这个文件的坑", spec["additionalContext"])

    def test_same_file_is_mentioned_once_per_session(self):
        d = self.repo()
        self.assertTrue(hook_out("aip_after_edit.py", self.payload(d, "src/a.py")))
        self.assertEqual(hook_out("aip_after_edit.py", self.payload(d, "src/a.py")), "")
        # 换个会话照提
        self.assertTrue(hook_out("aip_after_edit.py", self.payload(d, "src/a.py", session="s2")))

    def test_quiet_for_aip_files_and_outside_paths(self):
        d = self.repo()
        self.assertEqual(hook_out("aip_after_edit.py", self.payload(d, ".aip/conventions.md")), "")
        out = hook_out("aip_after_edit.py", {"session_id": "s9", "cwd": str(d),
                                             "tool_input": {"file_path": "/tmp/somewhere-else.py"}})
        self.assertEqual(out, "")

    def test_context_is_capped_like_relevant(self):
        d = self.repo()
        for i in range(20):
            it.new_item(d, "knowledge", f"坑 {i}", "active", stamp=f"20261102-1000{i:02d}",
                        meta={"category": "c", "scope": "s", "paths": "src/a.py"})
        text = ae.context_for(d, "src/a.py")
        self.assertIn("还有", text)
        self.assertLess(len(text.splitlines()), 16)


class Subagent(unittest.TestCase):
    def test_hands_the_rules_and_the_track_to_the_subagent(self):
        d = make_repo()
        track(d)
        out = json.loads(hook_out("aip_subagent.py", {"cwd": str(d), "agent_type": "Explore"}))
        spec = out["hookSpecificOutput"]
        self.assertEqual(spec["hookEventName"], "SubagentStart")
        self.assertIn("只有主代理写", spec["additionalContext"])
        self.assertIn("接着写 Y", spec["additionalContext"])

    def test_quiet_without_aip(self):
        d = make_repo()
        (d / ".aip" / "config.yaml").unlink()
        self.assertEqual(hook_out("aip_subagent.py", {"cwd": str(d)}), "")

    def test_context_builder_works_without_tracks(self):
        self.assertIn("只有主代理写", sa.context_for(make_repo()))


class HookMatchers(unittest.TestCase):
    def groups(self, d: Path, event: str) -> list[dict]:
        data = json.loads((d / ".claude" / "settings.json").read_text(encoding="utf-8"))
        return data["hooks"][event]

    def test_edit_hook_is_scoped_to_edit_and_write(self):
        d = make_repo()
        engine = d / ".claude" / "skills" / "aip"
        ih.install_claude_after_edit(d, engine)
        ih.install_claude_subagent(d, engine)
        self.assertEqual(self.groups(d, "PostToolUse")[0]["matcher"], "Edit|Write")
        self.assertEqual(self.groups(d, "SubagentStart")[0]["matcher"], "*")

    def test_init_installs_all_four_claude_hooks(self):
        d = make_repo(git_init=True)
        sys.argv = ["aip_init.py", "--repo-root", str(d), "--engine-root", str(ENGINE)]
        aip_init.main()
        data = json.loads((d / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(data["hooks"]), ["PostToolUse", "PreCompact", "SessionStart", "SubagentStart"])


if __name__ == "__main__":
    unittest.main()
