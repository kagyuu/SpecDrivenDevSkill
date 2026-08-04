import unittest
from datetime import date, timedelta

from app.core.datetime_utils import is_future_or_today, is_upcoming, parse_date, parse_time


class DatetimeUtilsTest(unittest.TestCase):
    def test_parse_date_valid(self):
        self.assertEqual(parse_date("2026-08-10"), date(2026, 8, 10))

    def test_parse_date_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            parse_date("2026/08/10")

    def test_parse_time_valid(self):
        self.assertEqual(parse_time("10:30"), (10, 30))

    def test_parse_time_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            parse_time("10-30")

    def test_is_future_or_today_true_for_today(self):
        today_str = date.today().strftime("%Y-%m-%d")
        self.assertTrue(is_future_or_today(today_str))

    def test_is_future_or_today_true_for_future(self):
        future_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertTrue(is_future_or_today(future_str))

    def test_is_future_or_today_false_for_past(self):
        past_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertFalse(is_future_or_today(past_str))

    def test_is_upcoming_true_for_today_and_future(self):
        today_str = date.today().strftime("%Y-%m-%d")
        self.assertTrue(is_upcoming(today_str))

    def test_is_upcoming_false_for_past(self):
        past_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertFalse(is_upcoming(past_str))


if __name__ == "__main__":
    unittest.main()
