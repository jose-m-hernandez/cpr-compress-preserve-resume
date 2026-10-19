import json
import os
import tempfile
import unittest

from flags.loader import load_flags


class LoaderTests(unittest.TestCase):
    def test_loads_flags_from_a_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "flags.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"on-flag": True, "off-flag": False}, handle)
            self.assertEqual(load_flags(path), {"on-flag": True, "off-flag": False})


if __name__ == "__main__":
    unittest.main()
