import os
import unittest

from adventure.world import load_world, validate_world

WORLDS = os.path.join(os.path.dirname(__file__), "..", "worlds")


class WorldTests(unittest.TestCase):
    def test_cave_loads(self):
        self.assertIn("gate", load_world(os.path.join(WORLDS, "cave.json"))["rooms"])

    def test_missing_start_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_world({"start": "x", "rooms": {}})


if __name__ == "__main__":
    unittest.main()
