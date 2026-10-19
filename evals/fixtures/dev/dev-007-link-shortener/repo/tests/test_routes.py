import unittest

from shortener.routes import handle
from shortener.store import TTL_SECONDS, Store


class RoutesTests(unittest.TestCase):
    def test_shorten_returns_code(self):
        store = Store()
        status, _, code = handle("POST", "/shorten", "https://example.com/a", store)
        self.assertEqual(status, 201)
        self.assertEqual(store.get(code), "https://example.com/a")

    def test_shorten_rejects_bad_url(self):
        status, _, _ = handle("POST", "/shorten", "ftp://x.example/a", Store())
        self.assertEqual(status, 400)

    def test_shorten_rejects_get(self):
        status, headers, _ = handle("GET", "/shorten", "", Store())
        self.assertEqual(status, 405)
        self.assertEqual(headers["Allow"], "POST")

    def test_code_redirects_with_302(self):
        store = Store()
        code = store.add("https://example.com/a")
        status, headers, _ = handle("GET", "/" + code, "", store)
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "https://example.com/a")

    def test_expired_code_is_404(self):
        now = [0.0]
        store = Store(clock=lambda: now[0])
        code = store.add("https://example.com/a")
        now[0] += TTL_SECONDS
        status, _, _ = handle("GET", "/" + code, "", store)
        self.assertEqual(status, 404)

    def test_unknown_code_is_404(self):
        status, _, _ = handle("GET", "/zzzzzz", "", Store())
        self.assertEqual(status, 404)

    def test_root_is_404(self):
        status, _, _ = handle("GET", "/", "", Store())
        self.assertEqual(status, 404)

    def test_post_to_code_is_404(self):
        store = Store()
        code = store.add("https://example.com/a")
        status, _, _ = handle("POST", "/" + code, "", store)
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
