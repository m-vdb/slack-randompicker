from unittest.mock import call

import pytest

from randompicker.format import HELP


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
