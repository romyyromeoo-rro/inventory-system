import time
from redis_client import redis_client

FAILURE_THRESHOLD = 5
RECOVERY_TIMEOUT = 30


def is_circuit_open():
    opened_at = redis_client.get("circuit:opened_at")
    if not opened_at:
        return False

    opened_at = float(opened_at)
    now = time.time()

    if now - opened_at > RECOVERY_TIMEOUT:
        close.circuit()
        return False
    return True


def open_circuit():
    redis_client.set(
        "circuit:opened_at", time.time()
    )
    print("Circuit opened")


def close_circuit():
    redis_client.delete("circuit:opened_at")
    redis_client.delete(
        "circuit:failure_count"
    )
    print("Circuit Closed")


def record_failure():
    failures = redis_client.incr(
        "circuit:failure_count"
    )
    if failures >= FAILURE_THRESHOLD:
        open.circuit()


def record_succes():
    redis_client.delete(
        "circuit:failure_count"
    )
