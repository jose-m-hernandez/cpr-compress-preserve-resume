"""Offline tests for the eval runner and its isolation proof. They never call the real claude.

Run with: python3 -m unittest discover tests
"""

from __future__ import annotations

import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
sys.path.insert(0, str(ROOT / "scripts"))

import claude_run  # noqa: E402
import isolation  # noqa: E402
from cpr_common import project_slug  # noqa: E402

VERSION = "9.9.9"
MODEL = "claude-test-model"
CPR_NAME = "cpr:session_start.py"
MARKER = "this is a synthetic marker line for tests"
CFG = {
    "claude_code_version": VERSION, "model": MODEL, "isolated_baseline_hooks": 0, "isolation": "sources",
    "max_budget_usd_per_run": 0.75, "probe_max_output_tokens": 2048, "probe_timeout_s": 180,
    "phase_caps": {"control": 3.0, "generate": 15.0, "pilot": 30.0},
    "plugin_ref": "cfd1e77e07d2b3698591688e7e151d83d3ef51c3",
    "instructions_attachment_proven": True,
    "init_allowlist": {"skills": ["update-config"], "agents": ["general-purpose"]},
}


SYNTH_HOOKS = {"hooks": {
    "SessionStart": [{"matcher": "startup|clear|compact", "hooks": [{"type": "command", "command": "run start"}]}],
    "PreCompact": [{"hooks": [{"type": "command", "command": "run save"}]}],
}}


def hook(subtype, name, event="SessionStart", exit_code=0, stdout="", hook_id="h1"):
    ev = {"type": "system", "subtype": subtype, "hook_event": event, "hook_name": name, "hook_id": hook_id}
    if subtype == "hook_response":
        ev.update(exit_code=exit_code, stdout=stdout)
    return ev


class RunFixture:
    """Builds a passing run record on disk, then lets a test break one thing."""

    def __init__(self, tmp: Path, resumed=False, kind="plain", with_plugin=True):
        self.tmp = tmp
        self.sandbox = tmp / "sandbox"
        self.sandbox.mkdir()
        self.export = tmp / "export"
        (self.export / "hooks").mkdir(parents=True)
        (self.export / "hooks" / "hooks.json").write_text(json.dumps(SYNTH_HOOKS), encoding="utf-8")
        init = {
            "type": "system", "subtype": "init", "claude_code_version": VERSION, "model": MODEL,
            "plugins": [{"name": "cc-plugin-a", "path": "builtin", "source": "x"}],
            "mcp_servers": [], "skills": ["update-config"], "agents": ["general-purpose"], "tools": ["Read"],
            "memory_paths": {"auto": str(self.sandbox / "mem")}, "session_id": "s",
        }
        events = [init, {"type": "result", "subtype": "success", "is_error": False, "permission_denials": []}]
        if with_plugin:
            init["plugins"].append({"name": "cpr", "path": str(self.export), "source": "cpr@inline"})
            init["skills"].append("cpr:preserve")
            if not resumed:
                events.insert(0, hook("hook_started", CPR_NAME))
                events.insert(1, hook("hook_response", CPR_NAME))
        if kind == "probe":
            init["tools"] = []
        self.events = events
        self.init = init
        self.rows = [{"type": "attachment", "attachment": {"type": "instructions", "files": [
            {"path": str(self.sandbox / "CLAUDE.md"), "type": "Project", "content": "x"}]}}]
        self.run = {"events": events, "sandbox": str(self.sandbox), "session_id": "s", "resumed": resumed,
                    "kind": kind, "plugin": str(self.export) if with_plugin else None, "transcript": None,
                    "config_dir": str(tmp / "cfgdir")}
        self.write_transcript()

    def write_transcript(self):
        path = self.tmp / "t.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in self.rows) + "\n", encoding="utf-8")
        self.run["transcript"] = str(path)

    def check(self, markers=(MARKER,)):
        self.write_transcript()
        return isolation.check(self.run, CFG, list(markers))


class CheckTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.fx = RunFixture(Path(self._tmp.name))

    def assertFails(self, label):
        res = self.fx.check()
        self.assertFalse(res["ok"], res)
        self.assertIn(label, res["failures"])

    def test_good_run_passes(self):
        res = self.fx.check()
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["counts"]["sessionstart_hooks"], 1)
        self.assertEqual(res["counts"]["markers_checked"], 1)

    def test_version_and_model_pins(self):
        self.fx.init["claude_code_version"] = "0.0.1"
        self.assertFails("version_mismatch")
        self.fx.init["claude_code_version"] = VERSION
        self.fx.init["model"] = "other"
        self.assertFails("model_mismatch")

    def test_plugin_missing_wrong_path_and_extra(self):
        self.fx.init["plugins"] = [p for p in self.fx.init["plugins"] if p["name"] != "cpr"]
        self.assertFails("plugin_cpr_count")
        self.fx.init["plugins"].append({"name": "cpr", "path": str(self.fx.tmp / "elsewhere")})
        self.assertFails("plugin_path")
        self.fx.init["plugins"][-1] = {"name": "cpr", "source": "cpr@inline"}
        self.assertTrue(self.fx.check()["ok"])
        self.fx.init["plugins"].append({"name": "user-plugin", "path": "/somewhere"})
        self.assertFails("plugin_not_builtin")

    def test_mcp_servers(self):
        self.fx.init["mcp_servers"] = [{"name": "x"}]
        self.assertFails("mcp_servers")

    def test_skill_agent_allowlist(self):
        self.fx.init["skills"].append("stray-skill")
        self.assertFails("skills_outside_allowlist")
        self.fx.init["skills"].pop()
        self.fx.init["agents"].append("stray-agent")
        self.assertFails("agents_outside_allowlist")
        self.fx.init["agents"].pop()
        self.fx.init["skills"].remove("cpr:preserve")
        self.assertFails("skill_cpr_preserve_missing")

    def test_memory_path_outside_sandbox(self):
        self.fx.init["memory_paths"] = {"auto": str(self.fx.tmp / "config" / "projects" / "mem")}
        self.assertFails("memory_path_outside")

    def test_exact_declared_counts_pass_including_a_declared_precompact_pair(self):
        self.fx.events.insert(0, hook("hook_started", "x", event="PreCompact", hook_id="p1"))
        self.fx.events.insert(1, hook("hook_response", "x", event="PreCompact", hook_id="p1"))
        res = self.fx.check()
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["counts"]["host_hooks"], 0)

    def test_extra_sessionstart_event_fails(self):
        self.fx.events.insert(0, hook("hook_started", "x", hook_id="h2"))
        self.fx.events.insert(1, hook("hook_response", "x", hook_id="h2"))
        res = self.fx.check()
        self.assertIn("host_hook", res["failures"])
        self.assertEqual(res["counts"]["host_hooks"], 2)

    def test_undeclared_hook_event_fails(self):
        self.fx.events.insert(0, hook("hook_started", "x", event="SessionEnd", hook_id="e1"))
        self.fx.events.insert(1, hook("hook_response", "x", event="SessionEnd", hook_id="e1"))
        res = self.fx.check()
        self.assertIn("host_hook", res["failures"])
        self.assertEqual(res["counts"]["host_hooks"], 2)

    def test_missing_hook_pair_fails(self):
        self.fx.events.insert(0, hook("hook_started", "x", event="PreCompact", hook_id="p1"))
        res = self.fx.check()
        self.assertIn("hook_unpaired", res["failures"])
        self.fx.events.pop(0)
        self.fx.events[:] = [e for e in self.fx.events if e.get("subtype") != "hook_started"]
        self.assertIn("hook_unpaired", self.fx.check()["failures"])

    def test_response_with_a_different_hook_id_fails(self):
        for e in self.fx.events:
            if e.get("subtype") == "hook_response":
                e["hook_id"] = "other"
        self.assertIn("hook_unpaired", self.fx.check()["failures"])

    def test_baseline_must_be_recorded_as_zero(self):
        for bad in (None, 1, False):
            with self.subTest(baseline=bad):
                res = isolation.check(self.fx.run, dict(CFG, isolated_baseline_hooks=bad), [MARKER])
                self.assertIn("baseline_unproven", res["failures"])

    def test_declared_counts_parse_events_matcher_groups_and_hooks(self):
        export = self.fx.export
        self.assertEqual(isolation.declared_counts(export), {"SessionStart": 1, "PreCompact": 1})
        self.assertEqual(isolation.declared_counts(export, resumed=True), {"SessionStart": 0, "PreCompact": 1})
        two = {"hooks": {"SessionStart": [{"hooks": [{"command": "a"}, {"command": "b"}]},
                                          {"matcher": "resume", "hooks": [{"command": "c"}]}]}}
        (export / "hooks" / "hooks.json").write_text(json.dumps(two), encoding="utf-8")
        self.assertEqual(isolation.declared_counts(export), {"SessionStart": 2})
        self.assertEqual(isolation.declared_counts(export, resumed=True), {"SessionStart": 3})

    def test_sessionstart_count_startup(self):
        self.fx.events[:] = [e for e in self.fx.events if e.get("subtype") != "hook_response"]
        self.assertFails("sessionstart_count")

    def test_resumed_run_needs_zero_sessionstart(self):
        sub = Path(self._tmp.name) / "resumed"
        sub.mkdir()
        fx = RunFixture(sub, resumed=True)
        self.assertTrue(fx.check()["ok"])
        fx.events.insert(0, hook("hook_started", CPR_NAME))
        fx.events.insert(1, hook("hook_response", CPR_NAME))
        res = fx.check()
        self.assertIn("sessionstart_count", res["failures"])
        self.assertIn("host_hook", res["failures"])

    def test_instructions_type_and_path(self):
        files = self.fx.rows[0]["attachment"]["files"]
        files[0]["type"] = "User"
        res = self.fx.check()
        self.assertIn("instructions_not_project", res["failures"])
        self.assertEqual(res["counts"]["user_files"], 1)
        files[0]["type"] = "Project"
        files[0]["path"] = str(self.fx.tmp / "elsewhere" / "CLAUDE.md")
        self.assertFails("instructions_outside_sandbox")

    def test_marker_found_in_decoded_string_with_escapes(self):
        self.fx.rows.append({"type": "user", "message": {"content": "before\n" + MARKER + '\n"quoted"'}})
        res = self.fx.check()
        self.assertIn("markers_found", res["failures"])
        self.assertEqual(res["counts"]["markers_found"], 1)

    def test_result_error_and_preserve_checks(self):
        self.fx.events[-1]["is_error"] = True
        self.assertFails("result_error")
        self.fx.events[-1]["is_error"] = False
        self.fx.run["kind"] = "preserve"
        self.fx.events.append({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "AskUserQuestion"}]}})
        self.assertFails("ask_user")
        self.fx.events.pop()
        self.fx.events[-1]["permission_denials"] = [{"tool_name": "Bash"}]
        self.assertFails("denials")

    def test_probe_needs_no_tools(self):
        self.fx.run["kind"] = "probe"
        self.assertFails("probe_tools")

    def test_missing_transcript_and_init(self):
        self.fx.run["events"] = [e for e in self.fx.events if e.get("subtype") != "init"]
        self.assertFalse(isolation.check(self.fx.run, CFG, [])["ok"])
        self.fx.run["events"] = self.fx.events
        self.fx.rows.clear()
        self.assertFails("transcript_missing")

    def test_fail_closed_on_missing_init_fields(self):
        for key in ("memory_paths", "skills", "mcp_servers", "agents", "plugins"):
            with self.subTest(key=key):
                saved = self.fx.init.pop(key)
                res = self.fx.check()
                self.assertFalse(res["ok"], res)
                self.assertTrue([f for f in res["failures"] if key in f], res)
                self.fx.init[key] = saved

    def test_fail_closed_with_no_markers(self):
        res = self.fx.check(markers=())
        self.assertIn("no_markers", res["failures"])

    def test_fail_closed_on_none_pins_even_when_both_sides_are_none(self):
        self.fx.init["model"] = None
        res = isolation.check(self.fx.run, dict(CFG, model=None), [MARKER])
        self.assertIn("model_unpinned", res["failures"])
        self.fx.init["model"] = MODEL
        res = isolation.check(self.fx.run, dict(CFG, claude_code_version=None), [MARKER])
        self.assertIn("version_unpinned", res["failures"])

    def test_attachment_required_when_sandbox_has_claude_md(self):
        self.fx.rows[:] = [{"type": "user", "message": {"content": "hi"}}]
        (self.fx.sandbox / "CLAUDE.md").write_text("# x\n", encoding="utf-8")
        self.assertFails("instructions_attachment_missing")
        (self.fx.sandbox / "CLAUDE.md").unlink()
        (self.fx.sandbox / ".claude").mkdir()
        (self.fx.sandbox / ".claude" / "CLAUDE.md").write_text("# x\n", encoding="utf-8")
        self.assertFails("instructions_attachment_missing")

    def test_attachment_may_be_absent_without_claude_md_only_once_proven(self):
        self.fx.rows[:] = [{"type": "user", "message": {"content": "hi"}}]
        self.assertTrue(self.fx.check()["ok"])
        self.fx.write_transcript()
        res = isolation.check(self.fx.run, dict(CFG, instructions_attachment_proven=False), [MARKER])
        self.assertIn("instructions_attachment_missing", res["failures"])
        cfg = {k: v for k, v in CFG.items() if k != "instructions_attachment_proven"}
        self.assertIn("instructions_attachment_missing", isolation.check(self.fx.run, cfg, [MARKER])["failures"])

    def test_memory_path_allows_this_runs_auto_memory_dir_only(self):
        mem = isolation.auto_memory_dir(self.fx.run["config_dir"], self.fx.sandbox)
        self.fx.init["memory_paths"] = {"auto": str(mem) + "/"}
        self.assertTrue(self.fx.check()["ok"])
        other = Path(self.fx.run["config_dir"]) / "projects" / "-some-other-slug" / "memory"
        self.fx.init["memory_paths"] = {"auto": str(other) + "/"}
        self.assertFails("memory_path_outside")
        self.fx.init["memory_paths"] = {"auto": str(mem.parent)}
        self.assertFails("memory_path_outside")

    def test_no_plugin_run_rejects_cpr_and_any_hook(self):
        sub = Path(self._tmp.name) / "noplugin"
        sub.mkdir()
        fx = RunFixture(sub, with_plugin=False)
        self.assertTrue(fx.check()["ok"])
        fx.events.insert(0, hook("hook_started", "anything"))
        self.assertIn("host_hook", fx.check()["failures"])


class HardeningCheckTests(unittest.TestCase):
    """H4 to H7: the proof fails closed."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.fx = RunFixture(Path(self._tmp.name))

    def failures(self, markers=(MARKER,), cfg=None):
        self.fx.write_transcript()
        return isolation.check(self.fx.run, cfg or CFG, list(markers))["failures"]

    # H4
    def test_result_must_exist_be_a_success_and_is_error_must_be_false(self):
        result = self.fx.events[-1]
        for mutate in (lambda r: r.pop("is_error"), lambda r: r.update(is_error=True),
                       lambda r: r.update(is_error=None), lambda r: r.update(subtype="error_max_turns"),
                       lambda r: r.pop("subtype")):
            saved = dict(result)
            mutate(result)
            self.assertIn("result_error", self.failures())
            result.clear()
            result.update(saved)
        self.fx.events.remove(result)
        self.assertIn("result_error", self.failures())

    def test_kind_must_be_in_the_enum(self):
        for bad in (None, "", "other", 3):
            self.fx.run["kind"] = bad
            self.assertIn("kind_invalid", self.failures())
        self.fx.run.pop("kind")
        self.assertIn("kind_invalid", self.failures())
        for good in isolation.VALID_KINDS:
            self.fx.run["kind"] = good
            self.fx.init["tools"] = []
            self.assertNotIn("kind_invalid", self.failures())

    # H5
    def test_sandbox_must_be_present(self):
        for bad in (None, "", "  "):
            self.fx.run["sandbox"] = bad
            self.assertIn("sandbox_missing", self.failures())
        self.fx.run.pop("sandbox")
        self.assertIn("sandbox_missing", self.failures())

    def test_memory_paths_values_must_be_absolute_strings(self):
        sandbox = str(self.fx.sandbox)
        for bad in ({"auto": "relative/dir"}, {"auto": 5}, {"auto": None}, {"auto": ["/abs"]}, {"auto": {"x": "/abs"}},
                    ["~/mem"], "string", None):
            self.fx.init["memory_paths"] = bad
            self.assertIn("memory_paths_invalid", self.failures(), bad)
        for good in ({}, [], {"auto": sandbox + "/mem"}, [sandbox + "/mem"]):
            self.fx.init["memory_paths"] = good
            self.assertNotIn("memory_paths_invalid", self.failures(), good)

    def test_auto_memory_dir_must_not_be_a_symlink(self):
        cfgdir = Path(self.fx.run["config_dir"])
        mem = isolation.auto_memory_dir(cfgdir, self.fx.sandbox)
        mem.parent.mkdir(parents=True)
        target = self.fx.sandbox / "mem"
        target.mkdir()
        mem.symlink_to(target)
        self.fx.init["memory_paths"] = {"auto": str(mem) + "/"}
        self.assertIn("memory_dir_symlink", self.failures())
        mem.unlink()
        mem.mkdir()
        self.assertNotIn("memory_dir_symlink", self.failures())

    # H6
    def test_every_hook_subtype_is_counted_and_undeclared_events_fail(self):
        progress = {"type": "system", "subtype": "hook_progress", "hook_event": "SessionEnd", "hook_id": "z"}
        self.fx.events.insert(0, progress)
        self.assertIn("host_hook", self.failures())
        progress["hook_event"] = "SessionStart"  # declared: progress has no count bound
        self.assertNotIn("host_hook", self.failures())
        names = [e for e in isolation.hook_events(self.fx.events)]
        self.assertIn(progress, names)

    def test_corrupt_transcript_line_fails(self):
        self.fx.write_transcript()
        with open(self.fx.run["transcript"], "a", encoding="utf-8") as fh:
            fh.write("{not json\n")
        res = isolation.check(self.fx.run, CFG, [MARKER])
        self.assertIn("transcript_corrupt", res["failures"])

    def test_transcript_rows_must_carry_this_runs_session_id(self):
        self.fx.rows.append({"type": "user", "sessionId": "s", "message": {"content": "hi"}})
        self.assertNotIn("transcript_session_mismatch", self.failures())
        self.fx.rows.append({"type": "user", "sessionId": "other", "message": {"content": "hi"}})
        self.assertIn("transcript_session_mismatch", self.failures())

    def test_attachment_must_list_exactly_the_sandbox_claude_md_as_project(self):
        md = self.fx.sandbox / "CLAUDE.md"
        md.write_text("# x\n", encoding="utf-8")
        files = self.fx.rows[0]["attachment"]["files"]
        files[:] = [{"path": str(md), "type": "Project"}]
        self.assertTrue(isolation.check(self.fx.run, CFG, [MARKER])["ok"] or "instructions_mismatch" not in self.failures())
        self.assertNotIn("instructions_mismatch", self.failures())
        files.append({"path": str(self.fx.sandbox / "extra.md"), "type": "Project"})
        self.assertIn("instructions_mismatch", self.failures())
        files[:] = [{"path": str(md), "type": "Project"}, {"path": str(md), "type": "Project"}]
        self.assertIn("instructions_mismatch", self.failures())
        files[:] = []
        self.assertIn("instructions_mismatch", self.failures())
        files[:] = [{"path": str(md), "type": "User"}]
        self.assertIn("instructions_not_project", self.failures())

    def test_user_or_local_files_in_any_attachment_type_fail(self):
        self.fx.rows.append({"type": "attachment", "attachment": {"type": "something_else", "files": [
            {"path": "/x", "type": "Local"}]}})
        self.assertIn("user_or_local_files", self.failures())
        self.fx.rows[-1]["attachment"]["files"][0]["type"] = "Other"
        self.assertNotIn("user_or_local_files", self.failures())

    def test_markers_match_after_normalization_and_in_dict_keys(self):
        split = MARKER[:10] + "\u200b" + MARKER[10:]
        self.fx.rows.append({"type": "user", "message": {"content": split}})
        self.assertIn("markers_found", self.failures())
        self.fx.rows[-1] = {"type": "user", MARKER: 1}
        self.assertIn("markers_found", self.failures())
        self.fx.rows[-1] = {"type": "user", "message": {"content": MARKER.replace(" ", "\u00a0")}}
        self.assertIn("markers_found", self.failures())
        self.fx.rows[-1] = {"type": "user", "message": {"content": "unrelated"}}
        self.assertNotIn("markers_found", self.failures())

    # H7
    def test_pins_must_be_non_empty_strings(self):
        for bad in ("", "  ", 5, None, ["x"]):
            res = isolation.check(self.fx.run, dict(CFG, model=bad), [MARKER])
            self.assertIn("model_unpinned", res["failures"], bad)
            res = isolation.check(self.fx.run, dict(CFG, claude_code_version=bad), [MARKER])
            self.assertIn("version_unpinned", res["failures"], bad)

    def test_non_string_skill_agent_and_plugin_entries_fail(self):
        self.fx.init["skills"].append({"name": "update-config"})
        self.assertIn("skills_entry_invalid", self.failures())
        self.fx.init["skills"].pop()
        self.fx.init["agents"].append(7)
        self.assertIn("agents_entry_invalid", self.failures())
        self.fx.init["agents"].pop()
        self.fx.init["plugins"].append("cpr")
        self.assertIn("plugin_entry_invalid", self.failures())

    def test_cpr_names_need_a_plugin_export(self):
        sub = Path(self._tmp.name) / "bare"
        sub.mkdir()
        fx = RunFixture(sub, with_plugin=False)
        fx.init["skills"].append("cpr:preserve")
        fx.write_transcript()
        res = isolation.check(fx.run, CFG, [MARKER])
        self.assertIn("skills_outside_allowlist", res["failures"])

    def test_isolation_mode_must_be_in_the_enum(self):
        for bad in (None, "", "other"):
            self.assertIn("isolation_invalid", self.failures(cfg=dict(CFG, isolation=bad)))
        self.assertNotIn("isolation_invalid", self.failures(cfg=dict(CFG, isolation="tempconfig")))


class PhaseSpendTests(unittest.TestCase):
    """Per-phase spend ledgers and caps."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.environ = {"TMPDIR": str(Path(self._tmp.name).resolve())}

    def test_phases_have_separate_ledgers_and_the_judge_shares_control(self):
        claude_run.add_spend(1.0, self.environ, phase="control")
        claude_run.add_spend(2.0, self.environ, phase="generate")
        claude_run.add_spend(4.0, self.environ, phase="pilot")
        claude_run.add_spend(0.5, self.environ, phase="judge")
        self.assertAlmostEqual(claude_run.spend_total(self.environ, "control"), 1.5)
        self.assertAlmostEqual(claude_run.spend_total(self.environ, "judge"), 1.5)
        self.assertAlmostEqual(claude_run.spend_total(self.environ, "generate"), 2.0)
        self.assertAlmostEqual(claude_run.spend_total(self.environ, "pilot"), 4.0)
        self.assertAlmostEqual(claude_run.spend_total(self.environ), 1.5)

    def test_the_existing_total_is_the_control_ledger(self):
        root = claude_run.eval_root(self.environ)
        root.mkdir(parents=True)
        (root / "spend.json").write_text('{"total": 1.130123}', encoding="utf-8")
        self.assertAlmostEqual(claude_run.spend_total(self.environ, "control"), 1.130123)
        self.assertEqual(claude_run.spend_total(self.environ, "generate"), 0.0)
        claude_run.add_spend(1.0, self.environ, phase="generate")
        self.assertAlmostEqual(claude_run.spend_total(self.environ, "control"), 1.130123)

    def test_caps_come_from_config_and_a_missing_phase_or_cap_refuses(self):
        cfg = dict(CFG)
        self.assertEqual(claude_run.phase_cap(cfg, "control"), 3.0)
        self.assertEqual(claude_run.phase_cap(cfg, "judge"), 3.0)
        self.assertEqual(claude_run.phase_cap(cfg, "generate"), 15.0)
        self.assertEqual(claude_run.phase_cap(cfg, "pilot"), 30.0)
        for bad in ({}, {"control": 3.0}, {"generate": "15"}, {"generate": 0}, {"generate": float("nan")}, {"generate": True}):
            with self.subTest(caps=bad):
                with self.assertRaises(claude_run.ConfigError):
                    claude_run.phase_cap(dict(cfg, phase_caps=bad), "generate")
        for bad_cfg in (dict(cfg, phase_caps=None), {k: v for k, v in cfg.items() if k != "phase_caps"}):
            with self.assertRaises(claude_run.ConfigError):
                claude_run.phase_cap(bad_cfg, "control")
        for phase in (None, "", "other", "Generate"):
            with self.assertRaises(claude_run.ConfigError):
                claude_run.phase_cap(cfg, phase)
            with self.assertRaises(claude_run.ConfigError):
                claude_run.add_spend(1.0, self.environ, phase=phase)

    def test_a_bad_phases_dict_refuses(self):
        root = claude_run.eval_root(self.environ)
        root.mkdir(parents=True)
        for bad in ('{"total": 1, "phases": []}', '{"total": 1, "phases": {"generate": "x"}}',
                    '{"total": 1, "phases": {"generate": -1}}', '{"total": 1, "phases": {"generate": NaN}}'):
            (root / "spend.json").write_text(bad, encoding="utf-8")
            with self.assertRaises(claude_run.SpendError, msg=bad):
                claude_run.spend_total(self.environ, "generate")


class HardeningRunnerTests(unittest.TestCase):
    """H5 resume memory state, H7 and H8 config, spend, ledger and gating."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()

    def test_validate_config_enum_and_budget_range(self):
        claude_run.validate_config(dict(CFG))
        claude_run.validate_config(dict(CFG, max_budget_usd_per_run=5))
        for bad in (0, -1, 5.01, float("nan"), float("inf"), "1", True, None):
            with self.assertRaises(claude_run.ConfigError, msg=repr(bad)):
                claude_run.validate_config(dict(CFG, max_budget_usd_per_run=bad))
        with self.assertRaises(claude_run.ConfigError):
            claude_run.validate_config(dict(CFG, isolation="bogus"))

    def test_validate_config_probe_limits(self):
        for key in ("probe_max_output_tokens", "probe_timeout_s"):
            cfg = dict(CFG)
            del cfg[key]
            with self.assertRaises(claude_run.ConfigError, msg=f"missing {key}"):
                claude_run.validate_config(cfg)
            for bad in (0, -1, 1.5, "10", True, None, float("nan")):
                with self.assertRaises(claude_run.ConfigError, msg=f"{key}={bad!r}"):
                    claude_run.validate_config(dict(CFG, **{key: bad}))
            claude_run.validate_config(dict(CFG, **{key: 1}))

    def test_spend_total_refuses_bad_totals(self):
        environ = {"TMPDIR": str(self.tmp)}
        root = claude_run.eval_root(environ)
        root.mkdir(parents=True)
        for bad in ('{"total": "x"}', '{"total": -1}', '{"total": NaN}', '{"total": Infinity}', '{"total": true}',
                    '{"total": null}', '[]', ''):
            (root / "spend.json").write_text(bad, encoding="utf-8")
            with self.assertRaises(claude_run.SpendError, msg=bad):
                claude_run.spend_total(environ)
        (root / "spend.json").write_text('{"total": 1.5}', encoding="utf-8")
        self.assertEqual(claude_run.spend_total(environ), 1.5)

    def test_add_spend_counts_an_unknown_or_bad_cost_at_the_given_amount(self):
        environ = {"TMPDIR": str(self.tmp)}
        for bad in (None, -1, float("nan"), "x"):
            claude_run.add_spend(bad, environ, unknown_cost=0.75)
        self.assertAlmostEqual(claude_run.spend_total(environ), 3.0)

    def test_ledger_reads_every_regular_file_not_only_jsonl(self):
        d = self.tmp / "ledger"
        d.mkdir()
        (d / "rows.log").write_text("a\n", encoding="utf-8")
        (d / "sub").mkdir()
        before = isolation.ledger_snapshot([d])
        self.assertEqual(list(before.values()), [1])
        (d / "rows.log").write_text("a\nsid-1\n", encoding="utf-8")
        self.assertEqual(isolation.ledger_rows(before, [d], "sid-1"), 1)

    def test_ledger_unreadable_replaced_shrunk_or_vanished_fails(self):
        d = self.tmp / "ledger"
        d.mkdir()
        f = d / "a.jsonl"
        f.write_text("one\ntwo\n", encoding="utf-8")
        before = isolation.ledger_snapshot([d])
        f.write_text("one\n", encoding="utf-8")  # shrank
        with self.assertRaises(isolation.LedgerError) as cm:
            isolation.ledger_rows(before, [d], "x")
        self.assertEqual(str(cm.exception), "ledger_rotated")
        f.unlink()
        f.mkdir()  # replaced by a directory
        with self.assertRaises(isolation.LedgerError) as cm:
            isolation.ledger_rows(before, [d], "x")
        self.assertEqual(str(cm.exception), "ledger_rotated")
        with self.assertRaises(isolation.LedgerError) as cm:
            isolation.ledger_snapshot([self.tmp / "absent"])
        self.assertEqual(str(cm.exception), "ledger_unreadable")

    @unittest.skipIf(os.geteuid() == 0, "root reads everything")
    def test_ledger_file_that_cannot_be_read_fails(self):
        d = self.tmp / "ledger"
        d.mkdir()
        f = d / "a.jsonl"
        f.write_text("one\n", encoding="utf-8")
        f.chmod(0)
        self.addCleanup(f.chmod, 0o644)
        with self.assertRaises(isolation.LedgerError) as cm:
            isolation.ledger_snapshot([d])
        self.assertEqual(str(cm.exception), "ledger_unreadable")


class HelperTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_project_slug_rule_on_a_synthetic_path(self):
        path = Path("/" + "var" + "/folders/ab/c_d1/T/cpr-eval/sandboxes/c3-0a1b2c3d")
        self.assertEqual(project_slug(path), "-var-folders-ab-c-d1-T-cpr-eval-sandboxes-c3-0a1b2c3d")
        self.assertEqual(project_slug(Path("/a/b_c/d.e")), "-a-b-c-d-e")
        mem = isolation.auto_memory_dir("/cfg", self.tmp)
        self.assertEqual(mem.parent.parent, Path("/cfg/projects"))
        self.assertEqual(mem.parent.name, project_slug(Path(os.path.realpath(self.tmp))))

    def test_record_project_dir_appends_to_the_manifest_and_deletes_nothing(self):
        environ = {"TMPDIR": str(self.tmp)}
        sandbox = claude_run.make_sandbox("t", environ)
        cfgdir = self.tmp / "cfgdir"
        slug = project_slug(Path(os.path.realpath(sandbox)))
        (cfgdir / "projects" / slug).mkdir(parents=True)
        claude_run.record_project_dir(cfgdir, sandbox, environ)
        claude_run.record_project_dir(cfgdir, sandbox, environ)
        lines = (claude_run.eval_root(environ) / "project-dirs.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines, [f"{slug}\tprojects/{slug}"] * 2)
        self.assertTrue((cfgdir / "projects" / slug).is_dir())

    def test_markers_take_three_longest_distinct_lines_per_file_and_follow_imports(self):
        cfg_dir = self.tmp / "cfg"
        cfg_dir.mkdir()
        (cfg_dir / "CLAUDE.md").write_text("short\n" + "@" + "AGENTS.md\n" + "\n".join("a" * n for n in (30, 40, 50, 60, 60)) + "\n",
                                           encoding="utf-8")
        (cfg_dir / "AGENTS.md").write_text("b" * 26 + "\n" + "c" * 10 + "\n", encoding="utf-8")
        markers = isolation.host_markers({"CLAUDE_CONFIG_DIR": str(cfg_dir)})
        self.assertEqual(sorted(len(m) for m in markers), [26, 40, 50, 60])

    def test_ledger_counts_new_lines_with_session_id_only(self):
        d = self.tmp / "ledger"
        d.mkdir()
        f = d / "a.jsonl"
        f.write_text('{"session_id": "old-sid"}\n', encoding="utf-8")
        before = isolation.ledger_snapshot([d])
        with open(f, "a", encoding="utf-8") as fh:
            fh.write('{"session_id": "new-sid"}\n{"session_id": "other"}\n')
        (d / "b.jsonl").write_text('{"x": "new-sid"}\n', encoding="utf-8")
        self.assertEqual(isolation.ledger_rows(before, [d], "new-sid"), 2)
        self.assertEqual(isolation.ledger_rows(before, [d], "old-sid"), 0)

    def test_plugin_export_from_pinned_ref(self):
        environ = {"TMPDIR": str(self.tmp)}
        dest = claude_run.export_plugin(claude_run.load_config()["plugin_ref"], environ)
        self.assertTrue((dest / "hooks" / "hooks.json").is_file())
        self.assertEqual(isolation.declared_counts(dest), {"PreCompact": 1, "SessionStart": 1})
        self.assertEqual(isolation.declared_counts(dest, resumed=True), {"PreCompact": 1, "SessionStart": 0})

    def test_child_env_is_an_allowlist(self):
        environ = {"PATH": "/bin", "HOME": "/h", "SECRET_TEST": "x", "TMPDIR": str(self.tmp)}
        env = claude_run.child_env({"isolation": "sources"}, "r1", environ)
        self.assertNotIn("SECRET_TEST", env)
        self.assertIn("CPR_CONFIG", env)
        self.assertFalse(Path(env["CPR_CONFIG"]).exists())
        self.assertNotIn("CLAUDE_CONFIG_DIR", env)
        temp = claude_run.child_env({"isolation": "tempconfig"}, "r1", dict(environ, ANTHROPIC_API_KEY="k", CLAUDE_CODE_OAUTH_TOKEN="t"))
        self.assertIn("CLAUDE_CONFIG_DIR", temp)
        self.assertEqual(sum(v in temp for v in claude_run.AUTH_VARS), 1)

    def test_child_env_carries_max_output_tokens_for_probes_only(self):
        environ = {"PATH": "/bin", "HOME": "/h", "TMPDIR": str(self.tmp)}
        cfg = dict(CFG, probe_max_output_tokens=1234)
        self.assertEqual(claude_run.child_env(cfg, "r1", environ, probe=True)["CLAUDE_CODE_MAX_OUTPUT_TOKENS"], "1234")
        self.assertNotIn("CLAUDE_CODE_MAX_OUTPUT_TOKENS", claude_run.child_env(cfg, "r1", environ))


FAKE = r'''#!/usr/bin/env python3
import json, os, re, sys
here = os.path.dirname(os.path.abspath(__file__))
open(os.path.join(here, "calls.jsonl"), "a").write(json.dumps({"argv": sys.argv[1:], "env": sorted(os.environ), "env_values": {k: v for k, v in os.environ.items() if k.startswith("CLAUDE_CODE_")}, "stdin_tty": sys.stdin.isatty()}) + "\n")
a = sys.argv
if a[2] == "sleep":
    import time; time.sleep(10)
sid = a[a.index("--session-id") + 1] if "--session-id" in a else a[a.index("--resume") + 1]
if "--fork-session" in a:
    import uuid
    sid = str(uuid.uuid4())
slug = re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(os.getcwd()))
d = os.path.join(os.environ["HOME"], ".claude", "projects", slug)
os.makedirs(d, exist_ok=True)
open(os.path.join(d, sid + ".jsonl"), "w").write(json.dumps({"type": "user", "message": {"content": "hi"}}) + "\n")
print(json.dumps({"type": "system", "subtype": "init", "claude_code_version": "9.9.9", "model": "claude-test-model", "session_id": sid}))
print("not json")
print(json.dumps({"type": "rate_limit_event"}))
cost_file = os.path.join(here, "cost.txt")
cost = float(open(cost_file).read()) if os.path.exists(cost_file) else 0.01
print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "total_cost_usd": cost, "duration_ms": 5, "usage": {}, "permission_denials": []}))
'''


class FakeClaudeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        fake = self.bin / "claude"
        fake.write_text(FAKE, encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.environ = {"PATH": str(self.bin) + os.pathsep + os.environ["PATH"], "HOME": str(self.home),
                        "TMPDIR": str(self.tmp), "SECRET_TEST": "x", "CPR_EVAL_LIVE": "1"}

    def calls(self):
        return [json.loads(ln) for ln in (self.bin / "calls.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_run_claude_builds_the_spec_command_and_records_the_run(self):
        sandbox = claude_run.make_sandbox("t", self.environ)
        export = self.tmp / "export"
        export.mkdir()
        cfg = dict(CFG)
        rec = claude_run.run_claude(cfg, "hello", sandbox, label="t", phase="control", plugin=export, environ=self.environ)
        argv = self.calls()[0]["argv"]
        for flag in ("--output-format", "--include-hook-events", "--setting-sources", "--plugin-dir", "--model",
                     "--permission-mode", "--permission-prompts", "--max-budget-usd", "--session-id"):
            self.assertIn(flag, argv)
        self.assertEqual(argv[argv.index("--setting-sources") + 1], "project")
        self.assertEqual(argv[argv.index("--max-budget-usd") + 1], "0.75")
        self.assertNotIn("--no-session-persistence", argv)
        self.assertNotIn("--tools", argv)
        self.assertNotIn("SECRET_TEST", self.calls()[0]["env"])
        self.assertFalse(self.calls()[0]["stdin_tty"])
        self.assertEqual(rec["rate_limit_events"], 1)
        self.assertEqual(rec["cost_usd"], 0.01)
        self.assertTrue(rec["transcript"])
        self.assertEqual(Path(rec["transcript"]).name, rec["session_id"] + ".jsonl")
        self.assertEqual(Path(rec["transcript"]).parent.name, project_slug(Path(os.path.realpath(sandbox))))
        self.assertAlmostEqual(claude_run.spend_total(self.environ), 0.01)

    def test_c1_argv_pins_sonnet_but_stays_plain(self):
        argv = claude_run.build_argv(dict(CFG), "p", session_id="x", plain=True, model="sonnet")
        self.assertEqual(argv[argv.index("--model") + 1], "sonnet")
        self.assertNotIn("--setting-sources", argv)
        self.assertNotIn("--plugin-dir", argv)
        later = claude_run.build_argv(dict(CFG), "p", session_id="x", plugin="/e")
        self.assertEqual(later[later.index("--model") + 1], MODEL)

    def test_strict_mcp_config_on_every_isolated_run_but_not_plain(self):
        cases = {
            "c3": dict(session_id="x"),
            "c2": dict(session_id="x", plugin="/e"),
            "c4": dict(session_id="x", plugin="/e"),
            "c5 turn 1": dict(session_id="x", plugin="/e"),
            "c5 turn 2": dict(resume="x", plugin="/e", kind="preserve"),
            "probe": dict(session_id="x", probe=True),
        }
        for name, kw in cases.items():
            with self.subTest(run=name):
                kw.pop("kind", None)
                argv = claude_run.build_argv(dict(CFG), "p", **kw)
                self.assertIn("--strict-mcp-config", argv)
                self.assertNotIn("--mcp-config", argv)
        plain = claude_run.build_argv(dict(CFG), "p", session_id="x", plain=True, model="sonnet")
        self.assertNotIn("--strict-mcp-config", plain)
        self.assertNotIn("--mcp-config", plain)

    def test_plain_probe_and_resume_flags(self):
        sandbox = claude_run.make_sandbox("t", self.environ)
        claude_run.run_claude(dict(CFG), "p", sandbox, label="t", phase="control", plain=True, environ=self.environ)
        plain = self.calls()[-1]["argv"]
        for flag in ("--setting-sources", "--plugin-dir", "--model"):
            self.assertNotIn(flag, plain)
        prior = {"session_id": "abc", "sandbox": str(sandbox), "memory_dir_after": []}
        claude_run.run_claude(dict(CFG), "p", sandbox, label="t", phase="control", probe=True, resume="abc", environ=self.environ,
                              prior=prior)
        argv = self.calls()[-1]["argv"]
        self.assertEqual(argv[argv.index("--resume") + 1], "abc")
        self.assertNotIn("--session-id", argv)
        self.assertEqual(argv[argv.index("--tools") + 1], "")

    def test_control_refuses_without_live_flag_and_never_spawns_claude(self):
        env = dict(os.environ, PATH=self.environ["PATH"])
        env.pop("CPR_EVAL_LIVE", None)
        proc = subprocess.run([sys.executable, str(ROOT / "evals" / "run.py"), "control"], capture_output=True,
                              text=True, encoding="utf-8", env=env)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("live run refused: set CPR_EVAL_LIVE=1", proc.stdout)
        self.assertFalse((self.bin / "calls.jsonl").exists())

    def test_control_without_ledger_config_exits_3(self):
        env = dict(os.environ, PATH=self.environ["PATH"], CPR_EVAL_LIVE="1")
        env.pop("CPR_EVAL_HOST_LEDGERS", None)
        proc = subprocess.run([sys.executable, str(ROOT / "evals" / "run.py"), "control"], capture_output=True,
                              text=True, encoding="utf-8", env=env)
        self.assertEqual(proc.returncode, 3)
        self.assertIn("ledger not configured", proc.stdout)
        self.assertFalse((self.bin / "calls.jsonl").exists())

    def test_nonempty_auto_memory_dir_refuses_the_launch(self):
        sandbox = claude_run.make_sandbox("t", self.environ)
        mem = isolation.auto_memory_dir(self.home / ".claude", sandbox)
        mem.mkdir(parents=True)
        (mem / "note.md").write_text("x", encoding="utf-8")
        with self.assertRaises(claude_run.MemoryDirError):
            claude_run.run_claude(dict(CFG), "hello", sandbox, label="t", phase="control", environ=self.environ)
        self.assertFalse((self.bin / "calls.jsonl").exists())
        (mem / "note.md").unlink()
        rec = claude_run.run_claude(dict(CFG), "hello", sandbox, label="t", phase="control", environ=self.environ)
        self.assertEqual(rec["memory_dir_at_start"], "empty")
        self.assertEqual(rec["config_dir"], str(self.home / ".claude"))
        manifest = (claude_run.eval_root(self.environ) / "project-dirs.txt").read_text(encoding="utf-8")
        self.assertEqual(manifest.count("\n"), 1)

    def test_timeout_counts_the_full_cap_as_spent(self):
        sandbox = claude_run.make_sandbox("t", self.environ)
        old = claude_run.RUN_TIMEOUT
        claude_run.RUN_TIMEOUT = 1
        self.addCleanup(setattr, claude_run, "RUN_TIMEOUT", old)
        rec = claude_run.run_claude(dict(CFG), "sleep", sandbox, label="t", phase="control", environ=self.environ)
        self.assertTrue(rec["timed_out"])
        self.assertAlmostEqual(claude_run.spend_total(self.environ), 0.75)

    def test_probe_run_gets_output_cap_env_and_probe_timeout(self):
        sandbox = claude_run.make_sandbox("t", self.environ)
        cfg = dict(CFG, probe_max_output_tokens=777, probe_timeout_s=1)
        claude_run.run_claude(cfg, "hello", sandbox, label="t", phase="control", probe=True, environ=self.environ)
        self.assertIn("CLAUDE_CODE_MAX_OUTPUT_TOKENS", self.calls()[-1]["env"])
        self.assertEqual(self.calls()[-1]["env_values"]["CLAUDE_CODE_MAX_OUTPUT_TOKENS"], "777")
        # the probe timeout (1 s), not RUN_TIMEOUT (900 s), ends a slow probe and charges the whole cap
        started = time.time()
        rec = claude_run.run_claude(cfg, "sleep", sandbox, label="t", phase="control", probe=True, environ=self.environ)
        self.assertLess(time.time() - started, 8)
        self.assertTrue(rec["timed_out"])
        self.assertAlmostEqual(claude_run.spend_total(self.environ), 0.01 + 0.75)

    def test_non_probe_run_has_neither_probe_env_nor_probe_timeout(self):
        sandbox = claude_run.make_sandbox("t", self.environ)
        cfg = dict(CFG, probe_timeout_s=1)
        rec = claude_run.run_claude(cfg, "hello", sandbox, label="t", phase="control", environ=self.environ)
        self.assertNotIn("CLAUDE_CODE_MAX_OUTPUT_TOKENS", self.calls()[-1]["env"])
        self.assertNotIn("CLAUDE_CODE_MAX_OUTPUT_TOKENS", rec["env_names"])
        old = claude_run.RUN_TIMEOUT
        claude_run.RUN_TIMEOUT = 2
        self.addCleanup(setattr, claude_run, "RUN_TIMEOUT", old)
        started = time.time()
        claude_run.run_claude(cfg, "sleep", sandbox, label="t", phase="control", environ=self.environ)
        self.assertGreaterEqual(time.time() - started, 1.9)  # RUN_TIMEOUT applied, not probe_timeout_s=1

    def test_spend_file_missing_is_zero_unreadable_refuses(self):
        self.assertEqual(claude_run.spend_total(self.environ), 0.0)
        root = claude_run.eval_root(self.environ)
        root.mkdir(parents=True)
        (root / "spend.json").write_text("not json", encoding="utf-8")
        with self.assertRaises(claude_run.SpendError):
            claude_run.spend_total(self.environ)
        (root / "spend.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(claude_run.SpendError):
            claude_run.spend_total(self.environ)

    def test_preflight_version_mismatch_fails(self):
        (self.bin / "claude").write_text("#!/bin/sh\necho '0.0.1 (Claude Code)'\n", encoding="utf-8")
        reason = claude_run.preflight(dict(CFG), self.environ)
        self.assertEqual(reason, "claude version does not match the pin")


    def launch(self, **over):
        sandbox = claude_run.make_sandbox("t", self.environ)
        over.setdefault("phase", "control")
        return claude_run.run_claude(dict(CFG, **over.pop("cfg", {})), "hello", sandbox, label="t", environ=self.environ, **over), sandbox

    def test_launch_refused_without_live_flag(self):
        self.environ.pop("CPR_EVAL_LIVE")
        with self.assertRaises(claude_run.LiveRefused):
            self.launch()
        self.assertFalse((self.bin / "calls.jsonl").exists())

    def test_resume_launch_is_gated_too(self):
        self.environ["CPR_EVAL_LIVE"] = "0"
        sandbox = claude_run.make_sandbox("t", self.environ)
        with self.assertRaises(claude_run.LiveRefused):
            claude_run.run_claude(dict(CFG), "p", sandbox, label="t", phase="control", resume="abc", environ=self.environ,
                                  prior={"session_id": "abc", "sandbox": str(sandbox), "memory_dir_after": []})
        self.assertFalse((self.bin / "calls.jsonl").exists())

    def test_launch_refused_at_the_spend_cap(self):
        claude_run.add_spend(3.0, self.environ)
        with self.assertRaises(claude_run.SpendCapReached):
            self.launch()
        self.assertFalse((self.bin / "calls.jsonl").exists())

    def test_the_cap_is_per_phase(self):
        claude_run.add_spend(3.0, self.environ, phase="control")
        rec, _ = self.launch(phase="generate")
        self.assertEqual(rec["phase"], "generate")
        self.assertAlmostEqual(claude_run.spend_total(self.environ, "generate"), 0.01)
        claude_run.add_spend(15.0, self.environ, phase="generate")
        with self.assertRaises(claude_run.SpendCapReached):
            self.launch(phase="generate")
        with self.assertRaises(claude_run.SpendCapReached):
            self.launch(phase="judge")  # judge shares the exhausted control budget

    def test_a_launch_must_name_a_known_phase_with_a_cap(self):
        sandbox = claude_run.make_sandbox("t", self.environ)
        with self.assertRaises(TypeError):
            claude_run.run_claude(dict(CFG), "p", sandbox, label="t", environ=self.environ)
        for phase, cfg in (("bogus", {}), ("pilot", {"phase_caps": {"control": 3.0}})):
            with self.assertRaises(claude_run.ConfigError):
                claude_run.run_claude(dict(CFG, **cfg), "p", sandbox, label="t", phase=phase, environ=self.environ)
        self.assertFalse((self.bin / "calls.jsonl").exists())

    def test_allowed_tools_and_fork_session_reach_the_command(self):
        sandbox = claude_run.make_sandbox("t", self.environ)
        sid = "00000000-0000-4000-8000-000000000001"
        prior = {"session_id": sid, "sandbox": str(sandbox), "memory_dir_after": []}
        rec = claude_run.run_claude(dict(CFG), "q", sandbox, label="t", phase="generate", probe=True, resume=sid,
                                    fork_session=True, prior=prior, extra_session_ids=(sid,), environ=self.environ,
                                    allowed_tools=claude_run.bash_tools(["python3 *", "git *"]))
        argv = self.calls()[-1]["argv"]
        self.assertIn("--fork-session", argv)
        self.assertEqual(argv[argv.index("--tools") + 1], "")
        self.assertEqual(argv[argv.index("--allowedTools") + 1], "Bash(python3 *),Bash(git *)")
        self.assertNotEqual(rec["session_id"], sid)
        self.assertEqual(sorted(rec["session_ids"]), sorted([rec["session_id"], sid]))
        self.assertEqual(Path(rec["transcript"]).name, rec["session_id"] + ".jsonl")

    def test_launch_refused_for_a_bad_budget_or_isolation(self):
        for cfg in ({"max_budget_usd_per_run": 6}, {"isolation": "x"}):
            with self.assertRaises(claude_run.ConfigError):
                self.launch(cfg=cfg)
        self.assertFalse((self.bin / "calls.jsonl").exists())

    def test_resume_needs_the_turn_1_record_and_an_unchanged_memory_dir(self):
        rec, sandbox = self.launch()
        sid = rec["session_id"]
        with self.assertRaises(claude_run.MemoryDirError):
            claude_run.run_claude(dict(CFG), "p", sandbox, label="t", phase="control", resume=sid, environ=self.environ)
        mem = isolation.auto_memory_dir(self.home / ".claude", sandbox)
        mem.mkdir(parents=True)
        (mem / "note.md").write_text("changed", encoding="utf-8")
        with self.assertRaises(claude_run.MemoryDirError):
            claude_run.run_claude(dict(CFG), "p", sandbox, label="t", phase="control", resume=sid, environ=self.environ, prior=rec)
        self.assertEqual(len(self.calls()), 1)
        rec2 = claude_run.run_claude(dict(CFG), "p", sandbox, label="t", phase="control", resume=sid, environ=self.environ,
                                     prior=dict(rec, memory_dir_after=claude_run.memory_listing(self.home / ".claude", sandbox)))
        self.assertTrue(rec2["resumed"])

    def set_cost(self, value):
        (self.bin / "cost.txt").write_text(str(value), encoding="utf-8")

    def resume_chain(self, reported, **over):
        """Run turn 1 and then one --resume turn per further reported total; return the records."""
        sandbox = claude_run.make_sandbox("t", self.environ)
        sid = "00000000-0000-4000-8000-0000000000aa"
        recs, prior = [], None
        for n, value in enumerate(reported):
            self.set_cost(value)
            kw = dict(resume=sid, prior=prior, **over) if n else dict(session_id=sid)
            prior = claude_run.run_claude(dict(CFG), "p", sandbox, label="t", phase="generate", environ=self.environ, **kw)
            recs.append(prior)
        return recs

    def test_resumed_turns_charge_the_delta_of_the_cumulative_cost(self):
        recs = self.resume_chain([0.03, 0.05, 0.09])
        self.assertEqual([r["cost_usd_reported"] for r in recs], [0.03, 0.05, 0.09])
        self.assertEqual([r["cost_usd"] for r in recs], [0.03, 0.02, 0.04])
        self.assertAlmostEqual(claude_run.spend_total(self.environ, "generate"), 0.09)

    def test_a_negative_delta_charges_the_full_reported_value(self):
        recs = self.resume_chain([0.05, 0.03])
        self.assertEqual(recs[1]["cost_usd"], 0.03)
        self.assertAlmostEqual(claude_run.spend_total(self.environ, "generate"), 0.08)

    def test_a_missing_or_bad_prior_cost_charges_the_full_reported_value(self):
        self.assertEqual(claude_run.invocation_cost(0.07, None, resumed=True), 0.07)
        for bad in (None, -1, float("nan"), float("inf"), True, "0.1"):
            self.assertEqual(claude_run.invocation_cost(0.07, {"cost_usd_reported": bad}, resumed=True), 0.07)
            self.assertEqual(claude_run.invocation_cost(0.07, {"cost_usd": bad}, resumed=True), 0.07)
        self.assertAlmostEqual(claude_run.invocation_cost(0.07, {"cost_usd": 0.02}, resumed=True), 0.05)  # old record
        sandbox = claude_run.make_sandbox("t", self.environ)
        sid = "00000000-0000-4000-8000-0000000000ab"
        self.set_cost(0.07)
        prior = {"session_id": sid, "sandbox": str(sandbox), "memory_dir_after": []}
        rec = claude_run.run_claude(dict(CFG), "p", sandbox, label="t", phase="generate", resume=sid, prior=prior,
                                    environ=self.environ)
        self.assertEqual(rec["cost_usd"], 0.07)

    def test_a_fork_charges_the_full_reported_value(self):
        sandbox = claude_run.make_sandbox("t", self.environ)
        sid = "00000000-0000-4000-8000-0000000000ac"
        self.set_cost(0.07)
        prior = {"session_id": sid, "sandbox": str(sandbox), "memory_dir_after": [], "cost_usd_reported": 0.05}
        rec = claude_run.run_claude(dict(CFG), "p", sandbox, label="t", phase="generate", resume=sid, prior=prior,
                                    fork_session=True, environ=self.environ)
        self.assertEqual(rec["cost_usd"], 0.07)
        self.assertEqual(rec["cost_usd_reported"], 0.07)
        self.assertAlmostEqual(claude_run.spend_total(self.environ, "generate"), 0.07)

    def test_a_timeout_charges_the_cap_and_keeps_no_reported_cost(self):
        sandbox = claude_run.make_sandbox("t", self.environ)
        old = claude_run.RUN_TIMEOUT
        claude_run.RUN_TIMEOUT = 1
        self.addCleanup(setattr, claude_run, "RUN_TIMEOUT", old)
        rec = claude_run.run_claude(dict(CFG), "sleep", sandbox, label="t", phase="generate", environ=self.environ)
        self.assertIsNone(rec["cost_usd_reported"])
        self.assertAlmostEqual(claude_run.spend_total(self.environ, "generate"), 0.75)



def write_record(root: Path, name, session_id, phase, resumed, reported, mtime, **extra):
    d = root / "runs" / name
    d.mkdir(parents=True)
    rec = dict({"run_id": name, "session_id": session_id, "phase": phase, "resumed": resumed, "cost_usd": reported}, **extra)
    path = d / "record.json"
    path.write_text(json.dumps(rec), encoding="utf-8")
    os.utime(path, (mtime, mtime))
    return path


class SpendRebuildTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.environ = {"TMPDIR": str(self.tmp)}
        self.root = claude_run.eval_root(self.environ)
        self.root.mkdir(parents=True)
        (self.root / "spend.json").write_text(json.dumps({"total": 0.5, "phases": {"generate": 0.7}}), encoding="utf-8")
        # generate: one 3-turn session (old-style records hold the cumulative value), one fork alone in its session
        write_record(self.root, "g1", "s1", "generate", False, 0.03, 1)
        write_record(self.root, "g2", "s1", "generate", True, 0.05, 2)
        write_record(self.root, "g3", "s1", "generate", True, 0.09, 3, cost_usd_reported=0.09)
        write_record(self.root, "f1", "s2", "generate", True, 0.04, 4)
        write_record(self.root, "c1", "s3", "control", False, 0.02, 5)
        write_record(self.root, "j1", "s3", "judge", True, 0.01, 6)  # judge shares the control ledger

    def rebuild(self, **kw):
        out = io.StringIO()
        code = claude_run.spend_rebuild(self.environ, out=out, cfg=dict(CFG), **kw)
        return code, out.getvalue()

    def spend(self):
        return json.loads((self.root / "spend.json").read_text(encoding="utf-8"))

    def test_dry_run_prints_old_and_new_and_writes_nothing(self):
        before = (self.root / "spend.json").read_bytes()
        code, text = self.rebuild()
        self.assertEqual(code, 0)
        self.assertEqual((self.root / "spend.json").read_bytes(), before)
        self.assertIn("generate", text)
        self.assertIn("old   0.700000  new   0.130000", text)

    def test_write_produces_the_per_invocation_totals(self):
        code, _ = self.rebuild(write=True)
        self.assertEqual(code, 0)
        data = self.spend()
        # s1: 0.03 + 0.02 + 0.04, fork: 0.04 in full; control: 0.02 + judge turn 0.01 minus 0.02 is negative -> full 0.01
        self.assertAlmostEqual(data["phases"]["generate"], 0.13)
        self.assertAlmostEqual(data["total"], 0.03)
        self.assertEqual(data["phases"]["pilot"], 0.0)
        self.assertAlmostEqual(claude_run.spend_total(self.environ, "generate"), 0.13)

    def test_an_unreadable_record_refuses_and_writes_nothing(self):
        (self.root / "runs" / "g2" / "record.json").write_text("not json", encoding="utf-8")
        before = (self.root / "spend.json").read_bytes()
        for write in (False, True):
            code, text = self.rebuild(write=write)
            self.assertEqual(code, 1)
            self.assertIn("REFUSED", text)
        self.assertEqual((self.root / "spend.json").read_bytes(), before)

    def test_a_record_with_an_unknown_phase_refuses(self):
        write_record(self.root, "x1", "s9", "bogus", False, 0.01, 7)
        self.assertEqual(self.rebuild()[0], 1)

    def test_a_record_with_no_phase_key_counts_toward_control(self):
        d = self.root / "runs" / "old1"
        d.mkdir()
        (d / "record.json").write_text(json.dumps({"session_id": "s7", "resumed": False, "cost_usd": 0.1}), encoding="utf-8")
        self.rebuild(write=True)
        self.assertAlmostEqual(self.spend()["total"], 0.13)

    def test_a_timed_out_record_counts_as_the_cap(self):
        write_record(self.root, "t1", "s8", "pilot", False, None, 8, timed_out=True)
        self.rebuild(write=True)
        self.assertAlmostEqual(self.spend()["phases"]["pilot"], 0.75)

    def test_the_cli_has_the_subcommand(self):
        sys.path.insert(0, str(Path(claude_run.__file__).resolve().parent))
        import run
        calls = []
        orig = claude_run.spend_rebuild
        claude_run.spend_rebuild = lambda **kw: calls.append(kw) or 0
        self.addCleanup(setattr, claude_run, "spend_rebuild", orig)
        self.assertEqual(run.main(["spend-rebuild"]), 0)
        self.assertEqual(run.main(["spend-rebuild", "--write"]), 0)
        self.assertEqual(calls, [{"write": False}, {"write": True}])


CONTROL_MARKER = "a synthetic host marker line for control tests"


class ScriptedRunner:
    """Stands in for run_claude: builds records from synthetic events, no subprocess."""

    def __init__(self, tmp: Path, ledger: Path, c1_fires=True, cost=0.1, bare=(), c1_mcp=2, ledger_labels=()):
        self.c1_mcp, self.ledger_labels = c1_mcp, set(ledger_labels)
        self.tmp, self.ledger, self.c1_fires, self.cost, self.bare = tmp, ledger, c1_fires, cost, set(bare)
        self.config_dir = tmp / "home" / ".claude"
        self.calls = []
        self.kwargs = {}

    def __call__(self, cfg, prompt, sandbox, *, label, kind="plain", session_id=None, resume=None,
                 plugin=None, plain=False, probe=False, model=None, environ=None, prior=None, phase=None):
        self.calls.append(label)
        self.kwargs[label] = {"plain": plain, "model": model, "plugin": plugin}
        sid = resume or session_id
        c1 = label == "c1"
        init = {"type": "system", "subtype": "init", "claude_code_version": cfg["claude_code_version"],
                "model": "claude-sonnet-test" if c1 else cfg["model"],
                "plugins": [{"name": "cc-plugin-a", "path": "builtin"}], "mcp_servers": [],
                "skills": ["update-config"], "agents": ["general-purpose"], "tools": ["Read"],
                "memory_paths": {"auto": str(isolation.auto_memory_dir(self.config_dir, sandbox)) + "/"}}
        events = []
        if c1:
            init["mcp_servers"] = [{"name": f"connector-{i}", "status": "pending"} for i in range(self.c1_mcp)]
        if plugin:
            init["plugins"].append({"name": "cpr", "path": str(plugin)})
            init["skills"].append("cpr:preserve")
        if label in self.ledger_labels:
            with open(self.ledger / "a.jsonl", "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"session_id": sid}) + "\n")
        if c1 and self.c1_fires:
            events += [hook("hook_started", "host-hook", hook_id="x1"), hook("hook_response", "host-hook", hook_id="x1")]
            with open(self.ledger / "a.jsonl", "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"session_id": sid}) + "\n")
        elif plugin and not resume:
            out = 'topic "hook canary"' if label == "c4" else ""
            hid = "id-" + label
            events += [hook("hook_started", CPR_NAME, hook_id=hid), hook("hook_response", CPR_NAME, stdout=out, hook_id=hid)]
        events += [init, {"type": "result", "subtype": "success", "is_error": False, "permission_denials": [],
                          "total_cost_usd": self.cost}]
        files = [{"path": str(sandbox / "CLAUDE.md"), "type": "Project"}]
        rows = [{"type": "attachment", "attachment": {"type": "instructions", "files": files}}]
        if c1 and self.c1_fires:
            files[:] = [{"path": "/elsewhere/CLAUDE.md", "type": "User"}]
            rows.append({"type": "user", "message": {"content": CONTROL_MARKER}})
        if label == "c5b":
            with open(sandbox / "CLAUDE.md", "a", encoding="utf-8") as fh:
                fh.write("- Dev server on 8081.\n")
        if label in self.bare:
            rows = [{"type": "user", "message": {"content": "hi"}}]
        pdir = self.config_dir / "projects" / project_slug(Path(os.path.realpath(sandbox)))
        (pdir / "memory").mkdir(parents=True, exist_ok=True)
        tpath = self.tmp / f"{label}.jsonl"
        tpath.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        claude_run.add_spend(self.cost, environ)
        return {"events": events, "session_id": sid, "resumed": bool(resume), "kind": kind, "sandbox": str(sandbox),
                "plugin": str(plugin) if plugin else None, "transcript": str(tpath),
                "config_dir": str(self.config_dir)}


class ControlTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        exe = bin_dir / "claude"
        exe.write_text("#!/bin/sh\necho '2.1.302 (Claude Code)'\n", encoding="utf-8")
        exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
        home = self.tmp / "home"
        (home / ".claude").mkdir(parents=True)
        (home / ".claude" / "CLAUDE.md").write_text("# Title\n" + CONTROL_MARKER + "\n", encoding="utf-8")
        self.ledger = self.tmp / "ledger"
        self.ledger.mkdir()
        self.environ = {"PATH": str(bin_dir) + os.pathsep + os.environ["PATH"], "HOME": str(home),
                        "TMPDIR": str(self.tmp), "CPR_EVAL_LIVE": "1", "CPR_EVAL_HOST_LEDGERS": str(self.ledger)}
        self.config = self.tmp / "config.json"
        self.write_config()
        old = claude_run.POLL_SECONDS
        claude_run.POLL_SECONDS = 0
        self.addCleanup(setattr, claude_run, "POLL_SECONDS", old)

    def write_config(self, **over):
        cfg = claude_run.load_config()
        cfg["phase_caps"] = {"control": 3.0, "generate": 15.0, "pilot": 30.0}  # not the committed values
        cfg.update(over)
        claude_run.save_config(cfg, self.config)

    def run_control(self, runner, environ=None):
        out = io.StringIO()
        code = claude_run.control(environ or self.environ, out, runner, self.config)
        return code, out.getvalue()

    def test_happy_path_runs_all_five_and_writes_pins(self):
        runner = ScriptedRunner(self.tmp, self.ledger)
        code, out = self.run_control(runner)
        self.assertEqual(code, 0, out)
        self.assertEqual(runner.calls, ["c1", "c3", "c2", "c4", "c5a", "c5b"])
        self.assertIn("control: PASS (5/5)", out)
        self.assertIn("c3_overlap=not-applicable", out)
        self.assertEqual(runner.kwargs["c1"], {"plain": True, "model": "sonnet", "plugin": None})
        self.assertEqual(runner.kwargs["c3"]["model"], None)  # later runs take the pinned ID from cfg
        self.assertIn("-> FIRES (expected)", out)
        self.assertIn("mcp=2", out)
        saved = json.loads(self.config.read_text(encoding="utf-8"))
        self.assertEqual(saved["isolated_baseline_hooks"], 0)
        self.assertNotIn("hook_id_field", saved)
        self.assertIn("hook_attribution=count", out)
        self.assertEqual(saved["model"], "claude-sonnet-test")
        self.assertEqual(saved["init_allowlist"]["skills"], ["update-config"])

    def test_bare_sandboxes_pass_once_c1_proved_the_attachment_and_nothing_is_deleted(self):
        runner = ScriptedRunner(self.tmp, self.ledger, bare=("c3", "c2", "c4"))
        code, out = self.run_control(runner)
        self.assertEqual(code, 0, out)
        self.assertTrue(json.loads(self.config.read_text(encoding="utf-8"))["instructions_attachment_proven"])
        # c1, c3, c2, c4 and one shared c5 sandbox: five project dirs, every one still there.
        self.assertEqual(len(list((runner.config_dir / "projects").iterdir())), 5)

    def test_c1_without_connectors_stops_with_mcp_instrument_message(self):
        runner = ScriptedRunner(self.tmp, self.ledger, c1_mcp=0)
        code, out = self.run_control(runner)
        self.assertEqual(code, 1)
        self.assertEqual(runner.calls, ["c1"])
        self.assertIn("mcp=0", out)
        self.assertIn("control: STOP mcp instrument cannot fire", out)

    def test_dead_c1_stops_before_c3_and_c2(self):
        runner = ScriptedRunner(self.tmp, self.ledger, c1_fires=False)
        code, out = self.run_control(runner)
        self.assertEqual(code, 1)
        self.assertEqual(runner.calls, ["c1"])
        self.assertIn("control: STOP C1 did not fire", out)

    def test_spend_cap_stops_the_control(self):
        self.write_config(phase_caps={"control": 0.4, "generate": 15.0, "pilot": 30.0})
        runner = ScriptedRunner(self.tmp, self.ledger, cost=0.5)
        code, out = self.run_control(runner)
        self.assertEqual(code, 1)
        self.assertEqual(runner.calls, ["c1"])
        self.assertIn("spend cap reached", out)

    def test_claude_config_dir_in_sources_mode_is_refused(self):
        runner = ScriptedRunner(self.tmp, self.ledger)
        code, out = self.run_control(runner, dict(self.environ, CLAUDE_CONFIG_DIR=str(self.tmp / "cfg")))
        self.assertEqual(code, 3)
        self.assertIn("unset CLAUDE_CONFIG_DIR", out)
        self.assertEqual(runner.calls, [])

    def test_unreadable_spend_file_refuses_before_any_run(self):
        root = claude_run.eval_root(self.environ)
        root.mkdir(parents=True)
        (root / "spend.json").write_text("garbage", encoding="utf-8")
        runner = ScriptedRunner(self.tmp, self.ledger)
        code, out = self.run_control(runner)
        self.assertEqual(code, 1)
        self.assertEqual(runner.calls, [])
        self.assertIn("spend file unreadable", out)

    def test_runner_exception_becomes_a_label_without_text(self):
        def boom(*a, **k):
            raise RuntimeError("secret-argv /some/path")
        code, out = self.run_control(boom)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip(), "control: ERROR RuntimeError")

    def test_c4_and_c5_ledger_rows_fail_the_control(self):
        for label in ("c4", "c5b"):
            with self.subTest(label=label):
                runner = ScriptedRunner(self.tmp, self.ledger, ledger_labels=(label,))
                code, out = self.run_control(runner)
                self.assertEqual(code, 1)
                self.assertIn("ledger_rows=1", out)

    def test_happy_path_prints_ledger_rows_for_c4_and_c5(self):
        code, out = self.run_control(ScriptedRunner(self.tmp, self.ledger))
        self.assertEqual(code, 0, out)
        self.assertIn("hook_stdout_canary=yes ledger_rows=0", out)
        self.assertIn("denials=0 ledger_rows=0", out)

    def test_ledger_dir_vanishing_mid_control_stops_with_a_label(self):
        import shutil

        class Vanishing(ScriptedRunner):
            def __call__(inner, *a, **kw):
                if kw.get("label") == "c3":
                    shutil.rmtree(self.ledger)
                return ScriptedRunner.__call__(inner, *a, **kw)
        code, out = self.run_control(Vanishing(self.tmp, self.ledger))
        self.assertEqual(code, 1)
        self.assertIn("control: STOP ledger_unreadable", out)


if __name__ == "__main__":
    unittest.main()
