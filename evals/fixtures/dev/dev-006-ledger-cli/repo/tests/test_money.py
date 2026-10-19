import unittest

from ledger.money import format_cents, to_cents


class MoneyTests(unittest.TestCase):
    def test_to_cents_is_exact(self):
        self.assertEqual(to_cents("42.50"), 4250)
        self.assertEqual(to_cents("0.1"), 10)
        self.assertEqual(to_cents("7"), 700)
        self.assertEqual(to_cents("1.0"), 100)

    def test_too_many_decimals_is_rejected(self):
        with self.assertRaises(ValueError):
            to_cents("1.005")

    def test_garbage_is_rejected(self):
        for text in ("", ".", "abc", "1e3", "nan"):
            with self.assertRaises(ValueError):
                to_cents(text)

    def test_format_cents(self):
        self.assertEqual(format_cents(4250), "42.50")
        self.assertEqual(format_cents(5), "0.05")
        self.assertEqual(format_cents(-250), "-2.50")

    def test_sums_do_not_drift(self):
        self.assertEqual(sum(to_cents("0.10") for _ in range(10)), 100)


if __name__ == "__main__":
    unittest.main()
