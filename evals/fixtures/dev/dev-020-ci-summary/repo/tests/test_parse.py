import os
import unittest

from cisum.parse import load_results

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "samples")


class LoadResultsTests(unittest.TestCase):
    def test_reads_both_jobs(self):
        results = load_results(os.path.join(SAMPLES, "run1"))
        self.assertEqual([r["job"] for r in results], ["lint", "unit"])

    def test_odd_status_is_rejected(self):
        with self.assertRaises(ValueError):
            load_results(os.path.join(SAMPLES, "odd"))


if __name__ == "__main__":
    unittest.main()
