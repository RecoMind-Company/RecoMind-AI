# embedding/config.py

import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv()

# =======================================================
# 1. Source Database Connection (SQL Server)
# =======================================================
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
COMPANY_ID = os.getenv("COMPANY_ID")

# =======================================================
# 2. Destination Vector DB Connection (PostgreSQL)
# =======================================================
VECTOR_DB_HOST = os.getenv("VECTOR_DB_HOST")
VECTOR_DB_NAME = os.getenv("VECTOR_DB_NAME")
VECTOR_DB_USER = os.getenv("VECTOR_DB_USER")
VECTOR_DB_PASSWORD = os.getenv("VECTOR_DB_PASSWORD")

# =======================================================
# 3. LLM Settings (OpenRouter)
# =======================================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
LLM_MODEL_NAME = "mistralai/mistral-7b-instruct:free"

# =======================================================
# 4. Embedding Model Settings
# =======================================================
EMBEDDING_MODEL_NAME = 'BAAI/bge-small-en-v1.5'

# =======================================================
# 5. Ingestion Process Settings
# =======================================================
# Number of tables to process in a single batch for LLM description generation
INGESTION_CHUNK_SIZE = 10