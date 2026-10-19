"""Offline rehearsal of the one-seed dev baseline command, on the scripted claude and a fake judge.

It proves the command's run count, judge-call count and projected cost before anyone runs it live. Nothing here
calls the real CLI, and every ledger it touches lives in a temporary directory.

Run the tests:    python3 tests/test_evals_rehearse.py
Print the summary: python3 tests/test_evals_rehearse.py print
"""

from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
sys.path.insert(0, str(ROOT / "tests"))

import claude_run  # noqa: E402
import fixtures  # noqa: E402
import pilot  # noqa: E402
import run  # noqa: E402
import test_evals_score as base  # noqa: E402

# The command under rehearsal, as the arguments after `python3 evals/run.py`. Every use below reads this list.
ARGV = ["pilot", "--fixtures", "all", "--seeds", "1", "--arms", "floor,baseline,oracle", "--budget-usd", "5",
        "--out", "evals/results/dev-baseline-1seed"]
COMMAND = "python3 evals/run.py " + " ".join(ARGV)
PRICES_DIR = ROOT / "evals" / "results" / "pilot-20261017"
PRICES_LABEL = "evals/results/pilot-20261017"


def captured_args(argv=None):
    """The positional arguments run.main hands to pilot.command_pilot for argv; the real command is not run."""
    seen = []
    original = pilot.command_pilot
    pilot.command_pilot = lambda *args, **kwargs: seen.append(args) or 0
    try:
        code = run.main(list(ARGV if argv is None else argv))
    finally:
        pilot.command_pilot = original
    assert code == 0 and len(seen) == 1, (code, seen)
    return seen[0]


def _costs(paths):
    return [json.loads(Path(p).read_text(encoding="utf-8"))["cost_usd"] for p in paths]


def pilot_means(results=PRICES_DIR) -> dict:
    """Mean cost and sample size per call kind, read from a committed results tree."""
    results = Path(results)
    labels = json.loads((results / "labels.json").read_text(encoding="utf-8"))
    kinds = {
        "preserve": _costs(sorted(results.glob("preserve/*/*/s*.json"))),
        "probe_session": _costs(sorted(results.glob("probes/*/*/s*.json"))),
        "judge_items": [v["cost_usd"] for v in labels["items"].values()],
        "judge_probe": [v["cost_usd"] for v in labels["probe"].values()],
    }
    return {k: {"mean": sum(v) / len(v), "n": len(v)} for k, v in kinds.items()}


def projection(silent: dict, answers: dict, means: dict) -> dict:
    """Cost by block and the low and high totals, from the counts of the two uncapped modes."""
    p, q = means["preserve"]["mean"], means["probe_session"]["mean"]
    i, j = means["judge_items"]["mean"], means["judge_probe"]["mean"]
    high_blocks = {"preserve": silent["preserve"] * p, "probe_sessions": silent["probe_sessions"] * q,
                   "judge_items": silent["items_calls"] * i, "judge_probe_batches": answers["probe_batches"] * i}
    low = (silent["preserve"] * p + silent["probe_sessions"] * q + silent["items_calls"] * i
           + silent["probe_batches"] * j)
    return {"low": low, "high": sum(high_blocks.values()), "high_blocks": high_blocks}


class PerLineJudge(base.FakeJudge):
    """FakeJudge whose items labelling matches a line only to a needed item of the case in front of it.

    The base class maps each oracle line to an item id, and ids repeat across fixtures, so the cyclic mismatch
    control would match. Here a line matches only when its own item statement is one of the case's needed facts.
    """

    def __init__(self, specs, charge=None, **kw):
        super().__init__(specs, **kw)
        self.charge = charge
        self.statement_of_line = {}
        for spec in specs.values():
            for item in spec["items"]:
                if item["needed"]:
                    self.statement_of_line[item["oracle_line"].strip()] = (item["id"], item["statement"])

    def label_items(self, cfg, case, environ, model=None, **route):
        facts = {n["fact"] for n in case["needed"]}
        self.by_line = {line: iid for line, (iid, statement) in self.statement_of_line.items() if statement in facts}
        result = super().label_items(cfg, case, environ, model, **route)
        self.pay(environ, route)
        return result

    def label_probe(self, cfg, case, environ, model=None, **route):
        result = super().label_probe(cfg, case, environ, model, **route)
        self.pay(environ, route)
        return result

    def pay(self, environ, route):
        if self.charge is not None:
            claude_run.add_spend(self.charge, environ, phase=route["phase"])


def active_specs() -> dict:
    specs = {}
    for path in sorted(base.FIXTURES.glob("*/spec.json")):
        spec = fixtures.load_spec(path)
        if not fixtures.is_excluded(spec):
            specs[path.parent.name] = spec
    return specs


class Rehearsal(base.Env):
    """The scripted environment of test_evals_score, driven through pilot.command_pilot with the command's parameters."""

    def runTest(self):  # lets print mode build an instance outside unittest
        pass

    def setUp(self):
        super().setUp()
        for name, fake in (("preflight", lambda cfg, environ=None: ""), ("load_config", lambda path=None: self.cfg)):
            original = getattr(claude_run, name)
            setattr(claude_run, name, fake)
            self.addCleanup(setattr, claude_run, name, original)

    def rehearse(self, mode="silent", means=None) -> dict:
        """Run the command's parameters in one of: silent (floor answers UNKNOWN), answers, capped."""
        specs = active_specs()
        self.plan = base.build_plan(specs)
        if mode == "answers":
            for spec in specs.values():
                first = spec["repo"]["files"]["CLAUDE.md"].split("\n")[0]
                probe = next(p for p in spec["probes"] if p["type"] != "abstention")
                self.plan["fixtures"][first]["always_correct"] = [probe["id"]]
        charge = None
        if mode == "capped":
            self.plan["preserve_cost"] = means["preserve"]["mean"]
            self.plan["cost"] = means["probe_session"]["mean"]
            charge = means["judge_items"]["mean"]
        self.write_plan()
        judge = PerLineJudge(specs, charge=charge)
        root, out, split, wanted, arm_names, seeds, budget, date = captured_args()
        text = io.StringIO()
        code = pilot.command_pilot(root, self.out, split, wanted, arm_names, seeds, budget, date, self.environ, text,
                                   runner=claude_run.run_claude, label_probe=judge.label_probe,
                                   label_items=judge.label_items, sleep=lambda s: None, head=("0123abc", False))
        state = json.loads((self.out / pilot.STATE_NAME).read_text(encoding="utf-8"))
        per_arm = {arm: len(list(self.out.glob("probes/%s/*/s*.json" % arm))) for arm in arm_names}
        preserve = len(list(self.out.glob("preserve/*/*/s*.json")))
        return {
            "code": code, "output": text.getvalue(), "status": state["status"], "reasons": state["reasons"],
            "args": (root, split, wanted, arm_names, seeds, budget, out), "fixtures": sorted(specs),
            "preserve": preserve,
            "preserve_calls": sum(1 for c in self.calls() if c["argv"][1].startswith("/cpr:preserve")),
            "all_calls": len(self.calls()),
            "probe_per_arm": per_arm, "probe_sessions": sum(per_arm.values()),
            "items_calls": len(judge.items_calls), "probe_batches": len(judge.probe_calls),
            "scores": (self.out / "scores.json").is_file() and json.loads(
                (self.out / "scores.json").read_text(encoding="utf-8")) or None,
            "report": (self.out / "REPORT.md").is_file(),
        }


def run_mode(mode, means=None) -> dict:
    case = Rehearsal()
    case.setUp()
    try:
        return case.rehearse(mode, means)
    finally:
        case.doCleanups()


def rehearsal_all() -> dict:
    means = pilot_means()
    silent, answers, capped = run_mode("silent"), run_mode("answers"), run_mode("capped", means)
    return {"means": means, "silent": silent, "answers": answers, "capped": capped,
            "projection": projection(silent, answers, means)}


def summary(r) -> str:
    s, m, proj, cap = r["silent"], r["means"], r["projection"], r["capped"]
    root, split, wanted, arm_names, seeds, budget, out = s["args"]
    excluded = sorted(p.parent.name for p in base.FIXTURES.glob("*/spec.json")
                      if fixtures.is_excluded(fixtures.load_spec(p)))
    per = s["probe_per_arm"]
    blocks = proj["high_blocks"]
    verdict = "PASS" if proj["high"] <= 5.0 else "STOP"
    units = cap["preserve"] + cap["probe_sessions"]
    judge_calls = cap["items_calls"] + cap["probe_batches"]
    return "\n".join([
        "rehearsal: " + COMMAND,
        "fixtures: %d active (excluded: %s)" % (len(s["fixtures"]), ", ".join(excluded)),
        "claude runs: preserve %d; probe sessions %d (floor %d, baseline %d, oracle %d)" % (
            s["preserve"], s["probe_sessions"], per["floor"], per["baseline"], per["oracle"]),
        "judge calls: items %d; probe batches %d floor silent, %d floor answers" % (
            s["items_calls"], s["probe_batches"], r["answers"]["probe_batches"]),
        "pilot means (%s): preserve $%.4f (n %d); probe session $%.4f (n %d); judge items $%.4f (n %d); "
        "judge probe, one answer $%.4f (n %d)" % (
            PRICES_LABEL, m["preserve"]["mean"], m["preserve"]["n"], m["probe_session"]["mean"], m["probe_session"]["n"],
            m["judge_items"]["mean"], m["judge_items"]["n"], m["judge_probe"]["mean"], m["judge_probe"]["n"]),
        "cost by block (high): preserve $%.2f; probe sessions $%.2f; judge items $%.2f; judge probe batches $%.2f" % (
            blocks["preserve"], blocks["probe_sessions"], blocks["judge_items"], blocks["judge_probe_batches"]),
        "projection: low $%.2f, high $%.2f" % (proj["low"], proj["high"]),
        "capped at $%.2f with pilot-mean costs: %d units run, %d judge calls, status %s; scores.json %s; REPORT.md %s" % (
            budget, units, judge_calls, cap["status"], "present" if cap["scores"] else "absent",
            "present" if cap["report"] else "absent"),
        "verdict: %s (high $%.2f against $%.2f)" % (verdict, proj["high"], budget),
    ])


class ArgvTests(unittest.TestCase):
    def test_the_command_hands_pilot_exactly_the_rehearsed_parameters(self):
        root, out, split, wanted, arm_names, seeds, budget, date = captured_args()
        self.assertEqual(root, base.FIXTURES)
        self.assertEqual(root, ROOT / "evals" / "fixtures" / "dev")
        self.assertEqual((split, wanted, arm_names, seeds, budget), ("dev", "all", ["floor", "baseline", "oracle"], 1, 5.0))
        self.assertEqual(out, Path("evals/results/dev-baseline-1seed"))
        self.assertIsInstance(date, str)


class RehearsalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = rehearsal_all()

    def test_the_fixtures_are_the_nineteen_active_ones(self):
        ids = self.r["silent"]["fixtures"]
        self.assertEqual(len(ids), 19)
        self.assertNotIn("dev-014-log-digest", ids)
        self.assertEqual(ids, self.r["answers"]["fixtures"])
        self.assertEqual(ids, sorted(p.parent.name for p in base.FIXTURES.glob("*/spec.json") if p.parent.name != "dev-014-log-digest"))

    def test_run_counts_when_the_floor_is_silent(self):
        s = self.r["silent"]
        self.assertEqual((s["code"], s["status"], s["reasons"]), (0, "COMPLETE", []))
        self.assertEqual((s["preserve"], s["preserve_calls"]), (19, 19))
        self.assertEqual(s["probe_per_arm"], {"floor": 19, "baseline": 19, "oracle": 19})
        self.assertEqual(s["all_calls"], 19 + 57)
        self.assertEqual((s["items_calls"], s["probe_batches"]), (57, 38))

    def test_run_counts_when_the_floor_answers(self):
        a = self.r["answers"]
        self.assertEqual((a["code"], a["status"], a["reasons"]), (0, "COMPLETE", []))
        self.assertEqual((a["preserve"], a["probe_sessions"], a["all_calls"]), (19, 57, 76))
        self.assertEqual((a["items_calls"], a["probe_batches"]), (57, 57))

    def test_scores_carry_the_code_split_for_every_fixture(self):
        for mode in ("silent", "answers"):
            r = self.r[mode]
            self.assertTrue(r["report"])
            split = r["scores"]["scorable_split"]
            self.assertEqual(sorted(split), r["fixtures"])
            for value in split.values():
                self.assertEqual(sorted(value), ["code", "nocode"])

    def test_the_means_are_read_from_the_committed_results(self):
        m = self.r["means"]
        self.assertEqual((m["preserve"]["n"], m["probe_session"]["n"], m["judge_items"]["n"], m["judge_probe"]["n"]),
                         (15, 45, 25, 166))
        self.assertAlmostEqual(m["preserve"]["mean"], 0.13642469, places=7)
        self.assertAlmostEqual(m["probe_session"]["mean"], 0.01676361, places=7)
        self.assertAlmostEqual(m["judge_items"]["mean"], 0.0472146, places=7)
        self.assertAlmostEqual(m["judge_probe"]["mean"], 0.02167472, places=7)

    def test_the_projection_is_the_counts_times_the_means(self):
        m, s, a = self.r["means"], self.r["silent"], self.r["answers"]
        p, q, i, j = (m[k]["mean"] for k in ("preserve", "probe_session", "judge_items", "judge_probe"))
        low = s["preserve"] * p + s["probe_sessions"] * q + s["items_calls"] * i + s["probe_batches"] * j
        high = s["preserve"] * p + s["probe_sessions"] * q + s["items_calls"] * i + a["probe_batches"] * i
        proj = self.r["projection"]
        self.assertAlmostEqual(proj["low"], low, places=9)
        self.assertAlmostEqual(proj["high"], high, places=9)
        self.assertLessEqual(proj["low"], proj["high"])
        self.assertAlmostEqual(sum(proj["high_blocks"].values()), high, places=9)

    def test_a_five_dollar_budget_at_pilot_mean_costs_stops_where_it_stops(self):
        c = self.r["capped"]
        # The whole batch (76 units, $3.55) runs; the 31st sanity items call crosses the budget; no probe batch, no scores.
        self.assertEqual((c["code"], c["status"]), CAPPED_EXPECTED["outcome"])
        self.assertEqual((c["preserve"], c["probe_sessions"]), CAPPED_EXPECTED["units"])
        self.assertEqual((c["items_calls"], c["probe_batches"]), CAPPED_EXPECTED["judge"])
        self.assertEqual((bool(c["scores"]), c["report"]), CAPPED_EXPECTED["files"])
        self.assertTrue(any(CAPPED_EXPECTED["reason"] in x for x in c["reasons"]), c["reasons"])


CAPPED_EXPECTED = {"outcome": (1, "INCOMPLETE"), "units": (19, 57), "judge": (31, 0), "files": (False, False),
                   "reason": "the pilot budget was reached"}


if __name__ == "__main__":
    if sys.argv[1:] == ["print"]:
        print(summary(rehearsal_all()))
        sys.exit(0)
    unittest.main()
