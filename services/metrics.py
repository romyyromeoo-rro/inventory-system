from redis_client import redis_client
from services.task_queue import (
    HIGH_QUEUE,
    NORMAL_QUEUE,
    LOW_QUEUE,
    FAILED_QUEUE,
    DELAYED_QUEUE
)

def get_metrics():
    success = int(redis_client.get("metrics:success") or 0)

    failed = int(redis_client.get("metrics:failed") or 0)

    retry = int(redis_client.get("metrics:retry") or 0)

    dlq = int(redis_client.get("metrics:dlq") or 0)

    processing = int(redis_client.get("metrics:processing") or 0)

    total_processing_time = float(redis_client.get("metrics:processing_time_total") or 0)

    total_queue_latency = float(redis_client.get("metrics:queue_latency_total") or 0)

    total_jobs = success + failed

    throughput = round(total_jobs / 60, 2)

    avg_processing_time = (
        total_processing_time / success
        if success > 0 else 0
    )

    avg_queue_latency = (
        total_queue_latency / success
        if success > 0 else 0
    )

    success_rate = (
        (success / total_jobs) * 100
        if total_jobs > 0 else 0
    )

    failure_rate = (
        (failed / total_jobs) * 100
        if total_jobs > 0 else 0
    )

    return {
        "processing": processing,
        "success": success,
        "failed": failed,
        "retry": retry,
        "dlq": dlq,
        "throughput_per_minute": throughput,
        "high_queue": redis_client.llen(HIGH_QUEUE),
        "queue_rejected": int(redis_client.get("metrics:queue_rejected") or 0),
        "normal_queue": redis_client.llen(NORMAL_QUEUE),
        "low_queue": redis_client.llen(LOW_QUEUE),
        "failed_queue": redis_client.llen(FAILED_QUEUE),
        "delayed_queue": redis_client.llen(DELAYED_QUEUE),
        "avg_processing_time": round(avg_processing_time, 4),
        "avg_queue_latency": round(avg_queue_latency, 4),
        "success_rate": round(success_rate, 2),
        "failure_rate": round(failure_rate, 2)
    }
