from datetime import datetime
import os
from typing import Text, Union
import json

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from recurrent import RecurringEvent
import requests
from sanic import Sanic, response
from sanic.log import logger

from randompicker.format import (
    HELP,
    SLACK_ACTION_REMOVE_JOB,
    format_slack_message,
    format_scheduled_jobs,
    mention_slack_id,
    format_trigger,
)
from randompicker.jobs import list_scheduled_jobs, make_job_id
from randompicker.parser import (
    convert_recurring_event_to_trigger_format,
    is_list_command,
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
        jobs = list_scheduled_jobs(scheduler, team_id)
        jobs_json = await format_scheduled_jobs(channel_id, jobs)
        return response.json(jobs_json)

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
    job = schedule_randompick_for_later(
        frequency=frequency,
        user_tz=user_tz,
        target=params["target"],
        task=params["task"],
        user_id=user_id,
        channel_id=channel_id,
        team_id=team_id,
    )
    return response.text(
        f"OK, I will pick someone from {mention_slack_id(params['target'])} "
        f"to {params['task']} {format_trigger(job.trigger)}"
    )


@app.route("/actions", methods=["POST"])
@requires_slack_signature
async def actions(request):
    """
    This endpoint receives actions and other Interactivity elements from Slack.
    """
    payload = json.loads(request.form["payload"][0])
    team_id = payload["team"]["id"]
    user_id = payload["user"]["id"]
    channel_id = payload["channel"]["id"]
    response_url = payload["response_url"]

    for action in payload["actions"]:
        if action["action_id"] == SLACK_ACTION_REMOVE_JOB:
            job_id = action["value"]
            # remove job
            try:
                scheduler.remove_job(job_id)
            except JobLookupError:
                logger.error(f"Cannot find scheduled job with id {job_id}")
            else:
                # update the message the user sees
                jobs = list_scheduled_jobs(scheduler, team_id)
                jobs_json = await format_scheduled_jobs(channel_id, jobs)
                resp = requests.post(response_url, json=jobs_json)
                resp.raise_for_status()
            break

    return response.text("OK")


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

    return scheduler.add_job(
        pick_user_and_send_message,
        kwargs={"channel_id": channel_id, "target": target, "task": task},
        id=make_job_id(team_id, user_id, task, target, frequency),
        replace_existing=True,  # replace job with same id
        **trigger_params,
    )


if __name__ == "__main__":  # pragma: no cover
    app.run(host="0.0.0.0", port=80, access_log=True)
