from typing import Dict, List, Text, Union

from apscheduler.job import Job
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
import cron_descriptor


COMMAND_NAME = "/pickrandom"


HELP = (
    f"Example usage:\n\n"
    f"*{COMMAND_NAME}* @group to do something\n"
    f"*{COMMAND_NAME}* @group to do something every day at 9am\n"
    f"*{COMMAND_NAME}* @group to do something on Monday at 9am\n"
    f"*{COMMAND_NAME}* #channel to do something\n"
    f"*{COMMAND_NAME}* list\n"
    f"*{COMMAND_NAME}* list all\n"
)


SLACK_ACTION_REMOVE_JOB = "REMOVE_JOB"


async def format_user_jobs(jobs: List[Job], list_all=False) -> Dict:
    """
    Format the list of user jobs to text.
    """
    if not jobs:
        return {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": "You haven't configured any random picks.",
                    },
                },
            ]
        }

    your = "" if list_all else "your "
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": f"Here is the list of {your}random picks:",
            },
        },
    ]
    for job in jobs:
        block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{COMMAND_NAME}* {mention_slack_id(job.kwargs['target'])} "
                f"to {job.kwargs['task']} {format_trigger(job.trigger)}",
            },
        }
        if list_all is False:
            block["accessory"] = {
                "type": "button",
                "style": "danger",
                "text": {"type": "plain_text", "text": "Remove"},
                "value": job.id,
                "action_id": SLACK_ACTION_REMOVE_JOB,
            }
        blocks.append(block)
    return {"blocks": blocks}


def format_trigger(trigger: Union[CronTrigger, DateTrigger]) -> Text:
    """
    Format a trigger to human readable format.
    """
    if isinstance(trigger, CronTrigger):
        trigger_fields = {field.name: field for field in trigger.fields}
        return remove_first_cap(
            cron_descriptor.get_description(
                f"{trigger_fields['minute']} {trigger_fields['hour']} {trigger_fields['day']} "
                f"{trigger_fields['month']} {trigger_fields['day_of_week']}"
            ).replace("only on", "every")
        )

    return trigger.run_date.strftime("on %A %B %-d at %I:%M %p")


def format_slack_message(user: Text, task: Text) -> Text:
    """
    Format Slack message to send to member.
    """
    return f"{mention_slack_id(user)} you have been picked to {task}"


def mention_slack_id(slack_id: Text):
    """
    Format a slack id to the proper mentionning format.
    """
    if slack_id.startswith("C"):  # channel
        return f"<#{slack_id}>"
    elif slack_id.startswith("U"):  # user
        return f"<@{slack_id}>"
    elif slack_id.startswith("S"):  # usergroup
        return f"<!subteam^{slack_id}>"

    raise ValueError(f"Unknown type for Slack ID {slack_id}")


def remove_first_cap(text: Text):
    """
    Remove the first capital letter of a string.
    """
    return text[0].lower() + text[1:] if text else text