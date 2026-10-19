import json
import threading
import unittest

from factory import make_event
from router.dispatch import dispatch, response_headers
from router.registry import Registry


class DispatchTests(unittest.TestCase):
    def test_known_type_reaches_its_handler(self):
        seen = []
        registry = Registry()
        registry.register("t", seen.append)
        status, _ = dispatch(json.dumps(make_event("t")), registry, now=110)
        self.assertEqual((status, len(seen)), (200, 1))

    def test_handler_runs_in_the_calling_thread(self):
        threads = []
        registry = Registry()
        registry.register("t", lambda event: threads.append(threading.current_thread()))
        dispatch(json.dumps(make_event("t")), registry, now=110)
        self.assertEqual(threads, [threading.current_thread()])

    def test_unknown_type_is_ignored_with_202(self):
        result = dispatch('{"id": "a", "type": "nope", "sent": 100}', Registry(), now=110)
        self.assertEqual(result, (202, {"status": "ignored"}))

    def test_5xx_carries_retry_after_in_seconds(self):
        for status in (500, 503, 599):
            self.assertEqual(response_headers(status), {"Retry-After": "30"})

    def test_non_5xx_has_no_retry_after(self):
        for status in (200, 202, 400, 404, 499):
            self.assertEqual(response_headers(status), {})

    def test_bad_body_is_400(self):
        self.assertEqual(dispatch("{", Registry(), now=0)[0], 400)

    def test_stale_event_is_400(self):
        status, _ = dispatch('{"id": "a", "type": "t", "sent": 0}', Registry(), now=1000)
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
