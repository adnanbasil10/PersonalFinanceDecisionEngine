"""
Core configuration module.
Uses Pydantic BaseSettings for type-safe environment variable management.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Personal Finance Decision Engine"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://finuser:finpass@localhost:5432/finance_engine"
    SQLITE_FALLBACK: bool = False

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Redis
    REDIS_URL: Optional[str] = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def effective_database_url(self) -> str:
        """Return SQLite URL if fallback is enabled or Postgres is unavailable."""
        if self.SQLITE_FALLBACK:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "finance_engine.db")
            return f"sqlite:///{db_path}"
        return self.DATABASE_URL

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
