"""
Core Configuration Module
=========================
Environment Variables and Settings Management
"""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # ===========================================
    # App Configuration
    # ===========================================
    APP_NAME: str = "planning-board"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ===========================================
    # API Configuration
    # ===========================================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8003
    API_PREFIX: str = "/api/v1"
    ROOT_PATH: str = "/planning_board"
    ALLOWED_ORIGINS: str = "*"

    # Service Authentication
    SERVICE_API_KEY: str = "planning-board-service-key-change-me"

    # ===========================================
    # LLM Configuration (OpenRouter)
    # ===========================================
    OPENROUTER_API_KEY: str = ""
    BASE_URL: str = "https://openrouter.ai/api/v1"
    MODEL_NAME: str = "openai/gpt-4o"

    # ===========================================
    # .NET Backend API
    # ===========================================
    DOTNET_API_BASE_URL: str = "https://api.recomind.site/api"
    DOTNET_TEAM_EMPLOYEES_URL_TEMPLATE: str = (
        "https://api.recomind.site/api/Team/{team_id}/company/{company_id}"
    )
    DOTNET_API_TOKEN: str = ""

    # ===========================================
    # Celery & Redis Configuration
    # ===========================================
    REDIS_HOST: str = "planning-board-redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://planning-board-redis:6379/0"

    CELERY_BROKER_URL: str = "redis://planning-board-redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://planning-board-redis:6379/0"
    CELERY_QUEUE_NAME: str = "planning_board_queue"

    # ===========================================
    # Timeouts & Rate Limiting
    # ===========================================
    LLM_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 120

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


# Global settings instance
settings = Settings()
