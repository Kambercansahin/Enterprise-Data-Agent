import os
import json
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

def get_cache_key(question: str) -> str:
    normalized = question.strip().lower()
    return f"agent_cache:{normalized}"

def get_cached_response(question: str) -> dict | None:
    try:
        data = redis_client.get(get_cache_key(question))
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"Redis get hatası: {e}")
    return None

def set_cached_response(question: str, data: dict, ttl_seconds: int = 600):
    try:
        redis_client.setex(
            name=get_cache_key(question),
            time=ttl_seconds,
            value=json.dumps(data)
        )
    except Exception as e:
        print(f"Redis set hatası: {e}")