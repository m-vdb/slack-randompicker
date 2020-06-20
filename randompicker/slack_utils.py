import functools
import random
from typing import Optional, Set, Text

from sanic import response
from sanic.log import logger
from slack import WebClient

from randompicker.constants import SLACK_SIGNING_SECRET, SLACK_TOKEN
from randompicker.format import format_slack_message


slack_client = WebClient(token=SLACK_TOKEN, run_async=True)


async def list_users_target(target: Text) -> Set[Text]:
    """
    List users from a channel or usergroup.
    """
    if target.startswith("C"):  # channel
        channel_info = await slack_client.conversations_members(channel=target)
        return set(channel_info["members"])
    elif target.startswith("S"):  # usergroup
        group_info = await slack_client.usergroups_users_list(usergroup=target)
        return set(group_info["users"])

    raise ValueError(f"Unknown type for Slack ID {target}")


async def pick_user_and_send_message(
    channel_id: Text,
    target: Text,
    task: Text,
    previous_user_picks: Optional[Set[Text]] = None,
) -> Set[Text]:
    """
    This function is scheduled from `schedule_randompick_for_later`.
    """
    users = await list_users_target(target)
    # if some users were never picked, reduce the set of
    # pick-able users. Otherwise do not change it, and reset previous_user_pics
    previous_user_picks = previous_user_picks or set()
    users_never_picked = users - previous_user_picks
    if users_never_picked:
        users = users_never_picked
    else:
        previous_user_picks = set()
    user = random.sample(users, 1)[0]
    previous_user_picks.add(user)

    logger.info("Sending message to Slack API")
    await slack_client.chat_postMessage(
        channel=channel_id, text=format_slack_message(user, task)
    )
    logger.info("Done.")
    return previous_user_picks


def requires_slack_signature(func):
    """
    Decorator to require slack signature on sanic endpoints.
    """

    @functools.wraps(func)
    async def inner(request):
        if not WebClient.validate_slack_signature(
            signing_secret=SLACK_SIGNING_SECRET,
            data=request.body.decode("utf-8"),
            timestamp=request.headers.get("X-Slack-Request-Timestamp", ""),
            signature=request.headers.get("X-Slack-Signature", ""),
        ):
            return response.text("Invalid secret", status=401)

        return await func(request)

    return inner
