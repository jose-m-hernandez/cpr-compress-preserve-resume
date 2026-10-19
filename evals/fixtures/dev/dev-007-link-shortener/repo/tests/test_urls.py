import unittest

from shortener.urls import check_url


class CheckUrlTests(unittest.TestCase):
    def test_https_is_fine(self):
        self.assertEqual(check_url("https://example.com"), "https://example.com")

    def test_other_schemes_fail(self):
        with self.assertRaises(ValueError):
            check_url("mailto:me@example.com")


if __name__ == "__main__":
    unittest.main()
