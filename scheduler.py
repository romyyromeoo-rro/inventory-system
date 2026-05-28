import json
import time
from core.logger import logger
from redis_client import redis_client
from services.task_queue import (
    DELAYED_QUEUE,
    push_existing_job
)


def scheduler():
    logger.info("Scheduler Started")

    while True:
        try:
            queue_size = redis_client.llen(DELAYED_QUEUE)
            redis_client.set(
                "metrics:retry_queue_size", queue_size
            )

            redis_client.set(
                "scheduler:heartbeat",
                time.time(),
                ex=10
            )
            jobs = redis_client.lrange(
                DELAYED_QUEUE,
                0,
                -1
            )

            if not jobs:
                time.sleep(1)
                continue

            for raw in jobs:
                try:
                    job = json.loads(raw)

                except json.JSONDecodeError:
                    logger.error("Invalid delayed job JSON")
                    continue

            now = int(time.time())

            execute_at = job.get("execute_at", now)
            if execute_at <= now:
                redis_client.lrem(
                    DELAYED_QUEUE,
                    1,
                    raw
                )
                push_existing_job(job)
                logger.info(
                    "Moved delayed job to processing queue"
                )
                redis_client.incr("metrics:scheduler_processed")
                time.sleep(0.1)

            else:
                logger.info(f"Retry delayed until {execute_at}")
                time.sleep(1)
                continue

        except Exception as e:
            logger.error(f"Scheduler Error: {e}")
            time.sleep(1)

