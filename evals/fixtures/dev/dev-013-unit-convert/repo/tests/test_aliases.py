import unittest

from units.aliases import ALIASES, resolve
from units.convert import convert
from units.table import FACTORS, TEMPERATURE


class AliasTests(unittest.TestCase):
    def test_spellings_resolve_to_canonical_unit(self):
        for name in ("m", "metre", "meter", "metres", "meters"):
            self.assertEqual(resolve(name), "m")

    def test_matching_is_case_insensitive(self):
        self.assertEqual(resolve("Metre"), "m")
        self.assertEqual(resolve("KM"), "km")
        self.assertEqual(resolve("Feet"), "ft")

    def test_unknown_name_is_returned_unchanged(self):
        self.assertEqual(resolve("Furlong"), "Furlong")

    def test_temperature_units_keep_their_case(self):
        self.assertEqual(resolve("celsius"), "C")
        self.assertEqual(resolve("c"), "C")

    def test_every_unit_has_an_alias_entry(self):
        for unit in (*FACTORS, *TEMPERATURE):
            self.assertEqual(ALIASES[unit.lower()], unit)

    def test_convert_accepts_aliases(self):
        self.assertEqual(convert(2, "Kilometres", "meter"), 2000.0)
        self.assertEqual(convert(1, "MILE", "km"), 1.60934)

    def test_temperature_alias_is_still_rejected(self):
        with self.assertRaises(ValueError):
            convert(1, "celsius", "fahrenheit")


if __name__ == "__main__":
    unittest.main()
