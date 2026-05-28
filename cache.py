from redis_client import redis_client
import json

def get_cache(key):
    data = redis_client.get(key)
    return json.loads(data) if data else None

def set_cache(key, value, ttl=60):
    redis_client.setex(key, ttl, json.dumps(value))
