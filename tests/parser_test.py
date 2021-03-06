from datetime import datetime

from apscheduler.triggers.cron import CronTrigger
import pytest
from recurrent import RecurringEvent

from randompicker import parser


test_list_commands = [
    ("list", True),
    ("  list  ", True),
    ("  list  stuff", False),
    ("<#C012X7LEUSV|general> to play music", False),
]


@pytest.mark.parametrize("command,expected", test_list_commands)
def test_is_list_command(command, expected):
    assert parser.is_list_command(command) is expected


test_commands = [
    ("stuff", None),
    (
        "<#C012X7LEUSV|general> to play music",
        {"target": "C012X7LEUSV", "task": "play music", "frequency": None},
    ),
    (
        "<#C012X7LEUSV|general> to play music every day",
        {"target": "C012X7LEUSV", "task": "play music", "frequency": "every day"},
    ),
    (
        "<#C012X7LEUSV|general> to play music                 ",
        {"target": "C012X7LEUSV", "task": "play music", "frequency": None},
    ),
    (
        "<#C012X7LEUSV|general> to play music on monday",
        {"target": "C012X7LEUSV", "task": "play music", "frequency": "on monday"},
    ),
    (
        "<#C012X7LEUSV|general> to play music next monday",
        {"target": "C012X7LEUSV", "task": "play music", "frequency": "next monday"},
    ),
    (
        "<!subteam^S013R9HGXJ5|test-group> to play music",
        {"target": "S013R9HGXJ5", "task": "play music", "frequency": None},
    ),
]


@pytest.mark.parametrize("command,expected", test_commands)
def test_parse_command(command, expected):
    assert parser.parse_command(command) == expected


test_frequencies = [
    ("every day", {"freq": "daily", "interval": 1, "byhour": "9", "byminute": "0",}),
    ("every year", {"interval": 1, "freq": "yearly", "byhour": "9", "byminute": "0",}),
    (
        "every tuesday",
        {
            "byday": "TU",
            "freq": "weekly",
            "interval": 1,
            "byhour": "9",
            "byminute": "0",
        },
    ),
    (
        "every tuesday at 9pm",
        {
            "byday": "TU",
            "byhour": "21",
            "byminute": "0",
            "freq": "weekly",
            "interval": 1,
        },
    ),
    (
        "every other thursday at 9pm",
        {
            "byday": "TH",
            "byhour": "21",
            "byminute": "0",
            "freq": "weekly",
            "interval": 2,
        },
    ),
]


@pytest.mark.parametrize("frequency,expected", test_frequencies)
def test_parse_frequency(frequency, expected):
    output = parser.parse_frequency(frequency)
    assert isinstance(output, RecurringEvent)
    assert output.get_params() == expected


test_specific_dates = [
    ("tomorrow at 9am", datetime(2020, 4, 29, 9, 0)),
    ("today at 10am", datetime(2020, 4, 28, 10, 0)),
    ("on Friday", datetime(2020, 5, 1, 9, 0)),
    ("on Monday May 4th at 10am", datetime(2020, 5, 4, 10, 0)),
]


@pytest.mark.freeze_time("2020-04-28 8:20")
@pytest.mark.parametrize("frequency,expected", test_specific_dates)
def test_parse_frequency_specific_date(frequency, expected):
    assert parser.parse_frequency(frequency) == expected


test_bad_frequencies = [
    "every BOOM",
    "on any day in the future",
    "on my birthday",
    "every 4th of the month",
]


@pytest.mark.parametrize("frequency", test_bad_frequencies)
def test_parse_frequency_cannot_parse(frequency):
    assert parser.parse_frequency(frequency) is None


test_recurring_events_parsing = [
    ("every day at 12am", {"day_of_week": "*", "hour": "0", "minute": "0",}),
    (
        "every Monday at 9am",
        {"day_of_week": "mon", "hour": "9", "minute": "0", "week": "*"},
    ),
    (
        "every weekday at 11pm",
        {
            "day_of_week": "mon,tue,wed,thu,fri",
            "hour": "23",
            "minute": "0",
            "week": "*",
        },
    ),
    (
        "every Friday and Sunday at 2pm",
        {"day_of_week": "fri,sun", "hour": "14", "minute": "0", "week": "*"},
    ),
    (
        "every other Wednesday at 2pm",
        {"day_of_week": "wed", "hour": "14", "minute": "0", "week": "*/2"},
    ),
]


@pytest.mark.parametrize("frequency,expected", test_recurring_events_parsing)
def test_convert_recurring_event_to_trigger_format(frequency, expected):
    event = RecurringEvent()
    event.parse(frequency)
    assert parser.convert_recurring_event_to_trigger_format(event) == expected
    # validate with ApsSchedule cron trigger
    CronTrigger(**expected)
