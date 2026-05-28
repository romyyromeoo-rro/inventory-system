import os
import json
import traceback
import time
from core.logger import logger
from redis_client import redis_client
from core.exceptions import InvalidPayloadError
from services.job_handler import handle_log_action
from services.circuit_breaker import *
from services.task_queue import (
    PROCESSING_QUEUE,
    get_weighted_queues,
    get_priority_queues,
    push_retry_job,
    push_failed_job
)


QUEUE_NAME = "log_queue"
FAILED_QUEUE = "failed_queue"
MAX_RETRY = 3
WORKER_ID = os.getpid()



def process_job(job):
    WORKER_ID = os.getpid()

    #raise Exception("Test failed Job")

    logger.info(f"Worker {WORKER_ID} processing job")

    time.sleep(20)

    job_type = job.get("type")

    if job_type == "log_action":
        handle_log_action(job)

    else:
        raise Exception("Unknown job type")


def worker():
    WORKER_ID = os.getpid()

    logger.info(f"Worker {WORKER_ID} Started...")

    while True:
        redis_client.set(f"worker:{WORKER_ID}:heartbeat", time.time(), ex=10)

        queues = get_weighted_queues()

        data = redis_client.brpop(queues, timeout=5)

        if not data:
            continue

        queue_name, raw = data

        processing_job = {
            "worker_id": WORKER_ID,
            "started_processing_at": time.time(),
            "raw": raw
        }

        redis_client.lpush(
            PROCESSING_QUEUE,
            json.dumps(processing_job)
        )

        logger.info(
            f"Added job to processing_queue"
        )

        logger.info(f"FROM QUEUE: {queue_name}")

        try:
            job = json.loads(raw)
        except Exception as e:
            logger.error("Invalid JSON job")
            push_failed_job(job)

        if "type" not in job:
            logger.error("Invalid job format")
            continue

        logger.info(f"Worker {WORKER_ID} received job: {job}")

        redis_client.incr("metrics:processing")

        try:
            job["started_at"] = time.time()

            queue_latency = (
                job["started_at"] - job["created_at"]
            )
            job_id = job.get("job_id")

            if is_circuit_open():
                logger.warning("Circuit Open - Skipping Job")
                time.sleep(1)
                continue

            process_job(job)


            job["finished_at"] = time.time()

            processing_time = (
                job["finished_at"] - job["started_at"]
            )

            redis_client.incrbyfloat(
                "metrics:processing_time_total",
                processing_time
            )

            redis_client.incrbyfloat(
                "metrics:queue_latency_total",
                queue_latency
            )

            logger.info(f"Queue Latency: {queue_latency:.4f} sec")

            logger.info(
                f"Processing Time: {processing_time:.4f} sec"
            )

            logger.info(f"Worker {WORKER_ID} success: {job['type']}")

            redis_client.incr("metrics:success")

            #locked = redis_client.set(
                #f"processed_job:{job_id}",
                #1,
                #nx=True,
                #ex=3600
            #)

            #if not locked:
                #logger.warning(
                    #f"Duplicate job skipped:{job_id}"
                #)
                #continue

        except InvalidPayloadError as e:
            logger.error(f"Invalid Payload: {e}")

            push_failed_job(job)

            redis_client.incr("metrics:failed")

            logger.error("💀 Sent directly to DLQ")

        except Exception as e:
            retry = job.get("retry", 0) + 1

            job["retry"] = retry

            logger.error(f"ERROR: {e} | Retry: {retry}")
            traceback.print_exc()

            redis_client.incr("metrics:failed")

            if retry >= MAX_RETRY:
                redis_client.incr("metrics:dlq")
                push_failed_job(job)
                logger.error("Sent to DLQ")

            else:
                redis_client.incr("metrics:retry")
                push_retry_job(job)
                logger.warning(f"Requeued Retry={retry}")

        finally:
            redis_client.lrem(
                PROCESSING_QUEUE,
                1,
                json.dumps(processing_job)
            )

            redis_client.decr("metrics:processing")


