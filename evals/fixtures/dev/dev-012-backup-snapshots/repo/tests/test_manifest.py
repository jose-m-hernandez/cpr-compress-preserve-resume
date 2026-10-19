import json
import os
import tempfile
import unittest

from snap.manifest import MANIFEST_NAME, build_manifest, write_manifest
from snap.snapshot import snapshot


def make_file(root, rel, text):
    path = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


class ManifestTests(unittest.TestCase):
    def test_lists_paths_with_sizes_sorted(self):
        with tempfile.TemporaryDirectory() as root:
            make_file(root, "sub/b.txt", "bbb")
            make_file(root, "a.txt", "a")
            self.assertEqual(
                build_manifest(root),
                [{"path": "a.txt", "size": 1}, {"path": "sub/b.txt", "size": 3}],
            )

    def test_write_manifest_excludes_itself(self):
        with tempfile.TemporaryDirectory() as root:
            make_file(root, "a.txt", "a")
            path = write_manifest(root)
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(data, {"files": [{"path": "a.txt", "size": 1}]})

    def test_snapshot_contains_manifest(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dest:
            make_file(src, "f.txt", "xy")
            target = snapshot(src, dest, "20260502T101500")
            with open(os.path.join(target, MANIFEST_NAME), encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(data["files"], [{"path": "f.txt", "size": 2}])

    def test_distinct_stamps_make_distinct_snapshots_without_sleeping(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dest:
            make_file(src, "f.txt", "x")
            first = snapshot(src, dest, "20260502T101500")
            second = snapshot(src, dest, "20260502T101501")
            self.assertNotEqual(first, second)
            self.assertEqual(sorted(os.listdir(dest)), ["20260502T101500", "20260502T101501"])


if __name__ == "__main__":
    unittest.main()
