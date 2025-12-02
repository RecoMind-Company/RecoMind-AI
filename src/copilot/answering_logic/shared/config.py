# shared/config.py
from urllib.parse import quote
import os
from dotenv import load_dotenv
from crewai.llm import LLM

load_dotenv()

# LLM Configuration
CREWAI_LLM_MODEL = os.getenv("crewai_LLM_MODEL", "gpt-3.5-turbo") 
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Database Configuration
VECTOR_DB_HOST = os.getenv("VECTOR_DB_HOST")
VECTOR_DB_NAME = os.getenv("VECTOR_DB_NAME")
VECTOR_DB_USER = os.getenv("VECTOR_DB_USER")
VECTOR_DB_PASSWORD = os.getenv("VECTOR_DB_PASSWORD")


def get_llm() -> LLM:
    """Returns a CrewAI-compatible LLM object."""
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
        f"@{VECTOR_DB_HOST}:6543/{VECTOR_DB_NAME}"
    )
