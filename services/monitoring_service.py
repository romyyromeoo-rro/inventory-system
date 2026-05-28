from services.task_queue import FAILED_QUEUE
from core.logger import logger
from redis_client import redis_client
import time
import json

QUEUE_NAME = "log_queue"

def get_queue_stats():
    return {
        "high":redis_client.llen("high_queue"),
        "normal":redis_client.llen("log_queue"),
        "low":redis_client.llen("low_queue"),
        "failed":redis_client.llen("failed_queue")
    }


def get_failed_jobs():
    jobs = redis_client.lrange(
        FAILED_QUEUE,
        0,
        -1
    )

    parsed_jobs = []

    for job in jobs:
        try:
            parsed_jobs.append(json.loads(job))
        except:
            pass

    return {
        "failed_jobs": parsed_jobs,
        "total": len(parsed_jobs)
    }




def get_worker_status():
    keys = redis_client.keys("worker:*:heartbeat")

    if not keys:
        return {
            "status": "down",
            "workers": 0
        }

    active_workers = 0
    workers = []

    for key in keys:
        value = redis_client.get(key)

        if not value:
            continue

        last_seen = float(value)
        delta = time.time()- last_seen
        alive = delta < 10

        if alive:
            active_workers += 1

    worker_id = key.split(":")[1]

    workers.append({
        "worker_id": worker_id,
        "alive": alive,
        "last_seen_seconds": round(delta, 2)
    })

    status = (
        "running"
        if active_workers > 0
        else "down"
    )

    scheduler_alive = redis_client.exists(
        "scheduler:heartbeat"
    )

    return {
        "status": status,
        "workers": workers,
        "active_workers": active_workers,
        "scheduler": {
            "alive": bool(scheduler_alive)
        }
    }


