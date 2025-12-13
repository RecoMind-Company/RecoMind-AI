# config/database.py
"""Database connection utilities."""

from urllib.parse import quote
from crewai.llm import LLM
from config.settings import (
    OPENAI_API_KEY,
    CREWAI_LLM_MODEL,
    BASE_URL,
    VECTOR_DB_HOST,
    VECTOR_DB_NAME,
    VECTOR_DB_USER,
    VECTOR_DB_PASSWORD,
    VECTOR_DB_PORT,
)


def get_llm() -> LLM:
    """Returns a CrewAI-compatible LLM instance."""
    return LLM(
        model=CREWAI_LLM_MODEL,
        base_url=BASE_URL,
        api_key=OPENAI_API_KEY,
    )


def get_vector_db_url() -> str:
    """Returns SQLAlchemy connection URL for PostgreSQL metadata database."""
    encoded_password = quote(VECTOR_DB_PASSWORD)
    return (
        f"postgresql://{VECTOR_DB_USER}:{encoded_password}"
        f"@{VECTOR_DB_HOST}:{VECTOR_DB_PORT}/{VECTOR_DB_NAME}"
    )


def get_vector_db_params() -> dict:
    """Returns connection parameters for psycopg2."""
    return {
        "host": VECTOR_DB_HOST,
        "database": VECTOR_DB_NAME,
        "user": VECTOR_DB_USER,
        "password": VECTOR_DB_PASSWORD,
        "port": VECTOR_DB_PORT,
    }
