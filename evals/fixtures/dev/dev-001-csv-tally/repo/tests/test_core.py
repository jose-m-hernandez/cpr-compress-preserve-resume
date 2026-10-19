import contextlib
import io
import os
import unittest

from tally.cli import main
from tally.core import count_rows, load_rows, sum_column

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "samples")


class SumColumnTests(unittest.TestCase):
    def test_sums_the_basic_sample(self):
        rows = load_rows(os.path.join(SAMPLES, "basic.csv"))
        self.assertEqual(sum_column(rows, "amount"), 10.0)

    def test_reads_a_semicolon_separated_file(self):
        rows = load_rows(os.path.join(SAMPLES, "semicolons.csv"), delimiter=";")
        self.assertEqual(sum_column(rows, "amount"), 4.0)

    def test_count_rows_excludes_the_header(self):
        rows = load_rows(os.path.join(SAMPLES, "basic.csv"))
        self.assertEqual(count_rows(rows), len(rows))

    def test_count_flag_prints_the_row_count_without_a_column(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            main([os.path.join(SAMPLES, "semicolons.csv"), "--delimiter", ";", "--count"])
        self.assertEqual(out.getvalue().strip(), "2")

    def test_bad_number_names_the_column(self):
        with self.assertRaises(ValueError) as caught:
            sum_column([{"amount": "x"}], "amount")
        self.assertIn("amount", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
