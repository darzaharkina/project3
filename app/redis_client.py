import redis
import json
from app.config import get_settings

settings = get_settings()

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_redis():
    return redis_client

def cache_link(short_code: str, original_url: str, ttl: int = 3600):
    """Кэширование ссылки на 1 час"""
    redis_client.setex(f"link:{short_code}", ttl, original_url)

def get_cached_link(short_code: str):
    """Получение ссылки из кэша"""
    return redis_client.get(f"link:{short_code}")

def delete_cached_link(short_code: str):
    """Удаление ссылки из кэша"""
    redis_client.delete(f"link:{short_code}")

def cache_stats(short_code: str, stats: dict, ttl: int = 300):
    """Кэширование статистики на 5 минут"""
    redis_client.setex(f"stats:{short_code}", ttl, json.dumps(stats))

def get_cached_stats(short_code: str):
    """Получение статистики из кэша"""
    data = redis_client.get(f"stats:{short_code}")
    if data:
        return json.loads(data)
    return None
