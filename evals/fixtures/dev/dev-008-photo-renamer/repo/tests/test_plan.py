import os
import tempfile
import unittest

from renamer.plan import apply_plan, make_plan, new_name, slugify
from renamer.sidecar import Record, parse_sidecar


class PlanTests(unittest.TestCase):
    def test_new_name_keeps_the_extension(self):
        self.assertTrue(new_name(Record("a.png", "2026-01-01", "x")).endswith(".png"))

    def test_slug_is_lowercase_with_hyphens(self):
        self.assertEqual(slugify("Harbour  Walk, Day 1!"), "harbour-walk-day-1")
        self.assertEqual(new_name(Record("a.jpg", "2026-04-02", "Harbour Walk")), "2026-04-02_harbour-walk.jpg")

    def test_slug_is_capped_at_30_characters(self):
        self.assertEqual(slugify("a" * 60), "a" * 30)
        self.assertEqual(slugify("word " * 20), ("word-" * 6)[:-1])

    def test_plan_is_sorted_by_old_name(self):
        plan = make_plan(parse_sidecar("b.jpg | 2026-01-02 | two\na.jpg | 2026-01-01 | one\n"))
        self.assertEqual([old for old, _ in plan], ["a.jpg", "b.jpg"])

    def test_same_target_is_refused(self):
        with self.assertRaises(ValueError):
            make_plan([Record("a.jpg", "2026-01-01", "x"), Record("b.jpg", "2026-01-01", "x")])

    def test_apply_renames_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "a.jpg"), "w").close()
            apply_plan(tmp, [("a.jpg", "new.jpg")])
            self.assertEqual(sorted(os.listdir(tmp)), [".renamer-undo.json", "new.jpg"])

    def test_apply_changes_nothing_if_a_target_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("a.jpg", "b.jpg", "x.jpg"):
                open(os.path.join(tmp, name), "w").close()
            with self.assertRaises(ValueError):
                apply_plan(tmp, [("a.jpg", "n.jpg"), ("b.jpg", "x.jpg")])
            self.assertEqual(sorted(os.listdir(tmp)), ["a.jpg", "b.jpg", "x.jpg"])


if __name__ == "__main__":
    unittest.main()
