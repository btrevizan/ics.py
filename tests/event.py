import unittest
import pytest
from datetime import datetime, timedelta as td, datetime as dt
import arrow
from ics.event import Event
from ics.repeatable import Repeatable
from ics.icalendar import Calendar
from ics.parse import Container
from .fixture import cal12, cal13, cal15, cal16, cal17, cal18, cal19, cal20, cal32

CRLF = "\r\n"


class TestEvent(unittest.TestCase):

    def test_event(self):
        e = Event(begin=0, end=20)
        self.assertEqual(e.begin.timestamp, 0)
        self.assertEqual(e.end.timestamp, 20)
        self.assertTrue(e.has_end())
        self.assertFalse(e.all_day)

        f = Event(begin=10, end=30)
        self.assertTrue(e < f)
        self.assertTrue(e <= f)
        self.assertTrue(f > e)
        self.assertTrue(f >= e)

    def test_or(self):
        g = Event(begin=0, end=10) | Event(begin=10, end=20)
        self.assertEqual(g, (None, None))

        g = Event(begin=0, end=20) | Event(begin=10, end=30)
        self.assertEqual(tuple(map(lambda x: x.timestamp, g)), (10, 20))

        g = Event(begin=0, end=20) | Event(begin=5, end=15)
        self.assertEqual(tuple(map(lambda x: x.timestamp, g)), (5, 15))

        g = Event() | Event()
        self.assertEqual(g, (None, None))

    def test_event_with_duration(self):
        c = Calendar(cal12)
        e = next(iter(c.events))
        self.assertEqual(e._duration, td(1, 3600))
        self.assertEqual(e.end - e.begin, td(1, 3600))

    def test_not_duration_and_end(self):
        with self.assertRaises(ValueError):
            Calendar(cal13)

    def test_duration_output(self):
        e = Event(begin=0, duration=td(1, 23))
        lines = str(e).splitlines()
        self.assertIn('DTSTART:19700101T000000Z', lines)
        self.assertIn('DURATION:P1DT23S', lines)

    def test_make_all_day(self):
        e = Event(begin=0, end=20)
        begin = e.begin
        e.make_all_day()
        self.assertEqual(e.begin, begin)
        self.assertEqual(e._end_time, None)
        self.assertEqual(e._duration, None)

    def test_make_all_day2(self):
        e = Event(begin="1993/05/24")
        begin = arrow.get("1993/05/24")

        self.assertEqual(e._begin, begin)
        self.assertEqual(e.begin, begin)

        self.assertEqual(e._end_time, None)
        self.assertEqual(e.end, begin)

        e.make_all_day()

        self.assertEqual(e._begin, begin)
        self.assertEqual(e.begin, begin)
        self.assertEqual(e._begin_precision, "day")

        self.assertEqual(e._end_time, None)
        self.assertEqual(e.end, arrow.get("1993/05/25"))

    def test_init_duration_end(self):
        with self.assertRaises(ValueError):
            Event(name="plop", begin=0, end=10, duration=1)

    def test_end_before_begin(self):
        e = Event(begin="2013/10/10")
        with self.assertRaises(ValueError):
            e.end = "1999/10/10"

    def test_begin_after_end(self):
        e = Event(end="19991010")
        with self.assertRaises(ValueError):
            e.begin = "2013/10/10"

    def test_end_with_prescision(self):
        e = Event(begin="1999/10/10")
        e._begin_precision = "day"
        self.assertEqual(e.end, arrow.get("1999/10/11"))

    def test_plain_repr(self):
        self.assertEqual(repr(Event()), "<Event>")

    def test_all_day_repr(self):
        e = Event(name='plop', begin="1999/10/10")
        e.make_all_day()
        self.assertEqual(repr(e), "<all-day Event 'plop' 1999-10-10>")

    def test_name_repr(self):
        e = Event(name='plop')
        self.assertEqual(repr(e), "<Event 'plop'>")

    def test_repr(self):
        e = Event(name='plop', begin="1999/10/10")
        self.assertEqual(repr(e), "<Event 'plop' begin:1999-10-10T00:00:00+00:00 end:1999-10-10T00:00:00+00:00>")

    def test_init(self):
        e = Event()

        self.assertEqual(e._duration, None)
        self.assertEqual(e._end_time, None)
        self.assertEqual(e._begin, None)
        self.assertEqual(e._begin_precision, 'second')
        self.assertNotEqual(e.uid, None)
        self.assertEqual(e.description, None)
        self.assertEqual(e.created, None)
        self.assertEqual(e.location, None)
        self.assertEqual(e.url, None)
        self.assertEqual(e._unused, Container(name='VEVENT'))
        self.assertEqual(e.status, None)

    def test_has_end(self):
        e = Event()
        self.assertFalse(e.has_end())
        e = Event(begin="1993/05/24", duration=10)
        self.assertTrue(e.has_end())
        e = Event(begin="1993/05/24", end="1999/10/11")
        self.assertTrue(e.has_end())
        e = Event(begin="1993/05/24")
        e.make_all_day()
        self.assertFalse(e.has_end())

    def test_duration(self):
        e = Event()
        self.assertIsNone(e.duration)

        e1 = Event(begin="1993/05/24")
        e1.make_all_day()
        self.assertEqual(e1.duration, td(days=1))

        e2 = Event(begin="1993/05/24", end="1993/05/30")
        self.assertEqual(e2.duration, td(days=6))

        e3 = Event(begin="1993/05/24", duration=td(minutes=1))
        self.assertEqual(e3.duration, td(minutes=1))

        e4 = Event(begin="1993/05/24")
        self.assertEqual(e4.duration, td(0))

        e5 = Event(begin="1993/05/24")
        e5.duration = {'days': 6, 'hours': 2}
        self.assertEqual(e5.end, arrow.get("1993-05-30T02:00"))
        self.assertEqual(e5.duration, td(hours=146))

    def test_always_uid(self):
        e = Event()
        e.uid = None
        self.assertIn('UID:', str(e))

    def test_cmp_other(self):
        with self.assertRaises(NotImplementedError):
            Event() < 1
        with self.assertRaises(NotImplementedError):
            Event() > 1
        with self.assertRaises(NotImplementedError):
            Event() <= 1
        with self.assertRaises(NotImplementedError):
            Event() >= 1

    def test_cmp_by_name(self):
        self.assertGreater(Event(name="z"), Event(name="a"))
        self.assertGreaterEqual(Event(name="z"), Event(name="a"))
        self.assertGreaterEqual(Event(name="m"), Event(name="m"))

        self.assertLess(Event(name="a"), Event(name="z"))
        self.assertLessEqual(Event(name="a"), Event(name="z"))
        self.assertLessEqual(Event(name="m"), Event(name="m"))

    def test_cmp_by_name_fail(self):
        self.assertFalse(Event(name="a") > Event(name="z"))
        self.assertFalse(Event(name="a") >= Event(name="z"))

        self.assertFalse(Event(name="z") < Event(name="a"))
        self.assertFalse(Event(name="z") <= Event(name="a"))

    def test_cmp_by_name_fail_not_equal(self):
        self.assertFalse(Event(name="a") > Event(name="a"))
        self.assertFalse(Event(name="b") < Event(name="b"))

    def test_cmp_by_start_time(self):
        ev1 = Event(begin=datetime(2018, 6, 29, 6))
        ev2 = Event(begin=datetime(2018, 6, 29, 7))
        self.assertLess(ev1, ev2)
        self.assertGreaterEqual(ev2, ev1)
        self.assertLessEqual(ev1, ev2)
        self.assertGreater(ev2, ev1)

    def test_cmp_by_start_time_with_end_time(self):
        ev1 = Event(begin=datetime(2018, 6, 29, 5), end=datetime(2018, 6, 29, 7))
        ev2 = Event(begin=datetime(2018, 6, 29, 6), end=datetime(2018, 6, 29, 8))
        ev3 = Event(begin=datetime(2018, 6, 29, 6))
        self.assertLess(ev1, ev2)
        self.assertGreaterEqual(ev2, ev1)
        self.assertLessEqual(ev1, ev2)
        self.assertGreater(ev2, ev1)
        self.assertLess(ev3, ev2)
        self.assertGreaterEqual(ev2, ev3)
        self.assertLessEqual(ev3, ev2)
        self.assertGreater(ev2, ev3)

    def test_cmp_by_end_time(self):
        ev1 = Event(begin=datetime(2018, 6, 29, 6), end=datetime(2018, 6, 29, 7))
        ev2 = Event(begin=datetime(2018, 6, 29, 6), end=datetime(2018, 6, 29, 8))
        self.assertLess(ev1, ev2)
        self.assertGreaterEqual(ev2, ev1)
        self.assertLessEqual(ev1, ev2)
        self.assertGreater(ev2, ev1)

    def test_unescape_summary(self):
        c = Calendar(cal15)
        e = next(iter(c.events))
        self.assertEqual(e.name, "Hello, \n World; This is a backslash : \\ and another new \n line")

    def test_unescapte_texts(self):
        c = Calendar(cal17)
        e = next(iter(c.events))
        self.assertEqual(e.name, "Some special ; chars")
        self.assertEqual(e.location, "In, every text field")
        self.assertEqual(e.description, "Yes, all of them;")

    def test_escape_output(self):
        e = Event()

        e.name = "Hello, with \\ special; chars and \n newlines"
        e.location = "Here; too"
        e.description = "Every\nwhere ! Yes, yes !"
        e.created = arrow.Arrow(2013, 1, 1)
        e.uid = "empty-uid"

        eq = CRLF.join(("BEGIN:VEVENT",
                "DTSTAMP:20130101T000000Z",
                "SUMMARY:Hello\\, with \\\\ special\\; chars and \\n newlines",
                "DESCRIPTION:Every\\nwhere ! Yes\\, yes !",
                "LOCATION:Here\\; too",
                "TRANSP:OPAQUE",
                "UID:empty-uid",
                "END:VEVENT"))
        self.assertEqual(str(e), eq)

    def test_url_input(self):
        c = Calendar(cal16)
        e = next(iter(c.events))
        self.assertEqual(e.url, "http://example.com/pub/calendars/jsmith/mytime.ics")

    def test_url_output(self):
        URL = "http://example.com/pub/calendars/jsmith/mytime.ics"
        e = Event(name="Name", url=URL)
        self.assertIn("URL:" + URL, str(e).splitlines())

    def test_status_input(self):
        c = Calendar(cal16)
        e = next(iter(c.events))
        self.assertEqual(e.status, "CONFIRMED")

    def test_status_output(self):
        STATUS = "CONFIRMED"
        e = Event(name="Name", status=STATUS)
        self.assertIn("STATUS:" + STATUS, str(e).splitlines())

    def test_category_input(self):
        c = Calendar(cal16)
        e = next(iter(c.events))
        self.assertIn("Simple Category", e.categories)
        self.assertIn("My \"Quoted\" Category", e.categories)
        self.assertIn("Category, with comma", e.categories)

    def test_category_output(self):
        cat = "Simple category"
        e = Event(name="Name", categories={cat})
        self.assertIn("CATEGORIES:" + cat, str(e).splitlines())

    def test_all_day_with_end(self):
        c = Calendar(cal20)
        e = next(iter(c.events))
        self.assertTrue(e.all_day)

    def test_not_all_day(self):
        c = Calendar(cal16)
        e = next(iter(c.events))
        self.assertFalse(e.all_day)

    def test_all_day_duration(self):
        c = Calendar(cal20)
        e = next(iter(c.events))
        self.assertTrue(e.all_day)
        self.assertEqual(e.duration, td(days=2))

    def test_make_all_day_idempotence(self):
        c = Calendar(cal18)
        e = next(iter(c.events))
        self.assertFalse(e.all_day)
        e2 = e.clone()
        e2.make_all_day()
        self.assertTrue(e2.all_day)
        self.assertNotEqual(e.begin, e2.begin)
        self.assertNotEqual(e.end, e2.end)
        e3 = e2.clone()
        e3.make_all_day()
        self.assertEqual(e2.begin, e3.begin)
        self.assertEqual(e2.end, e3.end)

    def test_all_day_outputs_dtstart_value_date(self):
        """All day events should output DTSTART using VALUE=DATE without
        time and timezone in order to assume the user's current timezone

        refs http://www.kanzaki.com/docs/ical/dtstart.html
             http://www.kanzaki.com/docs/ical/date.html
        """
        e = Event(begin="2015/12/21")
        e.make_all_day()
        # no time or tz specifier
        self.assertIn('DTSTART;VALUE=DATE:20151221', str(e).splitlines())

    def test_transparent_input(self):
        c = Calendar(cal19)
        e = next(iter(c.events))
        self.assertEqual(e.transparent, False)

    def test_transparent_output(self):
        TRANSPARENT = True
        e = Event(name="Name", transparent=TRANSPARENT)
        self.assertIn("TRANSP:TRANSPARENT", str(e).splitlines())

    def test_default_transparent_input(self):
        c = Calendar(cal18)
        e = next(iter(c.events))
        self.assertEqual(e.transparent, False)

    def test_default_transparent_output(self):
        e = Event(name="Name")
        self.assertIn("TRANSP:OPAQUE", str(e).splitlines())

    def test_includes_disjoined(self):
        # disjoined events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=20))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 50), duration=td(minutes=20))
        assert not event_a.includes(event_b)
        assert not event_b.includes(event_a)

    def test_includes_intersected(self):
        # intersected events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 30), duration=td(minutes=30))
        assert not event_a.includes(event_b)
        assert not event_b.includes(event_a)

        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 30), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        assert not event_a.includes(event_b)
        assert not event_b.includes(event_a)

    def test_includes_included(self):
        # included events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 00), duration=td(minutes=60))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        assert event_a.includes(event_b)
        assert not event_b.includes(event_a)

        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 00), duration=td(minutes=60))
        assert not event_a.includes(event_b)
        assert event_b.includes(event_a)

    def test_intersects_disjoined(self):
        # disjoined events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=20))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 50), duration=td(minutes=20))
        assert not event_a.intersects(event_b)
        assert not event_b.intersects(event_a)

    def test_intersects_intersected(self):
        # intersected events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 30), duration=td(minutes=30))
        assert event_a.intersects(event_b)
        assert event_b.intersects(event_a)

        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 30), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        assert event_a.intersects(event_b)
        assert event_b.intersects(event_a)

    def test_intersects_included(self):
        # included events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 00), duration=td(minutes=60))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        assert event_a.intersects(event_b)
        assert event_b.intersects(event_a)

        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 00), duration=td(minutes=60))
        assert event_a.intersects(event_b)
        assert event_b.intersects(event_a)

    def test_join_disjoined(self):
        # disjoined events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=20))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 50), duration=td(minutes=20))
        with pytest.raises(ValueError):
            event_a.join(event_b)
        with pytest.raises(ValueError):
            event_b.join(event_a)

    def test_join_intersected(self):
        # intersected events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 30), duration=td(minutes=30))
        assert event_a.join(event_b).time_equals(Event(name=None, begin=event_a.begin, end=event_b.end))
        assert event_b.join(event_a).time_equals(Event(name=None, begin=event_a.begin, end=event_b.end))

        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 30), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        assert event_a.join(event_b).time_equals(Event(name=None, begin=event_b.begin, end=event_a.end))
        assert event_b.join(event_a).time_equals(Event(name=None, begin=event_b.begin, end=event_a.end))

    def test_join_included(self):
        # included events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 00), duration=td(minutes=60))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        assert event_a.join(event_b).time_equals(Event(name=None, begin=event_a.begin, end=event_a.end))
        assert event_b.join(event_a).time_equals(Event(name=None, begin=event_a.begin, end=event_a.end))

        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 00), duration=td(minutes=60))
        assert event_a.join(event_b).time_equals(Event(name=None, begin=event_b.begin, end=event_b.end))
        assert event_b.join(event_a).time_equals(Event(name=None, begin=event_b.begin, end=event_b.end))

        event = Event(uid='0', name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        event.join(event)
        assert event == Event(uid='0', name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))

    def test_issue_92(self):
        c = Calendar(cal32)
        e = list(c.events)[0]

        assert e.begin == arrow.get('2016-10-04')
        assert e.end == arrow.get('2016-10-05')

    def test_no_repeat(self):
        event = Event(name="Test repeatable #1", begin=dt(2019, 1, 14, 13, 30), duration=td(minutes=60))
        for e in event.repeat():
            self.assertEqual(e, event)

    def test_repeat_daily(self):
        repeatable = Repeatable("DAILY", count=3, interval=2)
        event = Event(name="Test repeatable #1", begin=dt(2019, 1, 14, 13, 30), duration=td(minutes=60),
                      rrule=repeatable)

        events = [event,
                  Event(name="Test repeatable #1", begin=dt(2019, 1, 16, 13, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2019, 1, 18, 13, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2019, 1, 20, 13, 30), duration=td(minutes=60),
                        rrule=repeatable)]

        i = 0
        for e in event.repeat():
            self.assertTrue(e.time_equals(events[i]))
            i += 1

    def test_repeat_weekly(self):
        repeatable = Repeatable("WEEKLY", count=2, byday=["MO", "WE"])
        event = Event(name="Test repeatable #1", begin=dt(2019, 1, 14, 13, 30), duration=td(minutes=60),
                      rrule=repeatable)

        events = [event,
                  Event(name="Test repeatable #1", begin=dt(2019, 1, 16, 13, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2019, 1, 21, 13, 30), duration=td(minutes=60),
                        rrule=repeatable)]

        i = 0
        for e in event.repeat():
            self.assertTrue(e.time_equals(events[i]))
            i += 1

    def test_repeat_monthly_by_day(self):
        repeatable = Repeatable("MONTHLY", until=arrow.Arrow.fromdatetime(dt(2019, 6, 30, 16, 00)),
                                interval=2, byday=["1SU", "-1SU"])

        event = Event(name="Test repeatable #1", begin=dt(2019, 3, 3, 15, 30), duration=td(minutes=60),
                      rrule=repeatable)

        events = [event,
                  Event(name="Test repeatable #1", begin=dt(2019, 3, 31, 15, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2019, 5, 5, 15, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2019, 5, 26, 15, 30), duration=td(minutes=60),
                        rrule=repeatable)]

        i = 0
        for e in event.repeat():
            self.assertTrue(e.time_equals(events[i]))
            i += 1

    def test_repeat_monthly_by_date(self):
        repeatable = Repeatable("MONTHLY", until=arrow.Arrow.fromdatetime(dt(2019, 9, 30, 16, 00)),
                                interval=3, bymonthday=[1, 20])

        event = Event(name="Test repeatable #1", begin=dt(2019, 1, 1, 15, 30), duration=td(minutes=60),
                      rrule=repeatable)

        events = [event,
                  Event(name="Test repeatable #1", begin=dt(2019, 1, 20, 15, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2019, 4, 1, 15, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2019, 4, 20, 15, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2019, 7, 1, 15, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2019, 7, 20, 15, 30), duration=td(minutes=60),
                        rrule=repeatable)]

        i = 0
        for e in event.repeat():
            self.assertTrue(e.time_equals(events[i]))
            i += 1

    def test_repeat_yearly_by_day(self):
        repeatable = Repeatable("YEARLY", until=arrow.Arrow.fromdatetime(dt(2022, 1, 30, 16, 00)),
                                interval=2, byday=["1SU", "-1SU"], bymonth=[1])

        event = Event(name="Test repeatable #1", begin=dt(2019, 1, 6, 15, 30), duration=td(minutes=60),
                      rrule=repeatable)

        events = [event,
                  Event(name="Test repeatable #1", begin=dt(2019, 1, 27, 15, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2021, 1, 3, 15, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2021, 1, 31, 15, 30), duration=td(minutes=60),
                        rrule=repeatable)]

        i = 0
        for e in event.repeat():
            self.assertTrue(e.time_equals(events[i]))
            i += 1

    def test_repeat_yearly_by_date(self):
        repeatable = Repeatable("YEARLY", until=arrow.Arrow.fromdatetime(dt(2022, 1, 30, 16, 00)),
                                bymonthday=[1, 15], bymonth=[5])

        event = Event(name="Test repeatable #1", begin=dt(2019, 5, 1, 15, 30), duration=td(minutes=60),
                      rrule=repeatable)

        events = [event,
                  Event(name="Test repeatable #1", begin=dt(2019, 5, 15, 15, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2020, 5, 1, 15, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2020, 5, 15, 15, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2021, 5, 1, 15, 30), duration=td(minutes=60),
                        rrule=repeatable),
                  Event(name="Test repeatable #1", begin=dt(2021, 5, 15, 15, 30), duration=td(minutes=60),
                        rrule=repeatable)]

        i = 0
        for e in event.repeat():
            self.assertTrue(e.time_equals(events[i]))
            i += 1
