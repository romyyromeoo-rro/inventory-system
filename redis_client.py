from core.config import config
import redis


print("REDIS_URL:", config.REDIS_URL)

redis_client = redis.from_url(
    config.REDIS_URL,
    decode_responses=True
)
