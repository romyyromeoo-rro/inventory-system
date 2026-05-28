from redis_client import redis_client

redis_client.delete("log_queue")
print("✅ Queue cleared")
