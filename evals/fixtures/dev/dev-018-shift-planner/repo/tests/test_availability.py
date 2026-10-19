import unittest

from rota.availability import parse_availability


class AvailabilityTests(unittest.TestCase):
    def test_reads_days(self):
        self.assertEqual(parse_availability("ana: mon, tue\n"), {"ana": {"mon", "tue"}})

    def test_unknown_day_names_the_line(self):
        with self.assertRaises(ValueError) as caught:
            parse_availability("ana: mon\nbo: funday\n")
        self.assertIn("line 2", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
