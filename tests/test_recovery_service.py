import json
import time
from redis_client import redis_client
from services.recovery_service import (
    recover_stuck_jobs,
    PROCESSING_QUEUE
)


def test_recover_stuck_jobs():
    TEST_QUEUE = "test_recovery_queue"
    redis_client.delete(PROCESSING_QUEUE)
    redis_client.delete(TEST_QUEUE)
    redis_client.delete("metrics:recovered_jobs")

    job = {
        "job_id": "test-123",
        "type": "log_action",
        "payload": {
            "username": "romeo",
            "action": "TEST"
        },
        "retry": 0,
        "created_at": int(time.time())
    }

    processing_job = {
        "worker_id": 999999,
        "started_processing_at": time.time() - 60,
        "raw": json.dumps(job)
    }

    redis_client.lpush(
        PROCESSING_QUEUE,
        json.dumps(processing_job)
    )

    recovered = recover_stuck_jobs()
    assert recovered == 1
    recovered_jobs = redis_client.get("metrics:recovered_jobs")
    assert int(recovered_jobs) == 1
    remaining = redis_client.llen(PROCESSING_QUEUE)
    assert remaining == 0
