import unittest

from inventory.diff import compare


class CompareTests(unittest.TestCase):
    def test_finds_added_removed_and_changed(self):
        kinds = [d.kind for d in compare({"A-1": 1, "B-1": 1}, {"A-1": 2, "C-1": 1})]
        self.assertEqual(kinds, ["changed", "removed", "added"])

    def test_equal_lists_have_no_differences(self):
        self.assertEqual(compare({"A-1": 1}, {"A-1": 1}), [])

    def test_change_within_tolerance_is_ignored(self):
        self.assertEqual(compare({"A-1": 10}, {"A-1": 11}, tolerance=1), [])
        self.assertEqual(compare({"A-1": 10}, {"A-1": 9}, tolerance=1), [])

    def test_change_beyond_tolerance_is_reported(self):
        self.assertEqual(len(compare({"A-1": 10}, {"A-1": 12}, tolerance=1)), 1)
        self.assertEqual(len(compare({"A-1": 10}, {"A-1": 8}, tolerance=1)), 1)

    def test_tolerance_does_not_hide_added_or_removed(self):
        kinds = [d.kind for d in compare({"B-1": 1}, {"A-1": 1}, tolerance=1)]
        self.assertEqual(kinds, ["added", "removed"])


if __name__ == "__main__":
    unittest.main()
