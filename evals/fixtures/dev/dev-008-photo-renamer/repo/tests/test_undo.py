import os
import tempfile
import unittest

from renamer.plan import apply_plan
from renamer.undo import LOG_NAME, read_log, write_log


class UndoLogTests(unittest.TestCase):
    def test_apply_logs_one_entry_per_rename(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("a.jpg", "b.jpg"):
                open(os.path.join(tmp, name), "w").close()
            apply_plan(tmp, [("a.jpg", "x.jpg"), ("b.jpg", "y.jpg")])
            self.assertEqual(
                read_log(tmp),
                [dict(old="a.jpg", new="x.jpg"), dict(old="b.jpg", new="y.jpg")],
            )

    def test_later_logs_keep_earlier_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_log(tmp, [("a.jpg", "x.jpg")])
            write_log(tmp, [("b.jpg", "y.jpg")])
            self.assertEqual([e["old"] for e in read_log(tmp)], ["a.jpg", "b.jpg"])

    def test_failed_apply_writes_no_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                apply_plan(tmp, [("missing.jpg", "x.jpg")])
            self.assertNotIn(LOG_NAME, os.listdir(tmp))

    def test_missing_log_reads_as_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(read_log(tmp), [])


if __name__ == "__main__":
    unittest.main()
