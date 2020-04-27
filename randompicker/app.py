import logging.config

from flask import Flask, request

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
    - token: Slack token for signing
    - command: the name of the command that was sent
    - text: the content of the command (after the `/pickrandom`)
    - response_url: a temporary webhook URL to generate messages responses
    """

    # 1. check token

    app.logger.info("Incoming command %s", request.form["text"])
    params = parse_command(request.form["text"])
    if params is None:
        return HELP

    app.logger.info("Handling slash command with params %s", params)

    if not params.get("frequency"):
        # TODO: slack API call to get group or channel users
        return "OK"

    # TODO: parse frequency and make sure we understand it
    # TODO: validate group id against api
    # TODO: store command somewhere
    return "OK, later"
