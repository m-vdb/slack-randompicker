import logging.config
import os
import random
from typing import List, Text

from flask import Flask, request
from slack import WebClient
import requests

from .parser import parse_command


logging.config.dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


app = Flask(__name__)


slack_client = WebClient(token=os.environ["SLACK_TOKEN"])


HELP = (
    "Example usage:\n\n"
    "/pickrandom @group to do something\n"
    "/pickrandom @group to do something every day at 9am\n"
    "/pickrandom @group to do something on Monday at 9am\n"
    "/pickrandom #channel to do something\n"
)


@app.route('/slashcommand', methods=["POST"])
def slashcommand():
    """
    Endpoint that receives `/pickrandom` command. Form data contains:
    - command: the name of the command that was sent
    - text: the content of the command (after the `/pickrandom`)
    - response_url: a temporary webhook URL to generate messages responses
    """

    if not WebClient.validate_slack_signature(
        signing_secret=os.environ["SLACK_SIGNING_SECRET"],
        data=request.get_data(as_text=True),
        timestamp=request.headers['X-Slack-Request-Timestamp'],
        signature=request.headers['X-Slack-Signature'],
    ):
        return "Invalid secret", 401

    app.logger.info("Incoming command %s", request.form["text"])
    params = parse_command(request.form["text"])
    if params is None:
        send_immediate_slack_message(request.form["response_url"], HELP)
        return "OK, help"

    app.logger.info("Handling slash command with params %s", params)

    users = list_users_target(params["target"])

    if not params.get("frequency"):
        user = random.choice(users)
        send_immediate_slack_message(request.form["response_url"], format_slack_message(user, params['task']))
        return "OK"

    # TODO: parse frequency and make sure we understand it
    # TODO: validate group id against api
    # TODO: store command somewhere
    return "OK, later"


def list_users_target(target: Text) -> List[Text]:
    """
    List users from a channel or usergroup.
    """
    if target.startswith("C"):  # channel
        response = slack_client.conversations_members(channel=target)
        return response["members"]
    elif target.startswith("S"):  # usergroup
        response = slack_client.usergroups_users_list(usergroup=target)
        return response["users"]

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
    response = requests.post(webhook_url, json={"text": message})
    response.raise_for_status()
