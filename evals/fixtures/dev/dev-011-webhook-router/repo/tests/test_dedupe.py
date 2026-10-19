import json
import unittest

from factory import make_event
from router.dedupe import SeenIds
from router.dispatch import dispatch
from router.registry import Registry


class SeenIdsTests(unittest.TestCase):
    def test_second_claim_is_refused(self):
        seen = SeenIds()
        self.assertEqual((seen.claim("a"), seen.claim("a")), (True, False))

    def test_oldest_id_is_evicted_past_capacity(self):
        seen = SeenIds(capacity=2)
        for event_id in ("a", "b", "c"):
            seen.claim(event_id)
        self.assertEqual((seen.claim("a"), seen.claim("c")), (True, False))

    def test_default_capacity_is_5000(self):
        seen = SeenIds()
        for number in range(5000):
            seen.claim(number)
        self.assertFalse(seen.claim(0))
        seen.claim("one more")
        self.assertEqual((seen.claim(0), seen.claim(2)), (True, False))

    def test_released_id_can_be_claimed_again(self):
        seen = SeenIds()
        seen.claim("a")
        seen.release("a")
        self.assertTrue(seen.claim("a"))


class DispatchDedupeTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.registry = Registry()
        self.registry.register("t", self.calls.append)
        self.seen = SeenIds()

    def send(self, event):
        return dispatch(json.dumps(event), self.registry, now=110, seen=self.seen)

    def test_repeat_is_duplicate_and_handled_once(self):
        event = make_event("t")
        first, second = self.send(event), self.send(event)
        self.assertEqual(
            (first, second, len(self.calls)),
            ((200, {"status": "ok"}), (200, {"status": "duplicate"}), 1),
        )

    def test_failed_handler_can_be_retried(self):
        def boom(event):
            raise RuntimeError("boom")

        self.registry.register("bad", boom)
        event = make_event("bad")
        with self.assertRaises(RuntimeError):
            self.send(event)
        self.registry.register("bad", self.calls.append)
        self.assertEqual(self.send(event)[1], {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
