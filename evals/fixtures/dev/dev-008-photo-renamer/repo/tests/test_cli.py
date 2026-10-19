import os
import tempfile
import unittest

from renamer.cli import main


class CliTests(unittest.TestCase):
    def make_dir(self, tmp):
        open(os.path.join(tmp, "a.jpg"), "w").close()
        with open(os.path.join(tmp, "index.txt"), "w", encoding="utf-8") as handle:
            handle.write("a.jpg | 2026-01-01 | one\n")

    def test_apply_without_yes_is_refused_and_renames_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_dir(tmp)
            self.assertEqual(main(["apply", tmp]), 2)
            self.assertIn("a.jpg", os.listdir(tmp))

    def test_apply_with_yes_renames(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_dir(tmp)
            self.assertEqual(main(["apply", tmp, "--yes"]), 0)
            self.assertIn("2026-01-01_one.jpg", os.listdir(tmp))


if __name__ == "__main__":
    unittest.main()
