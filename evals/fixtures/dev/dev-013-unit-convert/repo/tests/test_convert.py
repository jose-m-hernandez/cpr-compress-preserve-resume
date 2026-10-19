import unittest

from units.convert import convert


class ConvertTests(unittest.TestCase):
    def test_kilometres_to_metres(self):
        self.assertEqual(convert(2, "km", "m"), 2000.0)

    def test_result_is_rounded_to_6_significant_digits(self):
        self.assertEqual(convert(1, "mi", "km"), 1.60934)
        self.assertEqual(convert(1, "m", "mi"), 0.000621371)

    def test_float_noise_is_removed(self):
        self.assertEqual(convert(0.1, "ft", "m"), 0.03048)
        self.assertEqual(convert(0.3, "ft", "m"), 0.09144)

    def test_pound_uses_the_exact_international_factor(self):
        self.assertEqual(convert(1, "lb", "kg"), 0.453592)
        self.assertEqual(convert(0.1, "lb", "g"), 45.3592)
        self.assertEqual(convert(1000, "lb", "kg"), 453.592)

    def test_dimension_mismatch_is_an_error(self):
        with self.assertRaises(ValueError):
            convert(1, "km", "kg")

    def test_unknown_unit_is_an_error(self):
        with self.assertRaises(ValueError):
            convert(1, "furlong", "m")

    def test_temperature_is_not_supported(self):
        with self.assertRaises(ValueError):
            convert(1, "C", "F")


if __name__ == "__main__":
    unittest.main()
