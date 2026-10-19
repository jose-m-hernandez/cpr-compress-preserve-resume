import json
import os
import tempfile
import unittest

from flags.cache import TTLCache
from flags.store import FlagStore


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = os.path.join(self.dir.name, "flags.json")
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump({"on-flag": True}, handle)

    def test_evaluates_a_defined_flag(self):
        self.assertTrue(FlagStore(self.path).evaluate("on-flag"))

    def test_unknown_flag_evaluates_to_false(self):
        self.assertIs(FlagStore(self.path).evaluate("missing-flag"), False)

    def test_cache_expires_after_the_ttl(self):
        now = [0.0]
        cache = TTLCache(ttl=30, clock=lambda: now[0])
        cache.put("a", True)
        now[0] = 29
        self.assertTrue(cache.get("a"))
        now[0] = 31
        self.assertIsNone(cache.get("a"))


if __name__ == "__main__":
    unittest.main()
