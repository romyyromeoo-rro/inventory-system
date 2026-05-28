from services.task_queue import (
    build_job,
    calculate_backoff,
    queue_is_full,
    push_failed_job,
    push_task,
    get_priority_queues,
    get_weighted_queues,
    HIGH_QUEUE,
    NORMAL_QUEUE,
    LOW_QUEUE,
    FAILED_QUEUE
)
from redis_client import redis_client
import json



def test_build_job():
    payload = {
        "username": "romeo",
        "action": "TEST"
    }

    job = build_job(payload)

    assert "job_id" in job
    assert job["type"] == "log_action"
    assert job["payload"] == payload
    assert job["retry"] == 0
    assert "created_at" in job


def test_calculate_backoff():
    assert calculate_backoff(1) == 2
    assert calculate_backoff(2) == 4
    assert calculate_backoff(3) == 8


def test_get_priority_queue():
    queues = get_priority_queues()

    assert HIGH_QUEUE in queues
    assert NORMAL_QUEUE in queues
    assert LOW_QUEUE in queues


def test_get_weighted_queues():
    queues = get_weighted_queues()

    assert len(queues) == 5
    assert queues.count(HIGH_QUEUE) == 3
    assert queues.count(NORMAL_QUEUE) == 1
    assert queues.count(LOW_QUEUE) == 1


def test_push_task():
    from services import task_queue
    TEST_QUEUE = "test_queue"
    redis_client.delete(TEST_QUEUE)
    payload = {
        "username": "romeo",
        "action": "TEST"
    }

    task_queue.push_task(
        payload,
        queue_name=TEST_QUEUE
    )
    queue_size = redis_client.llen(TEST_QUEUE)
    assert queue_size == 1
    job = redis_client.lindex(TEST_QUEUE, 0)
    job = json.loads(job)
    assert job["payload"] == payload
    redis_client.delete(TEST_QUEUE)


def test_push_failed_job():
    redis_client.delete(FAILED_QUEUE)
    job = {
        "job_id": "test-123",
        "payload": {
            "username": "romeo"
        }
    }

    push_failed_job(job)
    queue_size = redis_client.llen(FAILED_QUEUE)
    assert queue_size == 1


def test_queue_is_full():
    redis_client.delete("test_queue")
    assert queue_is_full("test_queue") is False
