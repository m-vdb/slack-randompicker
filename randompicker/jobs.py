from datetime import datetime
import hashlib
from typing import Text, Union

from recurrent import RecurringEvent


def make_job_id(
    team_id: Text, user_id: Text, task: Text, frequency: Union[datetime, RecurringEvent]
) -> Text:
    """
    Make a job id from team id, user id and a hash of the task.
    """
    freq_repr = (
        repr(frequency)
        if isinstance(frequency, datetime)
        else repr(frequency.get_params())
    )
    task_id = hashlib.sha1(freq_repr.encode()).hexdigest()
    return f"{team_id}-{user_id}-{task_id}"
