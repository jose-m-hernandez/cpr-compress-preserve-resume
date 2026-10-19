import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_cisum(jobs):
    """Run cisum on a temporary folder holding the given jobs."""
    with tempfile.TemporaryDirectory() as folder:
        for job in jobs:
            with open(os.path.join(folder, job["job"] + ".json"), "w", encoding="utf-8") as handle:
                json.dump(job, handle)
        return subprocess.run(
            [sys.executable, "-m", "cisum", folder],
            cwd=ROOT, capture_output=True, text=True,
        )


class ExitCodeTests(unittest.TestCase):
    def test_flaky_job_is_reported_but_does_not_fail(self):
        done = run_cisum([
            {"job": "a", "status": "passed", "seconds": 1},
            {"job": "b", "status": "flaky", "seconds": 1},
        ])
        self.assertEqual(done.returncode, 0)
        self.assertIn("flaky: 1", done.stdout)

    def test_failed_job_still_fails(self):
        done = run_cisum([{"job": "a", "status": "failed", "seconds": 1}])
        self.assertEqual(done.returncode, 1)


if __name__ == "__main__":
    unittest.main()
