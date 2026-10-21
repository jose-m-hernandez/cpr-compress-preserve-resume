"""Offline rehearsal of the probe-only re-run of the ten repaired dev fixtures, on the scripted claude and a fake judge.

The command re-asks the 30 probe sessions (10 fixtures x 3 arms) of a copy of the one-seed dev baseline whose probe
files for those ten fixtures were removed. It proves, before anyone runs it live, that no preserve run happens, that the
probe-session and judge-call counts are the expected ones, that the nine untouched fixtures come out byte-identical, and
what the run costs at the prices the committed baseline observed. Nothing here calls the real CLI, nothing is written
into the committed results directory, and every ledger it touches lives in a temporary directory.

Run the tests:    python3 tests/test_evals_rehearse_repair.py
Print the summary: python3 tests/test_evals_rehearse_repair.py print
"""

from __future__ import annotations

import io
import json
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
sys.path.insert(0, str(ROOT / "tests"))

import arms  # noqa: E402
import claude_run  # noqa: E402
import legacy_labels  # noqa: E402
import pilot  # noqa: E402
import run  # noqa: E402
import test_evals_score as base  # noqa: E402
from test_evals_rehearse import PerLineJudge, active_specs  # noqa: E402

# The ten fixtures whose probes were repaired, and the command under rehearsal as the arguments after
# `python3 evals/run.py`. Every use below reads these.
REPAIRED = ["dev-002-notes-api", "dev-005-flag-service", "dev-009-inventory-diff", "dev-010-cron-expr",
            "dev-011-webhook-router", "dev-012-backup-snapshots", "dev-013-unit-convert",
            "dev-015-adventure-engine", "dev-016-mail-templates", "dev-019-plugin-registry"]
ARGV = ["pilot", "--fixtures", ",".join(f[:7] for f in REPAIRED), "--seeds", "1", "--arms", "floor,baseline,oracle",
        "--budget-usd", "2.25", "--out", "evals/results/dev-baseline-1seed-r1"]
COMMAND = "python3 evals/run.py " + " ".join(ARGV)
ARMS = ["floor", "baseline", "oracle"]
BUDGET = 2.25
SPEND_CAP = 3.00
COMMITTED = ROOT / "evals" / "results" / "dev-baseline-1seed"
COMMITTED_LABEL = "evals/results/dev-baseline-1seed"
RUN_ID = "dev-baseline-1seed-r1"
SCORE_KEYS = ("scorable", "scorable_counts", "scorable_split", "dropped")  # keyed by fixture id


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


def prepare(out):
    """Copy the committed baseline's tracked content, with the ten fixtures' probe files removed."""
    out = Path(out)
    shutil.copy(COMMITTED / "run.json", out / "run.json")
    # The committed labels keep the legacy key format; the rehearsal reads a converted copy (a label for a question the
    # repair reworded matches no current case and is left out, as the cache would miss it anyway).
    specs = legacy_labels.load_specs(ROOT / "evals" / "fixtures" / "dev")
    arms.write_json(out / "labels.json", legacy_labels.convert(
        COMMITTED / "labels.json", [COMMITTED], [specs], claude_run.load_config()["judge"]["model"]))
    for name in ("arms", "preserve", "probes"):  # never _raw/, never a write into the committed directory
        shutil.copytree(COMMITTED / name, out / name)
    for fid in REPAIRED:
        for arm in ARMS:
            (out / "probes" / arm / fid / "s1.json").unlink()
    meta = arms.read_json(out / "run.json")
    meta["run_id"] = RUN_ID
    arms.write_json(out / "run.json", meta)


def stats(values) -> dict:
    return {"n": len(values), "mean": sum(values) / len(values), "max": max(values)}


def committed_prices(results=COMMITTED) -> dict:
    """n, mean and max cost per call kind, from a committed results tree."""
    results = Path(results)
    labels = json.loads((results / "labels.json").read_text(encoding="utf-8"))
    sessions = [json.loads(p.read_text(encoding="utf-8"))["cost_usd"] for p in sorted(results.glob("probes/*/*/s*.json"))]
    return {"probe_session": stats(sessions),
            "judge_probe": stats([v["cost_usd"] for v in labels["probe"].values()]),
            "judge_items": stats([v["cost_usd"] for v in labels["items"].values()])}


def projection(silent: dict, answers: dict, prices: dict) -> dict:
    """Cost by block and the low and high totals, from the counts of the two uncapped modes."""
    p, j, i = prices["probe_session"], prices["judge_probe"], prices["judge_items"]
    high_blocks = {"probe_sessions": answers["probe_sessions"] * p["max"],
                   "judge_probe_batches": answers["probe_batches"] * j["max"],
                   "judge_items": answers["items_calls"] * i["max"]}
    low = (silent["probe_sessions"] * p["mean"] + silent["probe_batches"] * j["mean"]
           + silent["items_calls"] * i["mean"])
    return {"low": low, "high": sum(high_blocks.values()), "high_blocks": high_blocks}


class KindJudge(PerLineJudge):
    """PerLineJudge that records the order of its calls and charges each kind of call its own amount."""

    def __init__(self, specs, charges=None, **kw):
        super().__init__(specs, **kw)
        self.charges, self.order, self.kind = charges, [], None

    def label_items(self, cfg, case, environ, model=None, **route):
        self.order.append("items")
        self.kind = "items"
        return super().label_items(cfg, case, environ, model, **route)

    def label_probe(self, cfg, case, environ, model=None, **route):
        self.order.append("probe")
        self.kind = "probe"
        return super().label_probe(cfg, case, environ, model, **route)

    def pay(self, environ, route):
        if self.charges is not None:
            claude_run.add_spend(self.charges[self.kind], environ, phase=route["phase"])


def _bytes_differ(committed_dir, new_dir, fid) -> list:
    """Relative paths under arms/, preserve/, probes/ for fid whose bytes differ from the committed ones, or are missing."""
    bad = []
    for name in ("arms", "preserve", "probes"):
        for path in sorted(committed_dir.glob(f"{name}/*/{fid}/*")):
            other = new_dir / path.relative_to(committed_dir)
            if not other.is_file() or other.read_bytes() != path.read_bytes():
                bad.append(str(path.relative_to(committed_dir)))
    return bad


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

    def answer_from_added_text(self, spec, fid):
        """Make the scripted claude answer a probe when the arm's text carries something the floor lacks.

        build_plan's needle is an oracle line, which the committed baseline texts (real preserve output) paraphrase, so
        the baseline sessions would all answer UNKNOWN here although every committed baseline session answered. The
        needle becomes the first line the committed baseline and oracle texts share and the floor lacks (a section
        heading); the floor, which has none, answers UNKNOWN.
        """
        text = {a: (COMMITTED / "arms" / a / fid / "s1.md").read_text(encoding="utf-8") for a in ARMS}
        floor_lines = {ln.strip() for ln in text["floor"].splitlines()}
        baseline_lines = {ln.strip() for ln in text["baseline"].splitlines()}
        shared = [ln.strip() for ln in text["oracle"].splitlines()
                  if ln.strip() and ln.strip() in baseline_lines and ln.strip() not in floor_lines]
        oracle_only = [ln.strip() for ln in text["oracle"].splitlines()
                       if ln.strip() and ln.strip() not in text["baseline"] and ln.strip() not in text["floor"]]
        assert shared and oracle_only, fid
        first = spec["repo"]["files"]["CLAUDE.md"].split("\n")[0]
        entry = self.plan["fixtures"][first]
        for probe in entry["probes"].values():
            if not probe.get("abstention"):
                probe["needle"] = shared[0]
        # The baseline and oracle sessions of a live run give different answers, and the judge's cache is keyed on the
        # answer: two identical scripted answer sets would make the second session a free cache hit. A line only the
        # oracle text carries makes its abstention probes answer wrongly, so the two sessions differ as live ones do.
        entry["false_if"] = oracle_only[0]

    def rehearse(self, mode="silent", prices=None) -> dict:
        """Run the command's parameters in one of: silent (floor answers UNKNOWN), answers, priced (answers, at max prices)."""
        specs = active_specs()
        self.plan = base.build_plan(specs)
        for fid in REPAIRED:
            self.answer_from_added_text(specs[fid], fid)
        if mode in ("answers", "priced"):
            for fid in REPAIRED:
                first = specs[fid]["repo"]["files"]["CLAUDE.md"].split("\n")[0]
                probe = next(p for p in specs[fid]["probes"] if p["type"] != "abstention")
                self.plan["fixtures"][first]["always_correct"] = [probe["id"]]
        charges = None
        if mode == "priced":
            self.plan["cost"] = prices["probe_session"]["max"]
            charges = {"probe": prices["judge_probe"]["max"], "items": prices["judge_items"]["max"]}
        self.write_plan()
        self.out.mkdir()
        prepare(self.out)
        judge = KindJudge(specs, charges=charges)
        root, out, split, wanted, arm_names, seeds, budget, date = captured_args()
        text = io.StringIO()
        code = pilot.command_pilot(root, self.out, split, wanted, arm_names, seeds, budget, date, self.environ, text,
                                   runner=claude_run.run_claude, label_probe=judge.label_probe,
                                   label_items=judge.label_items, sleep=lambda s: None, head=("0123abc", False))
        state = json.loads((self.out / pilot.STATE_NAME).read_text(encoding="utf-8"))
        scores = (self.out / "scores.json").is_file() and json.loads(
            (self.out / "scores.json").read_text(encoding="utf-8")) or None
        committed = json.loads((COMMITTED / "scores.json").read_text(encoding="utf-8"))
        meta = arms.read_json(self.out / "run.json")
        untouched = [f for f in meta["fixtures"] if f not in REPAIRED]
        per_arm = {arm: len(list(self.out.glob("probes/%s/*/s*.json" % arm))) for arm in arm_names}
        first_probe = judge.order.index("probe") if "probe" in judge.order else len(judge.order)
        report = self.out / "REPORT.md"
        return {
            "code": code, "output": text.getvalue(), "status": state["status"], "reasons": state["reasons"],
            "args": (root, split, wanted, arm_names, seeds, budget, out, date), "selected": pilot.expand_fixtures(root, wanted),
            "all_active": sorted(specs), "run_fixtures": meta["fixtures"], "run_id": meta["run_id"],
            "untouched": untouched,
            "preserve": len(list(self.out.glob("preserve/*/*/s*.json"))) - len(list((COMMITTED / "preserve").glob("*/*/s*.json"))),
            "preserve_units": len(list(self.out.glob("arms/*/*/s*.md"))) - len(list((COMMITTED / "arms").glob("*/*/s*.md"))),
            "preserve_calls": sum(1 for c in self.calls() if c["argv"][1].startswith("/cpr:preserve")),
            "all_calls": len(self.calls()),
            "probe_per_arm": {arm: len([f for f in REPAIRED if (self.out / "probes" / arm / f / "s1.json").is_file()])
                              for arm in arm_names},
            "probe_files": per_arm,
            "probe_sessions": sum(1 for c in self.calls() if "Questions:" in c["argv"][1]),
            "items_calls": judge.order.count("items"), "probe_batches": judge.order.count("probe"),
            "items_before_probes": judge.order[:first_probe].count("items"),
            "items_after_probes": judge.order[first_probe:].count("items"),
            "sanity_cases": 2 * len(meta["fixtures"]),
            "ledger": claude_run.spend_total(self.environ, "pilot"),
            "scores": scores, "committed_scores": committed,
            "report_first_line": report.read_text(encoding="utf-8").splitlines()[0] if report.is_file() else None,
            "untouched_byte_diffs": {f: _bytes_differ(COMMITTED, self.out, f) for f in untouched},
            "repaired_kept_preserve": {f: [p for p in _bytes_differ(COMMITTED, self.out, f) if not p.startswith("probes/")]
                                       for f in REPAIRED},
            "repaired_new_probes": {f: [a for a in ARMS if (self.out / "probes" / a / f / "s1.json").is_file()]
                                    for f in REPAIRED},
        }


def run_mode(mode, prices=None) -> dict:
    case = Rehearsal()
    case.setUp()
    try:
        return case.rehearse(mode, prices)
    finally:
        case.doCleanups()


def rehearsal_all() -> dict:
    prices = committed_prices()
    silent, answers, priced = run_mode("silent"), run_mode("answers"), run_mode("priced", prices)
    return {"prices": prices, "silent": silent, "answers": answers, "priced": priced,
            "projection": projection(silent, answers, prices)}


def summary(r) -> str:
    s, a, pr, proj, m = r["silent"], r["answers"], r["priced"], r["projection"], r["prices"]
    blocks = proj["high_blocks"]
    per = s["probe_per_arm"]
    cached = s["sanity_cases"] - s["items_before_probes"]
    verdict = ("PASS (high $%.2f against budget $%.2f; spend cap $%.2f)" % (proj["high"], BUDGET, SPEND_CAP)
               if proj["high"] <= BUDGET else "STOP (high $%.2f exceeds budget $%.2f)" % (proj["high"], BUDGET))
    return "\n".join([
        "rehearsal: " + COMMAND,
        "fixtures: %d (%s)" % (len(s["selected"]), ", ".join(s["selected"])),
        "claude runs: preserve %d; probe sessions %d (floor %d, baseline %d, oracle %d); total %d" % (
            s["preserve_units"], s["probe_sessions"], per["floor"], per["baseline"], per["oracle"], s["all_calls"]),
        "judge calls: sanity %d cases, %d cached, %d new; arm items %d new; probe batches %d silent / %d answers" % (
            s["sanity_cases"], cached, s["items_before_probes"], s["items_after_probes"], s["probe_batches"],
            a["probe_batches"]),
        "prices (%s): probe session n %d, mean $%.8f, max $%.8f; judge probe batch n %d, mean $%.8f, max $%.8f; "
        "judge items n %d, mean $%.8f, max $%.8f" % (
            COMMITTED_LABEL, m["probe_session"]["n"], m["probe_session"]["mean"], m["probe_session"]["max"],
            m["judge_probe"]["n"], m["judge_probe"]["mean"], m["judge_probe"]["max"],
            m["judge_items"]["n"], m["judge_items"]["mean"], m["judge_items"]["max"]),
        "cost by block (high): probe sessions $%.4f; judge probe batches $%.4f; judge items $%.4f" % (
            blocks["probe_sessions"], blocks["judge_probe_batches"], blocks["judge_items"]),
        "projection: low $%.2f, high $%.2f" % (proj["low"], proj["high"]),
        "priced run at max prices: status %s, exit %d, ledger growth $%.6f (budget $%.2f)" % (
            pr["status"], pr["code"], pr["ledger"], BUDGET),
        "verdict: " + verdict,
    ])


class ArgvTests(unittest.TestCase):
    def test_the_command_hands_pilot_exactly_the_rehearsed_parameters(self):
        root, out, split, wanted, arm_names, seeds, budget, date = captured_args()
        self.assertEqual(root, base.FIXTURES)
        self.assertEqual(root, ROOT / "evals" / "fixtures" / "dev")
        self.assertEqual((split, wanted, arm_names, seeds, budget),
                         ("dev", ",".join(f[:7] for f in REPAIRED), ["floor", "baseline", "oracle"], 1, 2.25))
        self.assertEqual(out, Path("evals/results/dev-baseline-1seed-r1"))
        self.assertIsInstance(date, str)


class RehearsalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = rehearsal_all()

    def modes(self, *names):
        return [self.r[n] for n in names]

    def test_the_selection_is_exactly_the_ten_repaired_fixtures(self):
        self.assertEqual(len(REPAIRED), 10)
        self.assertEqual(REPAIRED, sorted(REPAIRED))
        for r in self.modes("silent", "answers", "priced"):
            self.assertEqual(r["selected"], REPAIRED)
            self.assertTrue(set(REPAIRED) <= set(r["all_active"]))  # all ten are active fixtures
            self.assertEqual(len(r["run_fixtures"]), 19)
            self.assertEqual(len(r["untouched"]), 9)

    def test_no_preserve_run_happens_in_any_mode(self):
        for r in self.modes("silent", "answers", "priced"):
            self.assertEqual((r["preserve"], r["preserve_units"], r["preserve_calls"]), (0, 0, 0))

    def test_thirty_probe_sessions_ten_per_arm_in_every_mode(self):
        for r in self.modes("silent", "answers", "priced"):
            self.assertEqual(r["probe_per_arm"], {"floor": 10, "baseline": 10, "oracle": 10})
            self.assertEqual((r["probe_sessions"], r["all_calls"]), (30, 30))

    def test_judge_calls_split_by_phase(self):
        for r in self.modes("silent", "answers", "priced"):
            self.assertEqual(r["sanity_cases"], 38)
            self.assertEqual(r["items_before_probes"], 0)  # every sanity-control case is cached
            self.assertEqual(r["items_after_probes"], 1)  # the dev-011-webhook-router baseline case
            self.assertEqual(r["items_calls"], 1)
        self.assertEqual(self.r["silent"]["probe_batches"], 20)
        self.assertEqual(self.r["answers"]["probe_batches"], 30)
        self.assertEqual(self.r["priced"]["probe_batches"], 30)

    def test_the_untouched_nine_are_byte_identical(self):
        r = self.r["silent"]
        self.assertEqual(r["untouched_byte_diffs"], {f: [] for f in r["untouched"]})
        new, old = r["scores"], r["committed_scores"]
        for fid in r["untouched"]:
            for key in SCORE_KEYS:
                self.assertEqual(new[key][fid], old[key][fid], (key, fid))
            for key in ("per_fixture", "per_seed"):
                self.assertEqual(sorted(new[key]), sorted(old[key]))
                for arm in old[key]:
                    self.assertEqual(new[key][arm][fid], old[key][arm][fid], (key, arm, fid))

    def test_the_repaired_ten_kept_their_preserve_outputs_and_got_new_probe_files(self):
        r = self.r["silent"]
        self.assertEqual(r["repaired_kept_preserve"], {f: [] for f in REPAIRED})
        self.assertEqual(r["repaired_new_probes"], {f: ARMS for f in REPAIRED})
        self.assertEqual(r["probe_files"], {"floor": 19, "baseline": 19, "oracle": 19})

    def test_status_and_outputs(self):
        for r in self.modes("silent", "answers"):
            self.assertEqual((r["code"], r["status"], r["reasons"]), (0, "COMPLETE", []))
            self.assertIsNotNone(r["scores"])
            self.assertEqual(r["report_first_line"], "# Evaluation report: dev-baseline-1seed-r1")
            self.assertEqual(r["run_id"], RUN_ID)

    def test_the_prices_are_read_from_the_committed_baseline_and_the_projection_is_counts_times_prices(self):
        m = self.r["prices"]
        self.assertEqual((m["probe_session"]["n"], m["judge_probe"]["n"], m["judge_items"]["n"]), (57, 41, 56))
        s, a, proj = self.r["silent"], self.r["answers"], self.r["projection"]
        p, j, i = m["probe_session"], m["judge_probe"], m["judge_items"]
        low = s["probe_sessions"] * p["mean"] + s["probe_batches"] * j["mean"] + s["items_calls"] * i["mean"]
        high = a["probe_sessions"] * p["max"] + a["probe_batches"] * j["max"] + a["items_calls"] * i["max"]
        self.assertAlmostEqual(proj["low"], low, places=9)
        self.assertAlmostEqual(proj["high"], high, places=9)
        self.assertLessEqual(proj["low"], proj["high"])
        self.assertAlmostEqual(sum(proj["high_blocks"].values()), high, places=9)

    def test_the_priced_run_fits_the_budget(self):
        c = self.r["priced"]
        self.assertEqual((c["code"], c["status"], c["reasons"]), (0, "COMPLETE", []))
        # The ledger rounds its running total to 6 places at every charge (claude_run.add_spend): at most 5e-7 each.
        charges = c["probe_sessions"] + c["probe_batches"] + c["items_calls"]
        self.assertAlmostEqual(c["ledger"], self.r["projection"]["high"], delta=charges * 5e-7)
        self.assertLess(c["ledger"], BUDGET)


if __name__ == "__main__":
    if sys.argv[1:] == ["print"]:
        print(summary(rehearsal_all()))
        sys.exit(0)
    unittest.main()
