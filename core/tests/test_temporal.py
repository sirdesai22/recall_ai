import unittest
import datetime
from temporal import parse_time_range, strip_time_expression


def midnight():
    return datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


class TestToday(unittest.TestCase):
    def test_today_range(self):
        now = datetime.datetime.now()
        result = parse_time_range("what was I reading today")
        self.assertIsNotNone(result)
        start, end = result
        self.assertEqual(
            datetime.datetime.fromtimestamp(start), midnight()
        )
        self.assertGreaterEqual(end, now.timestamp() - 5)

    def test_case_insensitive(self):
        self.assertIsNotNone(parse_time_range("TODAY"))

    def test_no_time_expression(self):
        self.assertIsNone(parse_time_range("find rate limiting"))


class TestYesterday(unittest.TestCase):
    def test_yesterday_is_24h_ending_at_midnight(self):
        result = parse_time_range("what did I read yesterday")
        start, end = result
        self.assertEqual(end - start, 86400)
        self.assertEqual(datetime.datetime.fromtimestamp(end), midnight())

    def test_yesterday_does_not_match_today(self):
        # "today" must not be swallowed by "yesterday" matching
        r1 = parse_time_range("today")
        r2 = parse_time_range("yesterday")
        self.assertNotEqual(r1[0], r2[0])


class TestLastWeekday(unittest.TestCase):
    def test_last_tuesday_is_a_tuesday(self):
        start, end = parse_time_range("what was I reading last tuesday")
        d = datetime.datetime.fromtimestamp(start)
        self.assertEqual(d.weekday(), 1)  # monday=0 ... tuesday=1
        self.assertEqual(d.hour, 0)
        self.assertEqual((end - start) / 86400, 1.0)

    def test_last_friday_is_a_friday(self):
        start, _ = parse_time_range("last friday")
        self.assertEqual(datetime.datetime.fromtimestamp(start).weekday(), 4)

    def test_last_today_weekday_goes_back_seven_days(self):
        today_name = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][
            datetime.datetime.now().weekday()
        ]
        start, end = parse_time_range(f"last {today_name}")
        self.assertEqual((end - start) / 86400, 1.0)
        expected_start = midnight() - datetime.timedelta(days=7)
        self.assertEqual(datetime.datetime.fromtimestamp(start), expected_start)


class TestWeekRanges(unittest.TestCase):
    def test_this_week_starts_monday(self):
        start, end = parse_time_range("this week")
        self.assertEqual(datetime.datetime.fromtimestamp(start).weekday(), 0)

    def test_last_week_spans_previous_mon_to_sun(self):
        start, end = parse_time_range("last week")
        s = datetime.datetime.fromtimestamp(start)
        e = datetime.datetime.fromtimestamp(end)
        self.assertEqual(s.weekday(), 0)
        self.assertEqual((e - s).days, 7)

    def test_this_morning_ends_at_noon(self):
        start, end = parse_time_range("this morning")
        noon = datetime.datetime.fromtimestamp(end)
        self.assertEqual(noon.hour, 12)
        self.assertEqual(noon.minute, 0)


class TestStripTimeExpression(unittest.TestCase):
    def test_removes_expression(self):
        self.assertEqual(strip_time_expression("what was I reading yesterday"), "what was I reading")

    def test_collapses_whitespace(self):
        self.assertEqual(strip_time_expression("show   me  last friday stuff"), "show me stuff")

    def test_preserves_non_temporal_query(self):
        self.assertEqual(strip_time_expression("rate limiting in go"), "rate limiting in go")


if __name__ == "__main__":
    unittest.main()
