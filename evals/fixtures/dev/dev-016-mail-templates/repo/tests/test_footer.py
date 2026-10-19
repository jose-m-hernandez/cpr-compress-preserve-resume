import unittest

from mailtpl.footer import FOOTER, add_footer


class FooterTests(unittest.TestCase):
    def test_footer_text(self):
        self.assertEqual(FOOTER, "Use the link to unsubscribe")

    def test_appends_after_blank_line(self):
        self.assertEqual(add_footer("Hi"), "Hi\n\nUse the link to unsubscribe\n")

    def test_trailing_newlines_do_not_pile_up(self):
        self.assertEqual(add_footer("Hi\n\n\n"), add_footer("Hi"))


if __name__ == "__main__":
    unittest.main()
