from redis_client import redis_client
import time

def blacklist_token(jti: str, exp: int):
    """
    Simpan token ke Redis sampai expired.
    """
    current_time = int(time.time())
    ttl = exp - current_time

    if ttl > 0:
        redis_client.setex(f"blacklist:{jti}", ttl, "1")

def is_token_blacklisted(jti: str):
    return redis_client.exists(f"blacklist:{jti}") == 1
