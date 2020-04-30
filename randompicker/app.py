from datetime import datetime
import os
from pathlib import Path
import random
import sys
from typing import List, Text, Union

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from recurrent import RecurringEvent
import requests
from sanic import Sanic, response
from sanic.log import logger
from slack import WebClient

from randompicker.parser import (
    convert_recurring_event_to_trigger_format,
    parse_command,
    parse_frequency,
)


app = Sanic("randompicker")


slack_client = WebClient(token=os.environ["SLACK_TOKEN"], run_async=True)


scheduler: AsyncIOScheduler = None


HELP = (
    "Example usage:\n\n"
    "/pickrandom @group to do something\n"
    "/pickrandom @group to do something every day at 9am\n"
    "/pickrandom @group to do something on Monday at 9am\n"
    "/pickrandom #channel to do something\n"
)


@app.listener("before_server_start")
async def initialize_scheduler(app, loop):
    logger.info("Starting job scheduler")
    global scheduler
    scheduler = AsyncIOScheduler(
        {
            "apscheduler.jobstores.default": {
                "type": "sqlalchemy",
                "url": os.environ["DATABASE_URL"],
            },
        }
    )
    scheduler.start()


@app.route("/slashcommand", methods=["POST"])
async def slashcommand(request):
    """
    Endpoint that receives `/pickrandom` command. Form data contains:
    - command: the name of the command that was sent
    - text: the content of the command (after the `/pickrandom`)
    - response_url: a temporary webhook URL to generate messages responses
    - user_id: the user id of the user who triggered the command
    """

    if not WebClient.validate_slack_signature(
        signing_secret=os.environ["SLACK_SIGNING_SECRET"],
        data=request.body.decode("utf-8"),
        timestamp=request.headers["X-Slack-Request-Timestamp"],
        signature=request.headers["X-Slack-Signature"],
    ):
        return response.text("Invalid secret", status=401)

    command = request.form["text"][0]
    webhook_url = request.form["response_url"][0]
    logger.info("Incoming command %s", command)
    params = parse_command(command)
    if params is None:
        return response.text(HELP)

    logger.info("Handling slash command with params %s", params)

    users = await list_users_target(params["target"])

    if not params.get("frequency"):
        user = random.choice(users)
        return response.text(format_slack_message(user, params["task"]))

    frequency = parse_frequency(params["frequency"])
    if frequency is None:
        return response.text(HELP)

    # get user timezone
    user_info = await slack_client.users_info(user=request.form["user_id"][0])
    user_tz = user_info["tz"]
    schedule_randompick_for_later(
        frequency=frequency,
        user_tz=user_tz,
        target=params["target"],
        task=params["task"],
    )
    return response.text(
        f"OK, I will pick someone " f"to {params['task']} {params['frequency']}"
    )


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


def format_slack_message(user: Text, task: Text) -> Text:
    """
    Format Slack message to send to member.
    """
    return f"<@{user}> you have been picked to {task}"


def schedule_randompick_for_later(
    frequency: Union[datetime, RecurringEvent], user_tz: Text, target: Text, task: Text
):
    """
    Schedule a job to send a Slack message later, using the `pick_user_and_send_message`
    function.
    """
    if isinstance(frequency, datetime):
        trigger_params = {
            "trigger": "date",
            "run_date": frequency,
            "timezone": user_tz,
        }
    else:
        trigger_params = {
            "trigger": "cron",
            "timezone": user_tz,
        }
        trigger_params.update(convert_recurring_event_to_trigger_format(frequency))

    scheduler.add_job(
        pick_user_and_send_message,
        kwargs={"target": target, "task": task},
        **trigger_params,
    )


async def pick_user_and_send_message(target: Text, task: Text):
    """
    This function is scheduled from `schedule_randompick_for_later`.
    """
    users = await list_users_target(target)
    user = random.choice(users)
    # TODO: send mesage via API
    logger.info("Sending message to Slack API")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, access_log=True)
