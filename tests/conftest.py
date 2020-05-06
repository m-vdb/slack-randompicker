import os

os.environ.setdefault("SLACK_TOKEN", "xoxb-00000000")
os.environ.setdefault("SLACK_SIGNING_SECRET", "1b5d1a00001001010be0a59fce1b8977")
os.environ.setdefault("DATABASE_URL", "sqlite://")

from asyncio import Future
import hashlib
import hmac
import urllib.parse

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
    users_info = Future()
    users_info.set_result({"tz": "Europe/Berlin"})
    mocker.patch.object(
        slack_utils.slack_client, "users_info", return_value=users_info,
    )
    return slack_utils.slack_client


@pytest.fixture
def api_signature():
    def inner_api_signature(data):
        fake_timestamp = "1588706373"
        format_req = str.encode(f"v0:{fake_timestamp}:{data}")
        encoded_secret = str.encode(os.environ["SLACK_SIGNING_SECRET"])
        request_hash = hmac.new(encoded_secret, format_req, hashlib.sha256).hexdigest()
        return {
            "X-Slack-Request-Timestamp": fake_timestamp,
            "X-Slack-Signature": f"v0={request_hash}",
        }

    return inner_api_signature


@pytest.fixture
def api_post(test_cli, api_signature):
    async def inner_api_post_with_signature(url, data):
        resp = await test_cli.post(
            url, data=data, headers=api_signature(urllib.parse.urlencode(data))
        )
        return resp

    yield inner_api_post_with_signature
    randompicker_app.scheduler.remove_all_jobs()
