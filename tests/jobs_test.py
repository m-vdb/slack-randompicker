from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest
from recurrent import RecurringEvent

from randompicker import jobs


rec_event = RecurringEvent()
rec_event.parse("every day at 9am")
test_frequencies = [
    (
        datetime(2020, 6, 10, 12),
        "T123456-U78910-545d7adf4cc8a00f42b4f514d03e54b501c7a63d",
    ),
    (rec_event, "T123456-U78910-0a0ca9f0c52fec59b714ea1a1c7f5f9928d33fd3"),
]


@pytest.mark.parametrize("frequency,expected", test_frequencies)
def test_make_job_id(frequency, expected):
    assert jobs.make_job_id("T123456", "U78910", "play music", frequency) == expected


def test_list_user_jobs():
    job1 = Mock(id="T123456-U78910-0a0ca9f0c52fec59b714ea1a1c7f5f9928d33fd3")
    job2 = Mock(id="T123456-U78911-0a0ca9f0c52fec59b714ea1a1c7f5f9928d33fd3")
    job3 = Mock(id="T123457-U78910-0a0ca9f0c52fec59b714ea1a1c7f5f9928d33fd3")
    job4 = Mock(id="T123456-U78910-broken")
    scheduler = MagicMock()
    scheduler.get_jobs.return_value = [job1, job2, job3, job4]
    assert jobs.list_user_jobs(scheduler, "T123456", "U78910") == [job1]
    assert jobs.list_user_jobs(scheduler, "T123456", None) == [job1, job2]
