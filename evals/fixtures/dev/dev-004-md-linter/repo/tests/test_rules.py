import unittest

from mdcheck.rules import (
    final_newline,
    heading_increment,
    line_length,
    no_bare_urls,
    no_tabs,
    trailing_space,
)


class RuleTests(unittest.TestCase):
    def test_no_tabs_flags_a_tab(self):
        self.assertEqual(no_tabs(["a\n", "\tb\n"]), [(2, "tab character")])

    def test_final_newline(self):
        self.assertEqual(final_newline(["a\n", "b"]), [(2, "file does not end with a newline")])
        self.assertEqual(final_newline(["a\n"]), [])

    def test_trailing_space(self):
        self.assertEqual(trailing_space(["a\n", "b\n", "", "c"]), [])
        self.assertEqual(
            trailing_space(["a \n", "ok\n", "b\t\n", "c "]),
            [(1, "trailing whitespace"), (3, "trailing whitespace"), (4, "trailing whitespace")],
        )

    def test_heading_increment(self):
        ok = ["# A\n", "## B\n", "### C\n", "## D\n", "# E\n", "## F\n"]
        self.assertEqual(heading_increment(ok), [])
        self.assertEqual(heading_increment(["## First\n", "#### Deep\n"]),
                         [(2, "heading level jumps from h2 to h4")])
        skipped = ["# A\n", "text\n", "### C\n"]
        self.assertEqual(heading_increment(skipped), [(3, "heading level jumps from h1 to h3")])

    def test_heading_increment_ignores_code_fences_and_non_headings(self):
        lines = ["# A\n", "```\n", "### not a heading\n", "```\n", "#hashtag\n", "## B\n"]
        self.assertEqual(heading_increment(lines), [])

    def test_no_bare_urls_flags_bare_urls(self):
        lines = ["See https://example.com/a.\n", "ok\n", "a http://x.org and https://y.org\n"]
        self.assertEqual(
            no_bare_urls(lines),
            [
                (1, "bare URL https://example.com/a; use a link"),
                (3, "bare URL http://x.org; use a link"),
                (3, "bare URL https://y.org; use a link"),
            ],
        )

    def test_no_bare_urls_allows_links_code_and_fences(self):
        lines = [
            "[site](https://example.com) and [https://a.org](https://a.org)\n",
            "<https://auto.link> and `https://code.span`\n",
            "[ref]: https://example.com/ref\n",
            "[text][ref] ftp://old.example\n",
            "```\n",
            "https://in.fence\n",
            "```\n",
        ]
        self.assertEqual(no_bare_urls(lines), [])

    def test_line_length(self):
        self.assertEqual(line_length(["a" * 88 + "\n"]), [])
        self.assertEqual(
            line_length(["ok\n", "a" * 89 + "\n"]),
            [(2, "line longer than 88 characters")],
        )


if __name__ == "__main__":
    unittest.main()
