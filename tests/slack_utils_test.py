from datetime import datetime
from unittest.mock import call

import pytest

from randompicker import slack_utils


@pytest.mark.asyncio
async def test_list_users_target_channel(mock_slack_api):
    users = await slack_utils.list_users_target("C000001")
    assert users == ["U1", "U2"]
    mock_slack_api.conversations_members.assert_called_with(channel="C000001")
    mock_slack_api.usergroups_users_list.assert_not_called()


@pytest.mark.asyncio
async def test_list_users_target_group(mock_slack_api):
    users = await slack_utils.list_users_target("S000001")
    assert users == ["U3", "U4"]
    mock_slack_api.conversations_members.assert_not_called()
    mock_slack_api.usergroups_users_list.assert_called_with(usergroup="S000001")


@pytest.mark.asyncio
async def test_list_users_target_other():
    with pytest.raises(ValueError):
        await slack_utils.list_users_target("X00000")


@pytest.mark.asyncio
async def test_pick_user_and_send_message(mock_slack_api):
    await slack_utils.pick_user_and_send_message("C000001", "C000002", "play music")
    mock_slack_api.conversations_members.assert_called_with(channel="C000002")
    mock_slack_api.usergroups_users_list.assert_not_called()
    mock_slack_api.chat_postMessage.assert_called()
    assert slack_utils.slack_client.chat_postMessage.mock_calls[0] in (
        call(channel="C000001", text="<@U1> you have been picked to play music"),
        call(channel="C000001", text="<@U2> you have been picked to play music"),
    )
