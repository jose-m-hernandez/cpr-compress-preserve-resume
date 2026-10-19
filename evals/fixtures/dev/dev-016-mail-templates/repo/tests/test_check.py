import unittest

from mailtpl.check import check_subject_length, check_template


class CheckTests(unittest.TestCase):
    def test_good_template_passes(self):
        check_template("Subject: Hi\nHello {name}\n")

    def test_missing_subject_fails(self):
        with self.assertRaises(ValueError):
            check_template("Hello {name}\n")

    def test_unknown_placeholder_fails(self):
        with self.assertRaises(ValueError):
            check_template("Subject: Hi\n{nope}\n")

    def test_subject_at_limit_passes(self):
        check_template("Subject: " + "a" * 60 + "\nHello {name}\n")

    def test_subject_over_limit_fails(self):
        with self.assertRaises(ValueError) as ctx:
            check_template("Subject: " + "a" * 61 + "\nHello {name}\n")
        self.assertIn("61", str(ctx.exception))

    def test_check_subject_length_ignores_body(self):
        check_subject_length("Subject: Hi\n" + "a" * 100 + "\n")


if __name__ == "__main__":
    unittest.main()
