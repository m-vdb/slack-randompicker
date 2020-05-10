from datetime import datetime
import re
from typing import Dict, Optional, Text, Union

import dateparser
from dateutil.rrule import rrulestr
from recurrent import RecurringEvent


HELP_RE = re.compile(r"^help.*$")
LIST_RE = re.compile(r"^\s*list\s*(all)?\s*$")
LIST_ALL_RE = re.compile(r"^\s*list\s*all\s*$")


FREQUENCY_PATTERN = r"(on|every|next|today|tomorrow) (.+)"


# /pickrandom @group to do something
# /pickrandom @group to do something every day at 9am
# /pickrandom #channel to do something
# /pickrandom @group to do something on Monday at 9am
# /pickrandom @group to do something next Monday at 9am
COMMAND_RE = re.compile(
    fr"^<(?:#|!subteam\^)(?P<target>[A-Z0-9]+)(?:|[^>]+)?>\s+"  # group or channel id
    fr"to (?P<task>.+?)\s*"  # task to do
    fr"(?P<frequency>{FREQUENCY_PATTERN})?$"  # optional date or frequency
)


def is_list_command(command: Text) -> bool:
    """
    Return True if the command is the list command.
    """
    return bool(LIST_RE.match(command))


def is_list_all_command(command: Text) -> bool:
    """
    Return True if the command is the list command.
    """
    return bool(LIST_ALL_RE.match(command))


def parse_command(command: Text) -> Optional[Dict]:
    """
    Parse the slash command and returns a dict containing the following keys:
    - target: the group or channel
    - task: the task to perform
    - frequency: optional frequency
    """
    match = COMMAND_RE.match(command.strip())
    return match.groupdict() if match else None


def parse_frequency(frequency: Text) -> Optional[Union[datetime, RecurringEvent]]:
    """
    Parse frequency or date using `recurrent` and `dateparser` module.
    """
    if frequency.startswith("every"):
        rec = RecurringEvent()
        parsed_rrule = rec.parse(frequency)
        if rec.bymonthday or rec.byyearday:
            # not supported
            return None

        try:
            rrulestr(parsed_rrule)  # this validates the parsing
        except (ValueError, TypeError):
            return None
        else:
            # ensure that hours are set, otherwise default to 9am
            if not rec.byhour and not rec.byminute:
                rec.byhour.append("9")
                rec.byminute.append("0")
            return rec
    else:
        value = dateparser.parse(frequency, settings={"PREFER_DATES_FROM": "future"})
        if value and not value.hour and not value.minute:
            # default 9am if no times
            value = value.replace(hour=9)
        return value


def convert_recurring_event_to_trigger_format(event: RecurringEvent):
    """
    Convert RecurringEvent instances to the APScheduler trigger cron format.

    https://github.com/kvh/recurrent
    https://apscheduler.readthedocs.io/en/stable/modules/triggers/cron.html
    """
    params = event.get_params()
    interval = params.pop("interval")
    frequency_value = "*" if interval == 1 else f"*/{interval}"
    frequency_key = RECURRING_EVENT_FREQUENCY_MAPPING[params.pop("freq")]

    trigger_params = {
        RECURRING_EVENT_PARAMS_MAPPING[param]: (
            _map_weekdays(value) if param == "byday" else value
        )
        for param, value in params.items()
    }
    trigger_params[frequency_key] = frequency_value
    return trigger_params


def _map_weekdays(weekdays: Text) -> Text:
    """
    Map weekdays to cron compatible weekdays.
    """
    return ",".join([WEEKDAY_MAP[weekday] for weekday in weekdays.split(",")])


# bymonthday and byyearday are omitted here because they're not supported
# by apscheduler cron triggers
RECURRING_EVENT_PARAMS_MAPPING = {
    "byday": "day_of_week",
    "bymonth": "month",
    "byhour": "hour",
    "byminute": "minute",
    "dtstart": "start_date",
    "until": "end_date",
}


RECURRING_EVENT_FREQUENCY_MAPPING = {
    "daily": "day_of_week",
    "weekly": "week",
    "monthly": "month",
    "yearly": "year",
    "minutely": "minute",
    "secondly": "second",
}

WEEKDAY_MAP = {
    "MO": "mon",
    "TU": "tue",
    "WE": "wed",
    "TH": "thu",
    "FR": "fri",
    "SA": "sat",
    "SU": "sun",
}
