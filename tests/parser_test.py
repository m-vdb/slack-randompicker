from datetime import datetime

import pytest
from recurrent import RecurringEvent

from randompicker import parser


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
]


@pytest.mark.parametrize("frequency,expected", test_frequencies)
def test_parse_frequency(frequency, expected):
    output = parser.parse_frequency(frequency)
    assert isinstance(output, RecurringEvent)
    assert output.get_params() == expected


test_specific_dates = [
    ("tomorrow at 9am", datetime(2020, 4, 29, 9, 0)),
    ("today at 10am", datetime(2020, 4, 28, 10, 0)),
    ("on Friday", datetime(2020, 5, 1, 0, 0)),
    ("on Monday May 4th at 9am", datetime(2020, 5, 4, 9, 0)),
]


@pytest.mark.freeze_time("2020-04-28 8:20")
@pytest.mark.parametrize("frequency,expected", test_specific_dates)
def test_parse_frequency_specific_date(frequency, expected):
    assert parser.parse_frequency(frequency) == expected


test_bad_frequencies = [
    "every BOOM",
    "on any day in the future",
    "on my birthday",
]


@pytest.mark.parametrize("frequency", test_bad_frequencies)
def test_parse_frequency_cannot_parse(frequency):
    assert parser.parse_frequency(frequency) is None
