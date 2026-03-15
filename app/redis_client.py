import json
from app.config import get_settings

settings = get_settings()

try:
    import redis
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()  # Проверяем подключение
    redis_available = True
except:
    redis_available = False
    redis_client = None
    print("Redis не доступен, кэширование отключено")

def cache_link(short_code: str, original_url: str, ttl: int = 3600):
    if redis_available and redis_client:
        try:
            redis_client.setex(f"link:{short_code}", ttl, original_url)
        except:
            pass

def get_cached_link(short_code: str):
    if redis_available and redis_client:
        try:
            return redis_client.get(f"link:{short_code}")
        except:
            return None
    return None

def delete_cached_link(short_code: str):
    if redis_available and redis_client:
        try:
            redis_client.delete(f"link:{short_code}")
        except:
            pass

def cache_stats(short_code: str, stats: dict, ttl: int = 300):
    if redis_available and redis_client:
        try:
            redis_client.setex(f"stats:{short_code}", ttl, json.dumps(stats))
        except:
            pass

def get_cached_stats(short_code: str):
    if redis_available and redis_client:
        try:
            data = redis_client.get(f"stats:{short_code}")
            if data:
                return json.loads(data)
        except:
            return None
    return None
