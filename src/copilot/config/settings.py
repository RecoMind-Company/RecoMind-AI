# config/settings.py
"""Environment configuration and settings."""

import os
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# LLM Configuration
# =============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CREWAI_LLM_MODEL = os.getenv("crewai_LLM_MODEL", "gpt-3.5-turbo")
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1")


# =============================================================================
# Vector Database (PostgreSQL with pgvector)
# =============================================================================
VECTOR_DB_HOST = os.getenv("VECTOR_DB_HOST")
VECTOR_DB_NAME = os.getenv("VECTOR_DB_NAME")
VECTOR_DB_USER = os.getenv("VECTOR_DB_USER")
VECTOR_DB_PASSWORD = os.getenv("VECTOR_DB_PASSWORD")
VECTOR_DB_PORT = int(os.getenv("VECTOR_DB_PORT", "6543"))


# =============================================================================
# Embedding Model
# =============================================================================
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
