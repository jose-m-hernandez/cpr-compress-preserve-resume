import unittest

from cisum.summary import slow_jobs, summarise, unique_jobs


class SummariseTests(unittest.TestCase):
    def test_counts_and_adds_up(self):
        results = [{"status": "passed", "seconds": 5}, {"status": "failed", "seconds": 7}]
        summary = summarise(results)
        self.assertEqual((summary["passed"], summary["failed"], summary["seconds"]), (1, 1, 12))

    def test_slow_jobs_are_over_120_seconds(self):
        results = [
            {"job": "a", "status": "passed", "seconds": 120},
            {"job": "b", "status": "passed", "seconds": 121},
            {"job": "c", "status": "failed"},
            {"job": "integration", "status": "passed", "seconds": 90},
        ]
        self.assertEqual([r["job"] for r in slow_jobs(results)], ["b"])

    def test_summarise_lists_slow_jobs(self):
        results = [{"job": "b", "status": "passed", "seconds": 150}]
        self.assertEqual(summarise(results)["slow"], results)

    def test_job_names_match_case_insensitively(self):
        results = [
            {"job": "Unit", "status": "failed", "seconds": 10},
            {"job": "unit", "status": "passed", "seconds": 20},
        ]
        self.assertEqual(unique_jobs(results), [results[1]])
        summary = summarise(results)
        self.assertEqual((summary["passed"], summary["failed"], summary["seconds"]), (1, 0, 20))

    def test_unnamed_jobs_are_not_merged(self):
        results = [{"status": "passed"}, {"status": "passed"}]
        self.assertEqual(summarise(results)["passed"], 2)


if __name__ == "__main__":
    unittest.main()
