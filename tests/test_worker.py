from worker import process_job
from unittest.mock import patch
import pytest


@patch("worker.time.sleep", return_value=None)
def test_process_job_log_action(mock_sleep):
    job = {
        "type": "log_action",
        "payload": {
            "username": "romeo",
            "action": "TEST"
        }
    }

    process_job(job)


@patch("worker.time.sleep", return_value=None)
def test_process_job_unknown_type(mock_sleep):
    job = {
        "type": "unknown_type"
    }

    with pytest.raises(Exception):
        process_job(job)
