from datetime import datetime
import os
from typing import Text, Union

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from recurrent import RecurringEvent
from sanic import Sanic, response
from sanic.log import logger
from slack import WebClient

from randompicker.format import HELP, format_slack_message, format_user_jobs
from randompicker.jobs import list_user_jobs, make_job_id
from randompicker.parser import (
    convert_recurring_event_to_trigger_format,
    is_list_command,
    is_list_all_command,
    parse_command,
    parse_frequency,
)
from randompicker.slack_utils import (
    slack_client,
    list_users_target,
    pick_user_and_send_message,
    requires_slack_signature,
)


app = Sanic("randompicker")


scheduler: AsyncIOScheduler = None


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
@requires_slack_signature
async def slashcommand(request):
    """
    Endpoint that receives `/pickrandom` command. Form data contains:
    - command: the name of the command that was sent
    - text: the content of the command (after the `/pickrandom`)
    - channel_id: the channel in which the command is invoked
    - user_id: the user id of the user who triggered the command
    - team_id: the workspace id
    """
    command = request.form["text"][0]
    user_id = request.form["user_id"][0]
    channel_id = request.form["channel_id"][0]
    team_id = request.form["team_id"][0]

    logger.info("Incoming command %s", command)

    if is_list_command(command):
        list_all = is_list_all_command(command)
        user_jobs = list_user_jobs(scheduler, team_id, None if list_all else user_id)
        user_jobs_text = await format_user_jobs(user_jobs, list_all)
        return response.text(user_jobs_text)

    params = parse_command(command)
    if params is None:
        return response.text(HELP)

    logger.info("Handling slash command with params %s", params)

    if not params.get("frequency"):
        await pick_user_and_send_message(channel_id, params["target"], params["task"])
        return response.text("")

    frequency = parse_frequency(params["frequency"])
    if frequency is None:
        return response.text(HELP)

    # get user timezone
    user_info = await slack_client.users_info(user=user_id)
    user_tz = user_info["tz"]
    schedule_randompick_for_later(
        frequency=frequency,
        user_tz=user_tz,
        target=params["target"],
        task=params["task"],
        user_id=user_id,
        channel_id=channel_id,
        team_id=team_id,
    )
    return response.text(
        f"OK, I will pick someone " f"to {params['task']} {params['frequency']}"
    )


def schedule_randompick_for_later(
    frequency: Union[datetime, RecurringEvent],
    user_tz: Text,
    target: Text,
    task: Text,
    user_id: Text,
    channel_id: Text,
    team_id: Text,
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
        kwargs={"channel_id": channel_id, "target": target, "task": task},
        id=make_job_id(team_id, user_id, task, frequency),
        replace_existing=True,  # replace job with same id
        **trigger_params,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, access_log=True)
