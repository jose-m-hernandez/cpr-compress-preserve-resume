import unittest

from notes_api.validation import MAX_TITLE, validate_title


class ValidateTitleTests(unittest.TestCase):
    def test_accepts_title_at_max_length(self):
        validate_title("x" * MAX_TITLE)

    def test_rejects_title_over_max_length(self):
        with self.assertRaisesRegex(ValueError, "title too long"):
            validate_title("x" * (MAX_TITLE + 1))


if __name__ == "__main__":
    unittest.main()
