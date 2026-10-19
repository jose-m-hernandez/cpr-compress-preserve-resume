import unittest

from mailtpl.footer import FOOTER
from mailtpl.render import MissingValue, placeholders, render


class RenderTests(unittest.TestCase):
    def test_fills_values(self):
        body = render("Hi {name}", {"name": "Ana"})
        self.assertTrue(body.startswith("Hi Ana\n"))

    def test_appends_footer(self):
        self.assertTrue(render("Hi", {}).endswith("\n\n" + FOOTER + "\n"))

    def test_no_footer_when_value_missing(self):
        with self.assertRaises(MissingValue):
            render("Hi {name}", {})

    def test_lists_placeholders(self):
        self.assertEqual(placeholders("{a} and {b}"), ["a", "b"])

    def test_missing_key_raises(self):
        with self.assertRaises(MissingValue) as ctx:
            render("Hi {name}", {})
        self.assertIn("name", str(ctx.exception))

    def test_none_raises(self):
        with self.assertRaises(MissingValue):
            render("Hi {name}", {"name": None})

    def test_empty_and_blank_raise(self):
        for blank in ("", "   "):
            with self.assertRaises(MissingValue):
                render("Hi {name}", {"name": blank})

    def test_falsy_but_real_value_is_kept(self):
        self.assertTrue(render("{n} left", {"n": 0}).startswith("0 left\n"))

    def test_one_missing_among_many_raises(self):
        with self.assertRaises(MissingValue):
            render("{a} {b}", {"a": "x"})


if __name__ == "__main__":
    unittest.main()
