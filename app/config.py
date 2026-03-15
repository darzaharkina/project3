from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@db:5432/urlshortener"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    BASE_URL: str = "http://localhost:8000"
    DEFAULT_EXPIRY_DAYS: int = 30
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():  # <-- ИЗМЕНИТЕ ЗДЕСЬ: было get_current_settings, должно быть get_settings
    return Settings()
