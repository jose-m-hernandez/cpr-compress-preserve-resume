import unittest

from renamer.sidecar import parse_sidecar


class SidecarTests(unittest.TestCase):
    def test_reads_three_fields(self):
        self.assertEqual(parse_sidecar("a.jpg | 2026-01-01 | one\n")[0].title, "one")

    def test_bad_line_is_named(self):
        with self.assertRaises(ValueError) as caught:
            parse_sidecar("a.jpg | 2026-01-01\n")
        self.assertIn("line 1", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
