from datetime import datetime
import re
from typing import Optional, Text, Union

import dateparser
from dateutil.rrule import rrulestr
from recurrent import RecurringEvent


HELP_RE = re.compile(r"^help.*$")


FREQUENCY_PATTERN = r"(on|every|next|today|tomorrow) (.+)"


# /pickrandom @group to do something
# /pickrandom @group to do something every day at 9am
# /pickrandom #channel to do something
# /pickrandom @group to do something on Monday at 9am
# /pickrandom @group to do something next Monday at 9am
COMMAND_RE = re.compile(
    fr"^<[@#](?P<target>[A-Z0-9]+)(?:|[^>]+)?>\s+"  # group or channel id
    fr"to (?P<task>.+?)\s*"  # task to do
    fr"(?P<frequency>{FREQUENCY_PATTERN})?$"  # optional date or frequency
)


def parse_command(command: str) -> Optional[dict]:
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
        return dateparser.parse(frequency, settings={"PREFER_DATES_FROM": "future"})
