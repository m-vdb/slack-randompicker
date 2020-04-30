import hashlib
from typing import Text


def make_job_id(team_id: Text, user_id: Text, task: Text) -> Text:
    """
    Make a job id from team id, user id and a hash of the task.
    """
    return f"{team_id}-{user_id}-{hashlib.sha1(task.encode()).hexdigest()}"
