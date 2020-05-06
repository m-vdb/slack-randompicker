from datetime import datetime
import json
from unittest.mock import call

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
import pytest
import requests

from randompicker import app as randompicker_app
from randompicker.format import HELP, SLACK_ACTION_REMOVE_JOB


async def test_index(test_cli):
    resp = await test_cli.get("/")
    assert resp.status == 404


async def test_GET_slashcommand(test_cli):
    resp = await test_cli.get("/slashcommand")
    assert resp.status == 405


async def test_POST_slashcommand_require_secret(test_cli):
    resp = await test_cli.post(
        "/slashcommand",
        data={
            "text": "help",
            "user_id": "U1337",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 401


async def test_POST_slashcommand_help(api_post):
    resp = await api_post(
        "/slashcommand",
        data={
            "text": "help",
            "user_id": "U1337",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 200
    assert resp.content_type == "text/plain"
    body = await resp.read()
    assert body.decode() == HELP


async def test_POST_slashcommand_help_by_default(api_post):
    resp = await api_post(
        "/slashcommand",
        data={
            "text": "stuff",
            "user_id": "U1337",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 200
    assert resp.content_type == "text/plain"
    body = await resp.read()
    assert body.decode() == HELP


async def test_POST_slashcommand_pickrandom_now(api_post, mock_slack_api):
    resp = await api_post(
        "/slashcommand",
        data={
            "text": "<#C012X7LEUSV|general> to play music",
            "user_id": "U1337",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 200
    assert resp.content_type == "text/plain"
    body = await resp.read()
    assert body.decode() == ""
    mock_slack_api.chat_postMessage.assert_called()
    assert mock_slack_api.chat_postMessage.mock_calls[0] in [
        call(channel="C1234", text="<@U2> you have been picked to play music"),
        call(channel="C1234", text="<@U1> you have been picked to play music"),
    ]


async def test_POST_slashcommand_pickrandom_wrong_frequency(api_post, mock_slack_api):
    resp = await api_post(
        "/slashcommand",
        data={
            "text": "<#C012X7LEUSV|general> to play music on any day in the future",
            "user_id": "U1337",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 200
    assert resp.content_type == "text/plain"
    body = await resp.read()
    assert body.decode() == HELP


async def test_POST_slashcommand_pickrandom_periodic(api_post, mock_slack_api):
    resp = await api_post(
        "/slashcommand",
        data={
            "text": "<#C012X7LEUSV|general> to play music every day",
            "user_id": "U1337",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 200
    assert resp.content_type == "text/plain"
    body = await resp.read()
    assert body.decode() == (
        f"OK, I will pick someone from <#C012X7LEUSV> "
        f"to play music at 09:00 AM, every day"
    )
    scheduled_jobs = randompicker_app.scheduler.get_jobs()
    assert len(scheduled_jobs) == 1
    scheduled_job = scheduled_jobs[0]
    assert scheduled_job.kwargs == {
        "channel_id": "C1234",
        "target": "C012X7LEUSV",
        "task": "play music",
    }
    assert str(scheduled_job.trigger) == str(
        CronTrigger(day_of_week="*", hour="9", minute="0", timezone="Europe/Berlin")
    )


@pytest.mark.freeze_time("2020-04-28 8:20")
async def test_POST_slashcommand_pickrandom_on_specific_date(api_post, mock_slack_api):
    resp = await api_post(
        "/slashcommand",
        data={
            "text": "<#C012X7LEUSV|general> to play music on Monday",
            "user_id": "U1337",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 200
    assert resp.content_type == "text/plain"
    body = await resp.read()
    assert body.decode() == (
        f"OK, I will pick someone from <#C012X7LEUSV> "
        f"to play music on Monday May 4 at 09:00 AM"
    )
    scheduled_jobs = randompicker_app.scheduler.get_jobs()
    assert len(scheduled_jobs) == 1
    scheduled_job = scheduled_jobs[0]
    assert scheduled_job.kwargs == {
        "channel_id": "C1234",
        "target": "C012X7LEUSV",
        "task": "play music",
    }
    assert str(scheduled_job.trigger) == str(
        DateTrigger(run_date=datetime(2020, 5, 4, 9, 0, 0), timezone="Europe/Berlin")
    )


async def test_POST_slashcommand_list_empty(api_post):
    resp = await api_post(
        "/slashcommand",
        data={
            "text": "list",
            "user_id": "U1337",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 200
    assert resp.content_type == "application/json"
    body = await resp.json()
    assert body == {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "You haven't configured any random picks.",
                },
            }
        ]
    }


@pytest.mark.freeze_time("2020-04-28 8:20")
async def test_POST_slashcommand_list(api_post, mock_slack_api):
    # create 2 random picks
    resp = await api_post(
        "/slashcommand",
        data={
            "text": "<#C012X7LEUSV|general> to play music every day",
            "user_id": "U1337",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 200
    resp = await api_post(
        "/slashcommand",
        data={
            "text": "<#C012X7LEUSV|general> to play music on Tuesday",
            "user_id": "U1337",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 200

    # list these picks
    resp = await api_post(
        "/slashcommand",
        data={
            "text": "list",
            "user_id": "U1337",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 200
    assert resp.content_type == "application/json"
    body = await resp.json()
    assert body == {
        "blocks": [
            {
                "text": {
                    "text": "Here is the list of your random picks:",
                    "type": "plain_text",
                },
                "type": "section",
            },
            {
                "accessory": {
                    "action_id": "REMOVE_JOB",
                    "style": "danger",
                    "text": {"text": "Remove", "type": "plain_text"},
                    "type": "button",
                    "value": "T0007-U1337-91755068743c58e50e5ad00db66fce661d4bdd18",
                },
                "text": {
                    "text": "*/pickrandom* <#C012X7LEUSV> to play music at "
                    "09:00 AM, every day",
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
                    "value": "T0007-U1337-22cc24968180ada6cdad2ba5e17fe623c22523e0",
                },
                "text": {
                    "text": "*/pickrandom* <#C012X7LEUSV> to play music on "
                    "Tuesday May 5 at 09:00 AM",
                    "type": "mrkdwn",
                },
                "type": "section",
            },
        ],
    }


@pytest.mark.freeze_time("2020-04-28 8:20")
async def test_POST_slashcommand_list_all(api_post, mock_slack_api):
    # create 1 random picks from different user
    resp = await api_post(
        "/slashcommand",
        data={
            "text": "<#C012X7LEUSV|general> to play guitar every day",
            "user_id": "U42",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 200

    # no picks for the user
    resp = await api_post(
        "/slashcommand",
        data={
            "text": "list",
            "user_id": "U1337",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 200
    assert resp.content_type == "application/json"
    body = await resp.json()
    assert body == {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "You haven't configured any random picks.",
                },
            }
        ]
    }

    # list all command
    resp = await api_post(
        "/slashcommand",
        data={
            "text": "list all",
            "user_id": "U1337",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 200
    assert resp.content_type == "application/json"
    body = await resp.json()
    assert body == {
        "blocks": [
            {
                "text": {
                    "text": "Here is the list of random picks:",
                    "type": "plain_text",
                },
                "type": "section",
            },
            {
                "text": {
                    "text": "*/pickrandom* <#C012X7LEUSV> to play guitar at "
                    "09:00 AM, every day",
                    "type": "mrkdwn",
                },
                "type": "section",
            },
        ],
    }


async def test_GET_actions(test_cli):
    resp = await test_cli.get("/actions")
    assert resp.status == 405


async def test_POST_actions_require_secret(test_cli):
    resp = await test_cli.post("/actions", data={"payload": "{}",},)
    assert resp.status == 401


async def test_POST_actions_unknown_job(api_post, mocker):
    mocker.patch.object(requests, "post")

    resp = await api_post(
        "/actions",
        data={
            "payload": json.dumps(
                {
                    "team": {"id": "T0007"},
                    "user": {"id": "U1337"},
                    "response_url": "http://resp.url",
                    "actions": [
                        {"action_id": "other", "value": "xxx"},
                        {"action_id": SLACK_ACTION_REMOVE_JOB, "value": "???"},
                    ],
                }
            ),
        },
    )
    assert resp.status == 200
    assert resp.content_type == "text/plain"
    body = await resp.read()
    assert body.decode() == "OK"
    requests.post.assert_not_called()


async def test_POST_actions_removed_job(api_post, mocker, mock_slack_api):
    mocker.patch.object(requests, "post")
    # create 1 pick
    resp = await api_post(
        "/slashcommand",
        data={
            "text": "<#C012X7LEUSV|general> to play music every day",
            "user_id": "U1337",
            "channel_id": "C1234",
            "team_id": "T0007",
        },
    )
    assert resp.status == 200
    scheduled_jobs = randompicker_app.scheduler.get_jobs()
    assert len(scheduled_jobs) == 1
    scheduled_job = scheduled_jobs[0]

    resp = await api_post(
        "/actions",
        data={
            "payload": json.dumps(
                {
                    "team": {"id": "T0007"},
                    "user": {"id": "U1337"},
                    "response_url": "http://resp.url",
                    "actions": [
                        {
                            "action_id": SLACK_ACTION_REMOVE_JOB,
                            "value": scheduled_job.id,
                        },
                    ],
                }
            ),
        },
    )
    assert resp.status == 200
    assert resp.content_type == "text/plain"
    body = await resp.read()
    assert body.decode() == "OK"
    assert len(randompicker_app.scheduler.get_jobs()) == 0
    requests.post.assert_called_with(
        "http://resp.url",
        json={
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "You haven't configured any random picks.",
                    },
                }
            ]
        },
    )
