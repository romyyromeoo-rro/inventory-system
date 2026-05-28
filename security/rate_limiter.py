from redis_client import redis_client
import time

def is_rate_limited(key: str, limit: int=5, window:
int = 10):
    """
    key: identifier (ip / username)
    limit: max request
    window: time window (seconds)
    """
    current = redis_client.get(key)

    if current and int(current) >= limit:
        return True

    pipe = redis_client.pipeline()
    pipe.incr(key, 1)
    pipe.expire(key, window)
    pipe.execute()

    return False
