"""Environment configuration and settings for reporting_system."""

import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# LLM Configuration
# =============================================================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", os.getenv("OPENAI_API_KEY", ""))
BASE_URL = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")
CREWAI_LLM_MODEL = os.getenv("crewai_LLM_MODEL", os.getenv("CREWAI_LLM_MODEL", "openai/gpt-4o-mini"))
LANGGRAPH_LLM_MODEL = os.getenv("langgraph_LLM_MODEL", os.getenv("LANGGRAPH_LLM_MODEL", "openai/gpt-4o-mini"))

# =============================================================================
# Vector Database (PostgreSQL with pgvector)
# =============================================================================
VECTOR_DB_HOST = os.getenv("VECTOR_DB_HOST", "localhost")
VECTOR_DB_NAME = os.getenv("VECTOR_DB_NAME", "postgres")
VECTOR_DB_USER = os.getenv("VECTOR_DB_USER", "postgres")
VECTOR_DB_PASSWORD = os.getenv("VECTOR_DB_PASSWORD", "")
VECTOR_DB_PORT = int(os.getenv("VECTOR_DB_PORT", "5432"))

# =============================================================================
# Embedding Model Configuration
# =============================================================================
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# =============================================================================
# Celery & Queue Configuration
# =============================================================================
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_QUEUE_NAME = "reporting_queue"
