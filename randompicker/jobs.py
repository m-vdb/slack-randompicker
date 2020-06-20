from copy import deepcopy
from datetime import datetime
import hashlib
import re
from typing import List, Optional, Text, Union

from apscheduler.events import JobExecutionEvent
from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from recurrent import RecurringEvent


def make_job_id(
    team_id: Text,
    user_id: Text,
    task: Text,
    target: Text,
    frequency: Union[datetime, RecurringEvent],
) -> Text:
    """
    Make a job id from team id, user id and a hash of the task.
    """
    freq_repr = (
        repr(frequency)
        if isinstance(frequency, datetime)
        else repr(frequency.get_params())
    )
    task_id = hashlib.sha1(f"{task}{target}{freq_repr}".encode()).hexdigest()
    return f"{team_id}-{user_id}-{task_id}"


def list_scheduled_jobs(scheduler: AsyncIOScheduler, team_id: Text) -> List[Job]:
    """
    Return all the jobs matching team_id.
    """
    id_re = re.compile(rf"^{team_id}\-U[A-Z0-9]+\-[a-f0-9]{{40}}$")
    return [job for job in scheduler.get_jobs() if id_re.match(job.id)]


def update_picker_rotation(
    scheduler: AsyncIOScheduler, event: JobExecutionEvent
) -> None:
    """
    When a job finishes, we update its `previous_user_picks`
    parameter so that next time it runs, it will be able to
    pick users that were never picked.
    """
    job = scheduler.get_job(event.job_id)
    new_kwargs = deepcopy(job.kwargs)
    new_kwargs["previous_user_picks"] = event.retval
    job.modify(kwargs=new_kwargs)
