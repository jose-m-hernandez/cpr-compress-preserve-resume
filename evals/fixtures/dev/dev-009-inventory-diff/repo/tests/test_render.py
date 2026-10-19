import json
import unittest

from helpers import sample_differences
from inventory.render import render_json, render_table

DIFFS = sample_differences()


class RenderTests(unittest.TestCase):
    def test_table_has_one_line_per_difference(self):
        lines = render_table(DIFFS)
        self.assertEqual(len(lines), 2)
        self.assertIn("A-1", lines[0])

    def test_json_has_one_object_per_difference(self):
        objects = [json.loads(line) for line in render_json(DIFFS)]
        self.assertEqual(
            objects,
            [
                {"sku": "A-1", "kind": "changed", "old": 1, "new": 9},
                {"sku": "B-1", "kind": "added", "old": None, "new": 3},
            ],
        )

    def test_no_differences_render_nothing(self):
        self.assertEqual(render_json([]), [])
        self.assertEqual(render_table([]), [])


if __name__ == "__main__":
    unittest.main()
