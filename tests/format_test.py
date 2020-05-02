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
]


@pytest.mark.asyncio
async def test_format_user_jobs():
    expected = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "Here is the list of your random picks:",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{format_.COMMAND_NAME}* <#C1234> to play music at 09:00 AM, every Monday",
                },
                "accessory": {
                    "type": "button",
                    "style": "danger",
                    "text": {"type": "plain_text", "text": "Remove"},
                    "value": "xxx",
                    "action_id": "REMOVE_JOB",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{format_.COMMAND_NAME}* <!subteam^S1234> to do groceries on Monday May 4 at 06:00 PM",
                },
                "accessory": {
                    "type": "button",
                    "style": "danger",
                    "text": {"type": "plain_text", "text": "Remove"},
                    "value": "yyy",
                    "action_id": "REMOVE_JOB",
                },
            },
        ]
    }
    value = await format_.format_user_jobs(test_jobs)
    assert value == expected

    expected_all = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "Here is the list of random picks:",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{format_.COMMAND_NAME}* <#C1234> to play music at 09:00 AM, every Monday",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{format_.COMMAND_NAME}* <!subteam^S1234> to do groceries on Monday May 4 at 06:00 PM",
                },
            },
        ]
    }
    value = await format_.format_user_jobs(test_jobs, True)
    assert value == expected_all

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
    value = await format_.format_user_jobs([])
    assert value == expected_empty


test_triggers = [
    # crons
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
        "at 02:00 PM, every Wednesday",
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
