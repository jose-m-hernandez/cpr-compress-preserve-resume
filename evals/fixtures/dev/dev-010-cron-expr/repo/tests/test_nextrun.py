import unittest
from datetime import datetime

from cronish.nextrun import cron_weekday, next_run
from cronish.parser import Schedule, parse


class NextRunTests(unittest.TestCase):
    def test_cron_weekday_numbers_sunday_as_zero(self):
        self.assertEqual(cron_weekday(datetime(2026, 10, 18)), 0)  # Sunday
        self.assertEqual(cron_weekday(datetime(2026, 10, 19)), 1)  # Monday

    def test_next_minute_when_every_minute(self):
        self.assertEqual(next_run(parse("* * *"), datetime(2026, 10, 17, 22, 46)),
                         datetime(2026, 10, 17, 22, 47))

    def test_result_is_strictly_after(self):
        after = datetime(2026, 10, 17, 9, 30)
        self.assertEqual(next_run(parse("30 9 *"), after),
                         datetime(2026, 10, 18, 9, 30))

    def test_seconds_are_dropped(self):
        after = datetime(2026, 10, 17, 9, 29, 45, 123)
        self.assertEqual(next_run(parse("30 9 *"), after),
                         datetime(2026, 10, 17, 9, 30))

    def test_rolls_to_the_next_hour(self):
        self.assertEqual(next_run(parse("5 * *"), datetime(2026, 10, 17, 9, 30)),
                         datetime(2026, 10, 17, 10, 5))

    def test_rolls_over_midnight_and_year(self):
        self.assertEqual(next_run(parse("0 0 *"), datetime(2026, 12, 31, 12, 0)),
                         datetime(2027, 1, 1, 0, 0))

    def test_skips_to_the_matching_weekday(self):
        # 2026-10-17 is a Saturday; weekdays 1-5 means Monday to Friday.
        self.assertEqual(next_run(parse("*/15 9-17 1-5"), datetime(2026, 10, 17, 12, 0)),
                         datetime(2026, 10, 19, 9, 0))

    def test_sunday_is_zero(self):
        self.assertEqual(next_run(parse("0 8 0"), datetime(2026, 10, 17, 12, 0)),
                         datetime(2026, 10, 18, 8, 0))

    def test_empty_field_raises(self):
        with self.assertRaises(ValueError):
            next_run(Schedule(set(), {0}, {0}), datetime(2026, 10, 17))


if __name__ == "__main__":
    unittest.main()
