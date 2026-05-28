from core.config import config
import redis

redis_client = redis.from_url(
    config.REDIS_URL,
    decode_responses=True
)
