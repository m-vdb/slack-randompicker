import os
from pathlib import Path
import random
import sys
from typing import List, Text

from sanic import Sanic, response
from sanic.log import logger
from slack import WebClient
import requests

from randompicker.parser import parse_command, parse_frequency


app = Sanic()


slack_client = WebClient(token=os.environ["SLACK_TOKEN"], run_async=True)


HELP = (
    "Example usage:\n\n"
    "/pickrandom @group to do something\n"
    "/pickrandom @group to do something every day at 9am\n"
    "/pickrandom @group to do something on Monday at 9am\n"
    "/pickrandom #channel to do something\n"
)


@app.route("/slashcommand", methods=["POST"])
async def slashcommand(request):
    """
    Endpoint that receives `/pickrandom` command. Form data contains:
    - command: the name of the command that was sent
    - text: the content of the command (after the `/pickrandom`)
    - response_url: a temporary webhook URL to generate messages responses
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
        send_immediate_slack_message(webhook_url, HELP)
        return response.text("OK, help")

    logger.info("Handling slash command with params %s", params)

    users = await list_users_target(params["target"])

    if not params.get("frequency"):
        user = random.choice(users)
        send_immediate_slack_message(
            webhook_url, format_slack_message(user, params["task"])
        )
        return response.text("OK")

    frequency = parse_frequency(params=params["frequency"])
    if frequency is None:
        send_immediate_slack_message(webhook_url, HELP)
        return "OK, cannot parse frequency"

    # TODO: store command somewhere
    send_immediate_slack_message(
        webhook_url,
        f"OK, I will pick someone " f"to {params['task']} {params['frequency']}",
    )
    return response.text("OK, later")


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


def send_immediate_slack_message(webhook_url: Text, message: Text):
    """
    Send an immediate Slack message using the webhook URL
    sent by Slack.
    """
    api_response = requests.post(webhook_url, json={"text": message})
    api_response.raise_for_status()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, access_log=True)
