from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    DEBUG: bool = False
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
