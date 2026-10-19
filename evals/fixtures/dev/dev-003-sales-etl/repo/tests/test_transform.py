import unittest

from etl.transform import revenue_by_sku


class RevenueTests(unittest.TestCase):
    def test_sums_per_sku(self):
        sales = [
            {"sku": "A", "quantity": 2, "unit_price": 3.0},
            {"sku": "A", "quantity": 1, "unit_price": 3.0},
            {"sku": "B", "quantity": 1, "unit_price": 5.0},
        ]
        self.assertEqual(revenue_by_sku(sales), {"A": 9.0, "B": 5.0})

    def test_dollar_prices_not_rounded_per_row(self):
        sales = [
            {"sku": "A", "quantity": 3, "unit_price": 0.333},
            {"sku": "A", "quantity": 3, "unit_price": 0.333},
            {"sku": "B", "quantity": 2, "unit_price": 19.99},
        ]
        totals = revenue_by_sku(sales)
        # Per-row rounding would give 2.00 for A; the unrounded sum is 1.998.
        self.assertAlmostEqual(totals["A"], 1.998)
        self.assertAlmostEqual(totals["B"], 39.98)


if __name__ == "__main__":
    unittest.main()
