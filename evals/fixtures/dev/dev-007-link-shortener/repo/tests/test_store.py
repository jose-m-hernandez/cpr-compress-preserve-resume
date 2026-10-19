import unittest

from shortener.store import TTL_SECONDS, Store, encode


class StoreTests(unittest.TestCase):
    def test_add_then_get(self):
        store = Store()
        code = store.add("https://example.com/a")
        self.assertEqual(store.get(code), "https://example.com/a")

    def test_codes_count_up_from_zero(self):
        store = Store()
        codes = [store.add("https://example.com/a") for _ in range(3)]
        self.assertEqual(codes, ["000000", "000001", "000002"])

    def test_encode_carries_into_next_digit(self):
        self.assertEqual(encode(35), "00000z")
        self.assertEqual(encode(36), "000010")

    def test_encode_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            encode(36 ** 6)

    def test_unknown_code_is_none(self):
        self.assertIsNone(Store().get("zzzzzz"))

    def test_link_works_just_before_expiry(self):
        now = [1000.0]
        store = Store(clock=lambda: now[0])
        code = store.add("https://example.com/a")
        now[0] += TTL_SECONDS - 1
        self.assertEqual(store.get(code), "https://example.com/a")

    def test_link_expires_after_7_days(self):
        now = [1000.0]
        store = Store(clock=lambda: now[0])
        code = store.add("https://example.com/a")
        now[0] += TTL_SECONDS
        self.assertIsNone(store.get(code))


if __name__ == "__main__":
    unittest.main()
