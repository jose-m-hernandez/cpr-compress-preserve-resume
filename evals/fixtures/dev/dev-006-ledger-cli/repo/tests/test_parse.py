import unittest

from ledger.parse import parse_line


class ParseLineTests(unittest.TestCase):
    def test_reads_four_fields(self):
        entry = parse_line("2026-03-02 | weekly shop | 42.50 | food", 1)
        self.assertEqual(entry.category, "food")
        self.assertEqual(entry.amount, 4250)

    def test_wrong_field_count_names_the_line(self):
        with self.assertRaises(ValueError) as caught:
            parse_line("2026-03-02 | weekly shop", 7)
        self.assertIn("line 7", str(caught.exception))

    def test_negative_amount_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_line("2026-03-02 | return | -5 | misc", 2)

    def test_bad_date_names_the_line(self):
        with self.assertRaises(ValueError) as caught:
            parse_line("March 2 | weekly shop | 1.00 | food", 4)
        self.assertIn("line 4", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
