import contextlib
import io
import os
import tempfile
import unittest

from snap.cli import main
from snap.prune import is_snapshot_name, prune


def stamp(number):
    return "20260502T1015%02d" % number


def make_snapshots(root, count):
    names = [stamp(number) for number in range(count)]
    for name in names:
        os.mkdir(os.path.join(root, name))
    return names


class PruneTests(unittest.TestCase):
    def test_keeps_the_newest(self):
        with tempfile.TemporaryDirectory() as root:
            names = make_snapshots(root, 3)
            self.assertEqual(prune(root, 2), names[:1])
            self.assertEqual(sorted(os.listdir(root)), names[1:])

    def test_default_keeps_ten(self):
        with tempfile.TemporaryDirectory() as root:
            names = make_snapshots(root, 12)
            self.assertEqual(prune(root), names[:2])
            self.assertEqual(sorted(os.listdir(root)), names[2:])

    def test_default_removes_nothing_when_fewer_than_ten(self):
        with tempfile.TemporaryDirectory() as root:
            make_snapshots(root, 9)
            self.assertEqual(prune(root), [])

    def test_stray_folders_and_files_are_never_deleted(self):
        with tempfile.TemporaryDirectory() as root:
            names = make_snapshots(root, 3)
            strays = ["notes", "20260502-101500", "20260502T1015", "z_other_team", "20260502T101500.bak"]
            for name in strays:
                os.mkdir(os.path.join(root, name))
            with open(os.path.join(root, "keep.txt"), "w", encoding="utf-8") as handle:
                handle.write("x")
            self.assertEqual(prune(root, 1), names[:2])
            self.assertEqual(sorted(os.listdir(root)), sorted(strays + ["keep.txt", names[2]]))

    def test_stray_folders_do_not_count_toward_keep(self):
        with tempfile.TemporaryDirectory() as root:
            names = make_snapshots(root, 2)
            os.mkdir(os.path.join(root, "zzz"))
            self.assertEqual(prune(root, 2), [])
            self.assertEqual(sorted(os.listdir(root)), names + ["zzz"])

    def test_snapshot_name_check(self):
        self.assertTrue(is_snapshot_name("20260502T101500"))
        self.assertFalse(is_snapshot_name("20260502-101500"))
        self.assertFalse(is_snapshot_name("20260502T101500\n"))
        self.assertFalse(is_snapshot_name("x20260502T101500"))


class PruneCliTests(unittest.TestCase):
    def run_prune(self, root, *extra):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["prune", root, *extra]), 0)

    def test_keep_defaults_to_ten(self):
        with tempfile.TemporaryDirectory() as root:
            make_snapshots(root, 13)
            self.run_prune(root)
            self.assertEqual(len(os.listdir(root)), 10)

    def test_keep_flag_overrides_default(self):
        with tempfile.TemporaryDirectory() as root:
            names = make_snapshots(root, 10)
            self.run_prune(root, "--keep", "3")
            self.assertEqual(sorted(os.listdir(root)), names[7:])


if __name__ == "__main__":
    unittest.main()
