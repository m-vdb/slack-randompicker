import pytest

from randompicker import parser


test_commands = [
    ("stuff", None),
    (
        "<#C012X7LEUSV|general> to play music",
        {"target": "#C012X7LEUSV", "task": "play music", "frequency": None},
    ),
    (
        "<#C012X7LEUSV|general> to play music every day",
        {"target": "#C012X7LEUSV", "task": "play music", "frequency": "every day"},
    ),
    (
        "<#C012X7LEUSV|general> to play music                 ",
        {"target": "#C012X7LEUSV", "task": "play music", "frequency": None},
    ),
    (
        "<#C012X7LEUSV|general> to play music on monday",
        {"target": "#C012X7LEUSV", "task": "play music", "frequency": "on monday"},
    ),
    (
        "<#C012X7LEUSV|general> to play music next monday",
        {"target": "#C012X7LEUSV", "task": "play music", "frequency": "next monday"},
    ),
]


@pytest.mark.parametrize("command,expected", test_commands)
def test_parse_command(command, expected):
    assert parser.parse_command(command) == expected
