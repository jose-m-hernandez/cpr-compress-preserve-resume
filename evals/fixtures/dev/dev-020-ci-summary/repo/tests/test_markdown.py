import unittest

from cisum.markdown import render_markdown
from cisum.summary import summarise


class RenderMarkdownTests(unittest.TestCase):
    def test_table_without_slow_jobs(self):
        summary = summarise([{"job": "a", "status": "passed", "seconds": 5}])
        self.assertEqual(render_markdown(summary), (
            "| Passed | Failed | Flaky | Total seconds |\n"
            "| ---: | ---: | ---: | ---: |\n"
            "| 1 | 0 | 0 | 5 |\n"
        ))

    def test_slow_jobs_get_their_own_table(self):
        summary = summarise([{"job": "build", "status": "flaky", "seconds": 150}])
        lines = render_markdown(summary).splitlines()
        self.assertEqual(lines[2], "| 0 | 0 | 1 | 150 |")
        self.assertEqual(lines[4:], ["| Slow job | Seconds |", "| --- | ---: |", "| build | 150 |"])


if __name__ == "__main__":
    unittest.main()
