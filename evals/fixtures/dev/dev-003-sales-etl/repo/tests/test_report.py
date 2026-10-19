import os
import tempfile
import unittest

from etl.report import write_report


class ReportTests(unittest.TestCase):
    def test_writes_report_and_creates_missing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            out_dir = os.path.join(directory, "out")
            path = write_report({"B": 5.0, "A": 1.998}, "2025-01", out_dir)
            self.assertEqual(path, os.path.join(out_dir, "report_2025-01.txt"))
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "A\t2.00\nB\t5.00\n")


if __name__ == "__main__":
    unittest.main()
