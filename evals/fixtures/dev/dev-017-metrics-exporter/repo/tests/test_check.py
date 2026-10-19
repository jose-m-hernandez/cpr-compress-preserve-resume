import unittest

from metrics.check import check_names


class CheckNamesTests(unittest.TestCase):
    def test_good_names_pass(self):
        check_names(["counter hits_total"])

    def test_counter_without_suffix_fails(self):
        with self.assertRaises(ValueError):
            check_names(["counter hits"])

    def test_wrong_shape_fails(self):
        with self.assertRaises(ValueError):
            check_names(["counter"])

    def test_name_with_brace_fails(self):
        with self.assertRaises(ValueError):
            check_names(["counter hits_total{path}"])


if __name__ == "__main__":
    unittest.main()
