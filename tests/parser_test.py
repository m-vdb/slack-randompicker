from datetime import datetime

from dateutil.rrule import rrulestr
import pytest

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
    ('every day', rrulestr('RRULE:INTERVAL=1;FREQ=DAILY')),
    ('every year', rrulestr('RRULE:INTERVAL=1;FREQ=YEARLY')),
    ('every tuesday', rrulestr('RRULE:BYDAY=TU;INTERVAL=1;FREQ=WEEKLY')),
]


@pytest.mark.parametrize("frequency,expected", test_frequencies)
def test_parse_frequency(frequency, expected):
    assert str(parser.parse_frequency(frequency)) == str(expected)


test_specific_dates = [
    ('tomorrow at 9am', datetime(2020, 4, 29, 9, 0)),
    ('today at 10am', datetime(2020, 4, 28, 10, 0)),
    ('on Friday', datetime(2020, 5, 1, 0, 0)),
    ('on Monday May 4th at 9am', datetime(2020, 5, 4, 9, 0)),
]


@pytest.mark.freeze_time('2020-04-28 8:20')
@pytest.mark.parametrize("frequency,expected", test_specific_dates)
def test_parse_frequency_specific_date(frequency, expected):
    assert parser.parse_frequency(frequency) == expected


test_bad_frequencies = [
    'every BOOM',
    'on any day in the future',
    'on my birthday',
]

@pytest.mark.parametrize("frequency", test_bad_frequencies)
def test_parse_frequency_cannot_parse(frequency):
    assert parser.parse_frequency(frequency) is None
