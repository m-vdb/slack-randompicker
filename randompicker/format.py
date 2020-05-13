from collections import OrderedDict
from typing import Dict, List, Text, Union

from apscheduler.job import Job
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
import cron_descriptor


COMMAND_NAME = "/pickrandom"


HELP = (
    f"*Example usage:*\n\n"
    f"_{COMMAND_NAME}_ @group to do something\n"
    f"_{COMMAND_NAME}_ @group to do something every day at 9am\n"
    f"_{COMMAND_NAME}_ @group to do something on Monday at 9am\n"
    f"_{COMMAND_NAME}_ #channel to do something\n"
    f"_{COMMAND_NAME}_ list\n"
)


SLACK_ACTION_REMOVE_JOB = "REMOVE_JOB"
KEY_THIS_CHANNEL = "In this channel"
KEY_OTHER_CHANNEL = "Other channels"
KEY_USER_GROUPS = "User groups"


async def format_scheduled_jobs(channel: Text, jobs: List[Job]) -> Dict:
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

    jobs_by_category = split_jobs_by_category(channel, jobs)
    blocks = []
    for category, job_list in jobs_by_category.items():
        if not job_list:
            continue

        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*{category}*",},},
        )
        for job in job_list:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"_{COMMAND_NAME}_ {mention_slack_id(job.kwargs['target'])} "
                        f"to {job.kwargs['task']} {format_trigger(job.trigger)}",
                    },
                    "accessory": {
                        "type": "button",
                        "style": "danger",
                        "text": {"type": "plain_text", "text": "Remove"},
                        "value": job.id,
                        "action_id": SLACK_ACTION_REMOVE_JOB,
                    },
                }
            )

    return {"blocks": blocks}


def split_jobs_by_category(channel: Text, jobs: List[Job]) -> Dict[Text, List[Job]]:
    """
    Split jobs in 3 categories:
        In this channel:
        ....

        Other channels:
        ....

        User groups:
        ....
    """
    output: OrderedDict = OrderedDict(
        [(KEY_THIS_CHANNEL, []), (KEY_OTHER_CHANNEL, []), (KEY_USER_GROUPS, []),]
    )
    # split in categories
    for job in jobs:
        if job.kwargs["target"] == channel:
            output[KEY_THIS_CHANNEL].append(job)
        elif job.kwargs["target"].startswith("C"):
            output[KEY_OTHER_CHANNEL].append(job)
        elif job.kwargs["target"].startswith("S"):
            output[KEY_USER_GROUPS].append(job)

    # sort each category
    for key in output:
        output[key] = sorted(output[key], key=lambda job: job.kwargs["target"])

    return output


def format_trigger(trigger: Union[CronTrigger, DateTrigger]) -> Text:
    """
    Format a trigger to human readable format.
    """
    if isinstance(trigger, CronTrigger):
        trigger_fields = {field.name: str(field) for field in trigger.fields}
        description = remove_first_cap(
            cron_descriptor.get_description(
                f"{trigger_fields['minute']} {trigger_fields['hour']} {trigger_fields['day']} "
                f"{trigger_fields['month']} {trigger_fields['day_of_week']}"
            ).replace("only on", "every")
        )
        if trigger_fields["day"] == "*" and trigger_fields["day_of_week"] == "*":
            description = f"{description}, every day"
        elif trigger_fields["week"].startswith("*/"):
            week_interval = int(trigger_fields["week"][2:])
            week_interval_ordinal = (
                "other" if week_interval == 2 else format_ordinal(week_interval)
            )
            description = f"{description}, every {week_interval_ordinal} week"

        return description

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


def format_ordinal(number: int) -> Text:
    """
    Given a number, output its ordinal version (1st, 2nd, 3rd, etc...).
    """
    return "%d%s" % (
        number,
        "tsnrhtdd"[(number / 10 % 10 != 1) * (number % 10 < 4) * number % 10 :: 4],
    )
