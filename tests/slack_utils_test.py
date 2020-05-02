from asyncio import Future
from datetime import datetime
from unittest.mock import call

import pytest

from randompicker import slack_utils


def _mock_slack(mocker):
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


@pytest.mark.asyncio
async def test_list_users_target_channel(mocker):
    _mock_slack(mocker)
    users = await slack_utils.list_users_target("C000001")
    assert users == ["U1", "U2"]
    slack_utils.slack_client.conversations_members.assert_called_with(channel="C000001")
    slack_utils.slack_client.usergroups_users_list.assert_not_called()


@pytest.mark.asyncio
async def test_list_users_target_group(mocker):
    _mock_slack(mocker)
    users = await slack_utils.list_users_target("S000001")
    assert users == ["U3", "U4"]
    slack_utils.slack_client.conversations_members.assert_not_called()
    slack_utils.slack_client.usergroups_users_list.assert_called_with(
        usergroup="S000001"
    )


@pytest.mark.asyncio
async def test_list_users_target_other():
    with pytest.raises(ValueError):
        await slack_utils.list_users_target("X00000")


@pytest.mark.asyncio
async def test_pick_user_and_send_message(mocker):
    _mock_slack(mocker)
    await slack_utils.pick_user_and_send_message("C000001", "C000002", "play music")
    slack_utils.slack_client.conversations_members.assert_called_with(channel="C000002")
    slack_utils.slack_client.usergroups_users_list.assert_not_called()
    slack_utils.slack_client.chat_postMessage.assert_called()
    assert slack_utils.slack_client.chat_postMessage.mock_calls[0] in (
        call(channel="C000001", text="<@U1> you have been picked to play music"),
        call(channel="C000001", text="<@U2> you have been picked to play music"),
    )
