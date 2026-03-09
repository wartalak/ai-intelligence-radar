"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Database ──
    DATABASE_URL: str = "postgresql+asyncpg://radar:radar@localhost:5432/ai_radar"
    DATABASE_URL_SYNC: str = "postgresql://radar:radar@localhost:5432/ai_radar"

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── OpenAI (embeddings) ──
    OPENAI_API_KEY: str = ""

    # ── Google Gemini (LLM) ──
    GEMINI_API_KEY: str = ""

    # ── YouTube ──
    YOUTUBE_API_KEY: str = ""

    # ── Twitter / X ──
    TWITTER_BEARER_TOKEN: str = ""

    # ── GitHub ──
    GITHUB_TOKEN: str = ""

    # ── App ──
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    ENVIRONMENT: str = "development"

    # ── Embedding ──
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536

    # ── LLM ──
    LLM_MODEL: str = "gemini-2.0-flash"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
