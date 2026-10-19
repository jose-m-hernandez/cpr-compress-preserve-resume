import unittest

from ledger.report import format_report


class ReportTests(unittest.TestCase):
    def test_report_has_one_line_per_category(self):
        report = format_report({"food": 100, "rent": 200})
        self.assertEqual(len(report.split("\n")), 2)

    def test_report_prints_dollars_and_cents_sorted_by_name(self):
        report = format_report({"rent": 50000, "food": 7005})
        self.assertEqual(report.splitlines(), ["food      70.05", "rent     500.00"])


if __name__ == "__main__":
    unittest.main()
