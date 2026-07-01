"""
Core Configuration Module
==========================
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
        extra="ignore",
    )

    # ===========================================
    # App Configuration
    # ===========================================
    APP_NAME: str = "validation"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ===========================================
    # API Configuration
    # ===========================================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8004
    API_PREFIX: str = "/api/v1"
    ROOT_PATH: str = "/validation"
    ALLOWED_ORIGINS: str = "*"

    # Service Authentication
    SERVICE_API_KEY: str = "validation-service-key-change-me"

    # ===========================================
    # LLM Configuration (Groq)
    # ===========================================
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 3

    # ===========================================
    # .NET Backend API
    # ===========================================
    DOTNET_API_BASE_URL: str = ""
    DOTNET_AUTH_ENDPOINT: str = ""
    DOTNET_COMPANY_ENDPOINT: str = ""
    DOTNET_REPORTS_ENDPOINT: str = ""

    # Authentication
    AUTH_EMAIL: str = ""
    AUTH_PASSWORD: str = ""

    # Report Retrieval
    REPORT_LIMIT: int = 2

    # ===========================================
    # Search Configuration (Precedent Engine)
    # ===========================================
    SERPER_API_KEY: str = ""
    SEARCH_TIMEOUT: int = 10
    SEARCH_MAX_WORKERS: int = 4
    MIN_PRECEDENT_CASES: int = 3
    MAX_PRECEDENT_CASES: int = 7
    TARGET_PRECEDENT_CASES: int = 5

    # ===========================================
    # Celery & Redis Configuration
    # ===========================================
    REDIS_HOST: str = "validation-redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://validation-redis:6379/0"

    CELERY_BROKER_URL: str = "redis://validation-redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://validation-redis:6379/0"
    CELERY_QUEUE_NAME: str = "validation_queue"

    # ===========================================
    # Timeouts & Rate Limiting
    # ===========================================
    REQUEST_TIMEOUT: int = 120
    AUTH_TOKEN_CACHE_TTL: int = 3600

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


# Global settings instance
settings = Settings()
