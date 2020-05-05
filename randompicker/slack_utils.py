import functools
import os
import random
from typing import List, Text

from sanic import response
from sanic.log import logger
from slack import WebClient

from randompicker.format import format_slack_message


slack_client = WebClient(token=os.environ["SLACK_TOKEN"], run_async=True)


async def list_users_target(target: Text) -> List[Text]:
    """
    List users from a channel or usergroup.
    """
    if target.startswith("C"):  # channel
        channel_info = await slack_client.conversations_members(channel=target)
        return channel_info["members"]
    elif target.startswith("S"):  # usergroup
        group_info = await slack_client.usergroups_users_list(usergroup=target)
        return group_info["users"]

    raise ValueError(f"Unknown type for Slack ID {target}")


async def pick_user_and_send_message(channel_id: Text, target: Text, task: Text):
    """
    This function is scheduled from `schedule_randompick_for_later`.
    """
    users = await list_users_target(target)
    user = random.choice(users)
    logger.info("Sending message to Slack API")
    await slack_client.chat_postMessage(
        channel=channel_id, text=format_slack_message(user, task)
    )
    logger.info("Done.")


def requires_slack_signature(func):
    """
    Decorator to require slack signature on sanic endpoints.
    """

    @functools.wraps(func)
    async def inner(request):
        if not WebClient.validate_slack_signature(
            signing_secret=os.environ["SLACK_SIGNING_SECRET"],
            data=request.body.decode("utf-8"),
            timestamp=request.headers.get("X-Slack-Request-Timestamp", ""),
            signature=request.headers.get("X-Slack-Signature", ""),
        ):
            return response.text("Invalid secret", status=401)

        return await func(request)

    return inner
