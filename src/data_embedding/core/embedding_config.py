# src/recomind/data_embedding/core/embedding_components.py

import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv()

# =======================================================
# 1. LLM For data-embedding description generation
# =======================================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
LLM_MODEL_NAME = "mistralai/mistral-7b-instruct:free"

# =======================================================
# 2. Embedding Model Settings
# =======================================================
EMBEDDING_MODEL_NAME = 'BAAI/bge-small-en-v1.5'

# =======================================================
# 3. Ingestion Process Settings
# =======================================================
# Number of tables to process in a single batch for LLM description generation
INGESTION_CHUNK_SIZE = 10