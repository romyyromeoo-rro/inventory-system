import json
import time
import uuid
from core.logger import logger
from redis_client import redis_client

NORMAL_QUEUE = "log_queue"
HIGH_QUEUE = "high_queue"
LOW_QUEUE = "low_queue"
FAILED_QUEUE = "failed_queue"
DELAYED_QUEUE = "delayed_queue"
PROCESSING_QUEUE = "processing_queue"
MAX_QUEUE_SIZE = 1000



def build_job(job: dict):
    job = {
        "job_id": str(uuid.uuid4()),
        "type": "log_action",
        "payload": job,
        "retry": 0,
        "created_at": int(time.time())

    }

    return job



def queue_is_full(queue_name):
    return (redis_client.llen(queue_name) >= MAX_QUEUE_SIZE)



def push_existing_job(job: dict, queue_name=NORMAL_QUEUE):
    redis_client.lpush(
        queue_name,
        json.dumps(job)
    )

    print(f"📨 Existing job moved to {queue_name}")


def push_task(job: dict, queue_name=NORMAL_QUEUE, delay=0):
    job = build_job(job)

    if not job:
        logger.error("failed build job")
        return False

    job["execute_at"] = int(time.time()) + delay

    if delay > 0:
        queue_name = DELAYED_QUEUE

    if queue_is_full(queue_name):
        redis_client.incr("metrics:queue_rejected")
        logger.warning(f"Queue full: {queue_name}")
        return False

    result = redis_client.lpush(
        queue_name,
        json.dumps(job)
    )

    print("LPUSH result:", result)
    print(f"📨 Job pushed to {queue_name}")


def calculate_backoff(retry: int):
    return 2 ** retry



def push_retry_job(job: dict):
    retry = job.get("retry", 1)

    delay = calculate_backoff(retry)

    job["execute_at"] = int(time.time()) + delay

    if not job:
        logger.error("Retry job is None")
        return False

    if queue_is_full(DELAYED_QUEUE):
        redis_client.incr("metrics:queue_rejected")
        logger.warning(f"Queue Full: {DELAYED_QUEUE}")
        return False

    redis_client.lpush(DELAYED_QUEUE, json.dumps(job))

    print(f"⏳ Retry scheduled in {delay} seconds")


def push_failed_job(job: dict):
    redis_client.lpush(FAILED_QUEUE, json.dumps(job))


def get_priority_queues():
    return [
        HIGH_QUEUE,
        NORMAL_QUEUE,
        LOW_QUEUE
    ]


def get_weighted_queues():
    return [
        HIGH_QUEUE,
        HIGH_QUEUE,
        NORMAL_QUEUE,
        HIGH_QUEUE,
        LOW_QUEUE
    ]

#def push_high_priority(data: dict):
    #job = {
        #"type": "log_action",
        #"payload": data,
        #"retry": 0,
        #"created_at": int(time.time())
    #}
    #redis_client.lpush(HIGH_QUEUE, json.dumps(job))



#def push_low_priority(data: dict):
    #job = {
        #"type": "log_action",
        #"payload": data,
        #"retry": 0,
        #"created_at": int(time.time())
    #}

    #redis_client.lpush(LOW_QUEUE, json.dumps(job))




#def push_log(data: dict):
    #print("🚨 MASUK PUSH_LOG:", data)
    #redis_client.rpush("log_queue", json.dumps(data))
