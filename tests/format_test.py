from datetime import datetime

from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
import pytest

from randompicker import format as format_


def dummy_func(target, task):
    pass


test_scheduler = AsyncIOScheduler()
test_jobs = [
    Job(
        id="xxx",
        scheduler=test_scheduler,
        func=dummy_func,
        args=(),
        kwargs={"target": "C1234", "task": "play music"},
        trigger=CronTrigger(day_of_week="mon", hour="9", minute="0", week="*"),
    ),
    Job(
        id="yyy",
        scheduler=test_scheduler,
        func=dummy_func,
        args=(),
        kwargs={"target": "S1234", "task": "do groceries"},
        trigger=DateTrigger(run_date=datetime(2020, 5, 4, 18, 0)),
    ),
    Job(
        id="zzz",
        scheduler=test_scheduler,
        func=dummy_func,
        args=(),
        kwargs={"target": "C6789", "task": "play guitar"},
        trigger=CronTrigger(day_of_week="tue", hour="9", minute="0", week="*/2"),
    ),
    Job(
        id="www",
        scheduler=test_scheduler,
        func=dummy_func,
        args=(),
        kwargs={"target": "C6789", "task": "play violin"},
        trigger=CronTrigger(day_of_week="wed", hour="9", minute="0", week="*"),
    ),
]


@pytest.mark.asyncio
async def test_format_scheduled_jobs():
    expected = {
        "blocks": [
            {"text": {"text": "In this channel", "type": "mrkdwn"}, "type": "section"},
            {"text": {"text": "", "type": "plain_text"}, "type": "section"},
            {
                "accessory": {
                    "action_id": "REMOVE_JOB",
                    "style": "danger",
                    "text": {"text": "Remove", "type": "plain_text"},
                    "type": "button",
                    "value": "xxx",
                },
                "text": {
                    "text": f"*{format_.COMMAND_NAME}* <#C1234> to play music at 09:00 "
                    "AM, every Monday",
                    "type": "mrkdwn",
                },
                "type": "section",
            },
            {"text": {"text": "Other channels", "type": "mrkdwn"}, "type": "section"},
            {"text": {"text": "", "type": "plain_text"}, "type": "section"},
            {
                "accessory": {
                    "action_id": "REMOVE_JOB",
                    "style": "danger",
                    "text": {"text": "Remove", "type": "plain_text"},
                    "type": "button",
                    "value": "zzz",
                },
                "text": {
                    "text": f"*{format_.COMMAND_NAME}* <#C6789> to play guitar at 09:00 "
                    "AM, every Tuesday, every other week",
                    "type": "mrkdwn",
                },
                "type": "section",
            },
            {
                "accessory": {
                    "action_id": "REMOVE_JOB",
                    "style": "danger",
                    "text": {"text": "Remove", "type": "plain_text"},
                    "type": "button",
                    "value": "www",
                },
                "text": {
                    "text": f"*{format_.COMMAND_NAME}* <#C6789> to play violin at 09:00 "
                    "AM, every Wednesday",
                    "type": "mrkdwn",
                },
                "type": "section",
            },
            {"text": {"text": "User groups", "type": "mrkdwn"}, "type": "section"},
            {"text": {"text": "", "type": "plain_text"}, "type": "section"},
            {
                "accessory": {
                    "action_id": "REMOVE_JOB",
                    "style": "danger",
                    "text": {"text": "Remove", "type": "plain_text"},
                    "type": "button",
                    "value": "yyy",
                },
                "text": {
                    "text": f"*{format_.COMMAND_NAME}* <!subteam^S1234> to do groceries "
                    "on Monday May 4 at 06:00 PM",
                    "type": "mrkdwn",
                },
                "type": "section",
            },
        ],
    }
    value = await format_.format_scheduled_jobs("C1234", test_jobs)
    assert value == expected

    expected_empty = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "You haven't configured any random picks.",
                },
            },
        ]
    }
    value = await format_.format_scheduled_jobs("C1234", [])
    assert value == expected_empty


test_triggers = [
    # crons
    (CronTrigger(hour="9", minute="0"), "at 09:00 AM, every day",),
    (
        CronTrigger(day_of_week="mon", hour="9", minute="0", week="*"),
        "at 09:00 AM, every Monday",
    ),
    (
        CronTrigger(
            day_of_week="mon,tue,wed,thu,fri", hour="23", minute="0", week="*",
        ),
        "at 11:00 PM, every Monday, Tuesday, Wednesday, Thursday, and Friday",
    ),
    (
        CronTrigger(day_of_week="fri,sun", hour="14", minute="0", week="*"),
        "at 02:00 PM, every Friday and Sunday",
    ),
    (
        CronTrigger(day_of_week="wed", hour="14", minute="0", week="*/2"),
        "at 02:00 PM, every Wednesday, every other week",
    ),
    (
        CronTrigger(day_of_week="wed", hour="14", minute="0", week="*/3"),
        "at 02:00 PM, every Wednesday, every 3rd week",
    ),
    # dates
    (DateTrigger(run_date=datetime(2020, 5, 4, 9, 0)), "on Monday May 4 at 09:00 AM"),
    (DateTrigger(run_date=datetime(2020, 5, 4, 18, 0)), "on Monday May 4 at 06:00 PM"),
    (
        DateTrigger(run_date=datetime(2020, 6, 4, 18, 0)),
        "on Thursday June 4 at 06:00 PM",
    ),
]


@pytest.mark.parametrize("trigger,expected", test_triggers)
def test_format_trigger(trigger, expected):
    assert format_.format_trigger(trigger) == expected


test_slack_ids_messages = [
    ("C01234", "<#C01234> you have been picked to play music"),
    ("U01234", "<@U01234> you have been picked to play music"),
    ("S01234", "<!subteam^S01234> you have been picked to play music"),
]


@pytest.mark.parametrize("slack_id,expected", test_slack_ids_messages)
def test_format_slack_message(slack_id, expected):
    assert format_.format_slack_message(slack_id, "play music") == expected


test_slack_ids = [
    ("C01234", "<#C01234>"),
    ("U01234", "<@U01234>"),
    ("S01234", "<!subteam^S01234>"),
]


@pytest.mark.parametrize("slack_id,expected", test_slack_ids)
def test_mention_slack_id(slack_id, expected):
    assert format_.mention_slack_id(slack_id) == expected


def test_mention_slack_id_unknown_format():
    with pytest.raises(ValueError):
        format_.mention_slack_id("X00000")
