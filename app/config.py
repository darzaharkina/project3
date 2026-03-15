from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@db:5432/urlshortener"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # App
    BASE_URL: str = "http://localhost:8000"
    DEFAULT_EXPIRY_DAYS: int = 30  # для неиспользуемых ссылок
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
