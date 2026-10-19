import unittest

from cronish.errors import ExprError
from cronish.parser import parse, parse_field


class ParserTests(unittest.TestCase):
    def test_star_covers_the_range(self):
        self.assertEqual(parse_field("*", 0, 5, "minute"), {0, 1, 2, 3, 4, 5})

    def test_step_over_a_range(self):
        self.assertEqual(parse_field("10-20/5", 0, 59, "minute"), {10, 15, 20})

    def test_weekday_range_and_list(self):
        self.assertEqual(parse_field("1-5", 0, 6, "weekday"), {1, 2, 3, 4, 5})
        self.assertEqual(parse("0 8 0,1").weekdays, {0, 1})

    def assert_expr_error(self, expr, *words):
        with self.assertRaises(ExprError) as ctx:
            parse(expr)
        for word in words:
            self.assertIn(word, str(ctx.exception))

    def test_expr_error_is_a_value_error(self):
        self.assertTrue(issubclass(ExprError, ValueError))

    def test_three_fields_are_required(self):
        self.assert_expr_error("* *", "3 fields")

    def test_out_of_range_minute(self):
        self.assert_expr_error("61 * *", "minute")

    def test_out_of_range_hour(self):
        self.assert_expr_error("0 24 *", "hour")

    def test_non_numeric_value_names_the_field(self):
        self.assert_expr_error("* abc *", "hour", "abc")

    def test_bad_step_names_the_field(self):
        self.assert_expr_error("*/0 * *", "minute", "step")
        self.assert_expr_error("* * */x", "weekday", "step")

    def test_weekday_seven_is_rejected(self):
        self.assert_expr_error("0 0 7", "weekday")


if __name__ == "__main__":
    unittest.main()
