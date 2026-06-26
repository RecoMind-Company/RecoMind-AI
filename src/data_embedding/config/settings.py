"""
Application configuration settings
Merges all config from embedding_config.py and shared/config.py
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================================================
# LLM Configuration (for description generation)
# ============================================================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "mistralai/mistral-nemo")


# ============================================================================
# Embedding Model Configuration
# ============================================================================
EMBEDDING_MODEL_NAME = 'BAAI/bge-small-en-v1.5'


# ============================================================================
# Pipeline Processing Configuration
# ============================================================================
# Number of tables to process in a single batch for LLM description generation
INGESTION_CHUNK_SIZE = 10

# Team assignment similarity threshold (0.0 - 1.0)
TEAM_ASSIGNMENT_THRESHOLD = 0.6

# Maximum number of teams to assign per table
MAX_TEAMS_PER_TABLE = 3


# ============================================================================
# External API Configuration
# ============================================================================
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.recomind.site/api")

# API endpoint templates (company_id will be replaced dynamically)
API_DB_SETTINGS_TEMPLATE = os.getenv(
    "API_DB_SETTINGS",
    "https://api.recomind.site/api/DbSetting/company/{company_id}"
)
API_TEAMS_TEMPLATE = os.getenv(
    "API_TEAMS",
    "https://api.recomind.site/api/Team/company/{company_id}/for-ai-model"
)


# ============================================================================
# Vector Database Configuration (PostgreSQL with pgvector)
# ============================================================================
VECTOR_DB_HOST = os.getenv("VECTOR_DB_HOST")
VECTOR_DB_NAME = os.getenv("VECTOR_DB_NAME")
VECTOR_DB_USER = os.getenv("VECTOR_DB_USER")
VECTOR_DB_PASSWORD = os.getenv("VECTOR_DB_PASSWORD")


# ============================================================================
# Celery Configuration
# ============================================================================
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://recomind-ingestion-redis:6379/0")
