import contextlib
import io
import os
import tempfile
import unittest

from ledger.parse import parse_file, parse_line
from unittest import mock

from ledger import cli
from ledger.cli import main
from ledger.summary import since, top_totals, totals_by, totals_by_category, week_start

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


class SummaryTests(unittest.TestCase):
    def test_totals_the_sample_file(self):
        totals = totals_by_category(parse_file(os.path.join(DATA, "sample.txt")))
        self.assertEqual(totals["food"], 7000)

    def test_mixed_case_categories_share_one_bucket(self):
        entries = [
            parse_line("2026-03-02 | shop | 1.00 | Food", 1),
            parse_line("2026-03-03 | snack | 2.50 | food", 2),
            parse_line("2026-03-04 | lunch | 3.00 | FOOD", 3),
        ]
        self.assertEqual(totals_by_category(entries), {"food": 650})

    def test_since_skips_earlier_entries_but_keeps_the_start_day(self):
        entries = parse_file(os.path.join(DATA, "sample.txt"))
        kept = since(entries, "2026-03-09")
        self.assertEqual([e.date for e in kept], ["2026-03-09", "2026-03-10"])

    def test_cli_since_filters_the_report(self):
        code, text = self.run_main(
            [os.path.join(DATA, "sample.txt"), "--by", "category", "--since", "2026-03-09"], {})
        self.assertEqual(code, 0)
        self.assertEqual(text.splitlines()[0].split(), ["food", "27.50"])
        self.assertNotIn("travel", text)

    def test_cli_rejects_a_bad_since_date(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main([os.path.join(DATA, "sample.txt"), "--since", "March"])

    def test_week_start_is_the_monday(self):
        self.assertEqual(week_start("2026-03-02"), "2026-03-02")
        self.assertEqual(week_start("2026-03-08"), "2026-03-02")
        self.assertEqual(week_start("2026-03-09"), "2026-03-09")

    def test_totals_by_week_for_the_sample_file(self):
        totals = totals_by(parse_file(os.path.join(DATA, "sample.txt")), "week")
        self.assertEqual(totals, {"2026-03-02": 7250, "2026-03-09": 52750})

    def test_totals_by_month_splits_on_the_month_boundary(self):
        entries = [
            parse_line("2026-02-28 | a | 1.00 | food", 1),
            parse_line("2026-03-01 | b | 2.00 | food", 2),
            parse_line("2026-03-31 | c | 3.00 | rent", 3),
        ]
        self.assertEqual(totals_by(entries, "month"), {"2026-02": 100, "2026-03": 500})

    def test_cli_groups_by_month_by_default(self):
        code, text = self.run_main([os.path.join(DATA, "sample.txt")], {})
        self.assertEqual(code, 0)
        self.assertEqual(text.split(), ["2026-03", "600.00"])

    def test_cli_by_week(self):
        code, text = self.run_main([os.path.join(DATA, "sample.txt"), "--by", "week"], {})
        self.assertEqual(code, 0)
        self.assertEqual(text.split()[0], "2026-03-02")

    def test_cli_by_category(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            main([os.path.join(DATA, "sample.txt"), "--by", "category"])
        self.assertEqual(out.getvalue().split()[0], "food")

    def test_top_totals_keeps_the_biggest(self):
        totals = {"a": 100, "b": 300, "c": 200}
        self.assertEqual(top_totals(totals, 2), {"b": 300, "c": 200})

    def test_top_totals_breaks_ties_by_name(self):
        self.assertEqual(top_totals({"b": 100, "a": 100}, 1), {"a": 100})

    def test_cli_top_limits_the_report(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main([os.path.join(DATA, "sample.txt"), "--by", "category", "--top", "2"])
        self.assertEqual(code, 0)
        self.assertEqual([line.split()[0] for line in out.getvalue().splitlines()], ["food", "rent"])

    def test_cli_top_defaults_to_three(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "many.txt")
            with open(path, "w", encoding="utf-8") as handle:
                for number in range(7):
                    handle.write(f"2026-03-02 | item | {number + 1}.00 | cat{number}\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                main([path, "--by", "category"])
        self.assertEqual(len(out.getvalue().splitlines()), 3)

    def test_cli_rejects_a_zero_top(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main([os.path.join(DATA, "sample.txt"), "--top", "0"])

    def run_main(self, argv, env):
        out = io.StringIO()
        with mock.patch.dict(os.environ, env), contextlib.redirect_stdout(out):
            code = main(argv)
        return code, out.getvalue()

    def test_file_comes_from_ledger_file_when_omitted(self):
        sample = os.path.join(DATA, "sample.txt")
        code, text = self.run_main(["--by", "category"], {"LEDGER_FILE": sample})
        self.assertEqual(code, 0)
        self.assertEqual(text.split()[0], "food")

    def test_file_argument_beats_ledger_file(self):
        sample = os.path.join(DATA, "sample.txt")
        code, text = self.run_main([sample, "--by", "category"], {"LEDGER_FILE": "/no/such/file"})
        self.assertEqual(code, 0)
        self.assertEqual(text.split()[0], "food")

    def test_file_defaults_to_data_ledger_when_unset(self):
        self.assertEqual(cli.DEFAULT_FILE, os.path.join("data", "ledger.txt"))
        with tempfile.TemporaryDirectory() as folder:
            default = os.path.join(folder, "ledger.txt")
            with open(default, "w", encoding="utf-8") as handle:
                handle.write("2026-03-02 | tea | 1.50 | drinks\n")
            env = {k: v for k, v in os.environ.items() if k != "LEDGER_FILE"}
            with mock.patch.object(cli, "DEFAULT_FILE", default), \
                    mock.patch.dict(os.environ, env, clear=True), \
                    contextlib.redirect_stdout(io.StringIO()) as out:
                code = main(["--by", "category"])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().split()[0], "drinks")

    def test_missing_file_is_reported_not_raised(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code, _ = self.run_main([], {"LEDGER_FILE": "/no/such/file"})
        self.assertEqual(code, 1)
        self.assertTrue(err.getvalue().startswith("error: "))


if __name__ == "__main__":
    unittest.main()
