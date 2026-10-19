import os
import tempfile
import unittest

from etl.load import load_sales


class LoadTests(unittest.TestCase):
    def test_unit_price_converted_from_cents_to_dollars(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "sales.csv")
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write("date,sku,quantity,unit_price\n")
                handle.write("2025-01-03,A100,2,1250\n")
                handle.write("2025-01-04,B200,1,999\n")
            sales = load_sales(path)
        self.assertEqual(sales[0]["unit_price"], 12.5)
        self.assertAlmostEqual(sales[1]["unit_price"], 9.99)
        self.assertEqual(sales[0]["quantity"], 2)


if __name__ == "__main__":
    unittest.main()
