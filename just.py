from redis_client import redis_client

print(redis_client.llen("log_queue"))
