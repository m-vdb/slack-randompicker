import os

os.environ.setdefault("SLACK_TOKEN", "xoxb-00000000")
os.environ.setdefault("SLACK_SIGNING_SECRET", "1b5d1a00001001010be0a59fce1b8977")
os.environ.setdefault("DATABASE_URL", "sqlite://")

from asyncio import Future

import pytest

from randompicker import app as randompicker_app, slack_utils


@pytest.yield_fixture
def app():
    yield randompicker_app.app


@pytest.fixture
def test_cli(loop, app, sanic_client):
    return loop.run_until_complete(sanic_client(app))


@pytest.fixture
def mock_slack_api(mocker):
    conversations_members = Future()
    conversations_members.set_result({"members": ["U1", "U2"]})
    mocker.patch.object(
        slack_utils.slack_client,
        "conversations_members",
        return_value=conversations_members,
    )
    usergroups_users_list = Future()
    usergroups_users_list.set_result({"users": ["U3", "U4"]})
    mocker.patch.object(
        slack_utils.slack_client,
        "usergroups_users_list",
        return_value=usergroups_users_list,
    )
    chat_postmessage = Future()
    chat_postmessage.set_result({"ok": True})
    mocker.patch.object(
        slack_utils.slack_client, "chat_postMessage", return_value=chat_postmessage,
    )
    return slack_utils.slack_client
