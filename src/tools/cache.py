import os
import json
import redis

REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
else:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True
    )

def get_cache_key(question: str,thread_id: str | None = None) -> str:
    normalized = question.strip().lower()
    if thread_id:
        return f"agent_cache:{thread_id}:{normalized}"
    return f"agent_cache:{normalized}"

def get_cached_response(question: str,thread_id: str | None = None) -> dict | None:
    try:
        data = redis_client.get(get_cache_key(question,thread_id))
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"Redis get hatası: {e}")
    return None

def set_cached_response(question: str, data: dict, ttl_seconds: int = 600,thread_id: str | None = None):
    try:
        redis_client.setex(
            name=get_cache_key(question,thread_id),
            time=ttl_seconds,
            value=json.dumps(data)
        )
    except Exception as e:
        print(f"Redis set hatası: {e}")