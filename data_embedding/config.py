import os
from dotenv import load_dotenv

# Load environment variables from .env file (assuming .env is in the project root)
# Note: When running from 'ingestion/' directory, you might need load_dotenv(dotenv_path='../.env')
load_dotenv() 

# =======================================================
# 1. PostgreSQL Connection (Vector DB)
# =======================================================
VECTOR_DB_HOST = os.getenv("VECTOR_DB_HOST")
VECTOR_DB_NAME = os.getenv("VECTOR_DB_NAME")
VECTOR_DB_USER = os.getenv("VECTOR_DB_USER")
VECTOR_DB_PASSWORD = os.getenv("VECTOR_DB_PASSWORD")

# =======================================================
# 2. SQL Server Connection (Source Schema)
# =======================================================
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
COMPANY_ID = os.getenv("COMPANY_ID")

# =======================================================
# 3. OpenRouter LLM Settings for Schema Description
# =======================================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL_NAME = "mistralai/mistral-7b-instruct:free" 
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"