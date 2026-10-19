import datetime
import os
import tempfile
import unittest

from snap.snapshot import make_stamp, snapshot


class SnapshotTests(unittest.TestCase):
    def test_stamp_is_utc_and_formatted(self):
        tz = datetime.timezone(datetime.timedelta(hours=2))
        now = datetime.datetime(2026, 5, 2, 12, 15, 0, tzinfo=tz)
        self.assertEqual(make_stamp(now), "20260502T101500")

    def test_stamps_sort_chronologically(self):
        utc = datetime.timezone.utc
        early = make_stamp(datetime.datetime(2026, 5, 2, 9, 59, 59, tzinfo=utc))
        late = make_stamp(datetime.datetime(2026, 5, 2, 10, 0, 0, tzinfo=utc))
        self.assertLess(early, late)

    def test_default_stamp_matches_format(self):
        self.assertRegex(make_stamp(), r"^\d{8}T\d{6}$")

    def test_copies_the_tree(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dest:
            with open(os.path.join(src, "f.txt"), "w", encoding="utf-8") as handle:
                handle.write("x")
            target = snapshot(src, dest, "one")
            self.assertTrue(os.path.exists(os.path.join(target, "f.txt")))

    def test_destination_inside_source_is_refused(self):
        with tempfile.TemporaryDirectory() as src:
            with self.assertRaises(ValueError):
                snapshot(src, os.path.join(src, "out"), "one")


if __name__ == "__main__":
    unittest.main()
