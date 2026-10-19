import unittest

from helpers import write_stock
from inventory.loader import load_stock


class LoaderTests(unittest.TestCase):
    def test_reads_a_valid_list(self):
        self.assertEqual(load_stock(write_stock(self, {"A-1": 2})), {"A-1": 2})

    def test_bad_sku_is_rejected(self):
        with self.assertRaises(ValueError):
            load_stock(write_stock(self, {"nope": 1}))


if __name__ == "__main__":
    unittest.main()
