import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

from mdcheck.cli import main
from mdcheck.errors import EXIT_CONFIG

ROOT = os.path.join(os.path.dirname(__file__), "..")
SAMPLES = os.path.join(ROOT, "samples")


class CliTests(unittest.TestCase):
    def test_clean_file_exits_zero(self):
        self.assertEqual(main([os.path.join(SAMPLES, "good.md")]), 0)

    def test_good_sample_exits_zero_as_subprocess(self):
        result = subprocess.run(
            [sys.executable, "-m", "mdcheck", os.path.join(SAMPLES, "good.md")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_findings_exit_one(self):
        self.assertEqual(main([os.path.join(SAMPLES, "bad.md")]), 1)

    def test_warning_does_not_change_exit_code(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
        self.addCleanup(os.remove, handle.name)
        with handle:
            handle.write("# A\n\n### C\n")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main([handle.name]), 0)
        self.assertIn("heading-increment: warning: heading level jumps from h1 to h3", out.getvalue())

    def test_json_format(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
        self.addCleanup(os.remove, handle.name)
        with handle:
            handle.write("# A\n\n### C\t\n")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["--format", "json", handle.name]), 1)
        records = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertIn({"path": handle.name, "line": 3, "rule": "no-tabs", "severity": "error"}, records)
        self.assertIn(
            {"path": handle.name, "line": 3, "rule": "heading-increment", "severity": "warning"},
            records,
        )
        for record in records:
            self.assertEqual(set(record), {"path", "line", "rule", "severity"})

    def test_json_format_clean_and_warning_only(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["--format", "json", os.path.join(SAMPLES, "good.md")]), 0)
        self.assertEqual(out.getvalue(), "")
        handle = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
        self.addCleanup(os.remove, handle.name)
        with handle:
            handle.write("# A\n\n### C\n")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["--format", "json", handle.name]), 0)
        self.assertEqual(
            [json.loads(line) for line in out.getvalue().splitlines()],
            [{"path": handle.name, "line": 3, "rule": "heading-increment", "severity": "warning"}],
        )

    def test_text_is_default_format(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            main([os.path.join(SAMPLES, "bad.md")])
        self.assertIn(": no-tabs: tab character", out.getvalue())

    def write_config(self, text):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        self.addCleanup(os.remove, handle.name)
        with handle:
            handle.write(text)
        return handle.name

    def test_config_selects_rules(self):
        bad = os.path.join(SAMPLES, "bad.md")
        only_length = self.write_config('{"rules": ["line-length"]}')
        only_tabs = self.write_config('{"rules": ["no-tabs"]}')
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["--config", only_length, bad]), 0)
            self.assertEqual(main(["--config", only_tabs, bad]), 1)
        self.assertIn("no-tabs", out.getvalue())
        self.assertNotIn("final-newline", out.getvalue())

    def test_bad_config_exits_config_error(self):
        good = os.path.join(SAMPLES, "good.md")
        with contextlib.redirect_stderr(io.StringIO()):
            for text in ("not json", '{"rules": "no-tabs"}', '{"rules": ["nope"]}'):
                self.assertEqual(main(["--config", self.write_config(text), good]), EXIT_CONFIG)
            self.assertEqual(main(["--config", "/nonexistent/.mdcheck.json", good]), EXIT_CONFIG)


if __name__ == "__main__":
    unittest.main()
