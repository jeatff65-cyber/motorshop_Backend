"""Application settings loaded from file.env."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Backend/ folder (two levels up from this file: app/core/config.py -> Backend/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / "file.env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Book Store API"
    API_V1_PREFIX: str = "/api/v1"

    # Render PostgreSQL
    DATABASE_URL: str = (
        "postgresql://bookstore_rxpj_user:YOUR_DATABASE_PASSWORD"
        "@dpg-da2ma2gae00c73cg0q50-a:5432/bookstore_rxpj"
    )

    # JWT
    SECRET_KEY: str = "bookstore-secret-key-change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours


@lru_cache
def get_settings() -> Settings:
    return Settings()
