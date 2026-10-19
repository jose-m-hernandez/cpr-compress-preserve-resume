import json
import unittest

from mdcheck.formats import FORMATS, format_finding, severity


class FormatTests(unittest.TestCase):
    def test_formats_list(self):
        self.assertEqual(FORMATS, ["text", "json"])

    def test_severity(self):
        self.assertEqual(severity("no-tabs"), "error")
        self.assertEqual(severity("heading-increment"), "warning")

    def test_text_error(self):
        self.assertEqual(
            format_finding("text", "a.md", 3, "no-tabs", "tab character"),
            "a.md:3: no-tabs: tab character",
        )

    def test_text_warning(self):
        self.assertEqual(
            format_finding("text", "a.md", 3, "heading-increment", "jump"),
            "a.md:3: heading-increment: warning: jump",
        )

    def test_json(self):
        line = format_finding("json", "a.md", 3, "heading-increment", "jump")
        self.assertNotIn("\n", line)
        self.assertEqual(
            json.loads(line),
            {"path": "a.md", "line": 3, "rule": "heading-increment", "severity": "warning"},
        )


if __name__ == "__main__":
    unittest.main()
