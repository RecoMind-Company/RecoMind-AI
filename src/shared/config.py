# shared/config.py

import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv()

# --- Static Configuration (Always Loaded) ---

# API Settings (URLs and Keys, but no actions)
API_URL = os.getenv("API_URL")
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN")

# Destination Vector DB Connection (PostgreSQL)
VECTOR_DB_HOST = os.getenv("VECTOR_DB_HOST")
VECTOR_DB_NAME = os.getenv("VECTOR_DB_NAME")
VECTOR_DB_USER = os.getenv("VECTOR_DB_USER")
VECTOR_DB_PASSWORD = os.getenv("VECTOR_DB_PASSWORD")