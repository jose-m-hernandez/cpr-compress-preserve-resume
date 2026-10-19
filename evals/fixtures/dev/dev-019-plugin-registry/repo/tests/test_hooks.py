import unittest

from plugins.hooks import HOOKS


class HooksTests(unittest.TestCase):
    def test_hook_points_are_before_and_after_run(self):
        self.assertEqual(HOOKS, ("before_run", "after_run"))


if __name__ == "__main__":
    unittest.main()
