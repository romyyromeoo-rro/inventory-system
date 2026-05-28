import json
import time
from core.logger import logger
from redis_client import redis_client
from services.task_queue import (
    PROCESSING_QUEUE,
    push_existing_job
)

STUCK_TIMEOUT = 30

def recover_stuck_jobs():
    jobs = redis_client.lrange(
        PROCESSING_QUEUE,
        0,
        -1
    )

    recovered = 0

    for item in jobs:
        try:
            processing_job = json.loads(item)
            worker_id = processing_job["worker_id"]
            started_processing_at = (
                processing_job["started_processing_at"]
            )

            raw = processing_job["raw"]
            worker_heartbeat = redis_client.get(
                f"worker:{worker_id}:heartbeat"
            )

            now = time.time()

            stuck = (now - started_processing_at) > STUCK_TIMEOUT

            worker_dead = not worker_heartbeat

            if stuck and worker_dead:
                job = json.loads(raw)
                push_existing_job(job)
                redis_client.lrem(
                    PROCESSING_QUEUE,
                    1,
                    item
                )

                redis_client.incr(
                    "metrics:recovered_jobs"
                )

                logger.warning(
                    f"Recovered stuck job"
                    f"from worker={worker_id}"
                )

                recovered += 1

        except Exception as e:
            logger.error(f"Recovery Error: {e}")

    return recovered
