from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest
from recurrent import RecurringEvent
from apscheduler.events import JobExecutionEvent, EVENT_JOB_EXECUTED

from randompicker import jobs


rec_event = RecurringEvent()
rec_event.parse("every day at 9am")
test_frequencies = [
    (
        datetime(2020, 6, 10, 12),
        "play music",
        "C1234",
        "T123456-U78910-b94bccc628b9d0cb233ce293f5c657df3f5f62f0",
    ),
    (
        datetime(2020, 6, 10, 12),
        "play music",
        "S5678",
        "T123456-U78910-6791a246535100ef9b437490f139cb377a50d795",
    ),
    (
        datetime(2020, 6, 10, 12),
        "do groceries",
        "C1234",
        "T123456-U78910-7a51ce02398b6db791b944d10c366ca8089bf79e",
    ),
    (
        rec_event,
        "play music",
        "C1234",
        "T123456-U78910-ab9b7ccab76fe57d326cc0c2afb46af1316844f7",
    ),
]


@pytest.mark.parametrize("frequency,task,target,expected", test_frequencies)
def test_make_job_id(frequency, task, target, expected):
    assert jobs.make_job_id("T123456", "U78910", task, target, frequency) == expected


def test_list_scheduled_jobs():
    job1 = Mock(id="T123456-U78910-0a0ca9f0c52fec59b714ea1a1c7f5f9928d33fd3")
    job2 = Mock(id="T123456-U78911-0a0ca9f0c52fec59b714ea1a1c7f5f9928d33fd3")
    job3 = Mock(id="T123457-U78910-0a0ca9f0c52fec59b714ea1a1c7f5f9928d33fd3")
    job4 = Mock(id="T123456-U78910-broken")
    scheduler = MagicMock()
    scheduler.get_jobs.return_value = [job1, job2, job3, job4]
    assert jobs.list_scheduled_jobs(scheduler, "T123456") == [job1, job2]


def fake_job(previous_user_picks=None):
    pass


def test_update_picker_rotation(scheduler):
    scheduler.add_job(fake_job, id="xxx", trigger="cron", day_of_week="*")
    event = JobExecutionEvent(
        EVENT_JOB_EXECUTED, "xxx", "default", datetime.now(), retval={"U1"}
    )
    jobs.update_picker_rotation(scheduler, event)

    job = scheduler.get_job("xxx")
    assert job.kwargs["previous_user_picks"] == {"U1"}
