# data_embedding/shared/config.py

import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv()

# --- API Settings ---

# This is the main endpoint we hit to get the database settings
API_GETDATA = os.getenv("API_GETDATA")

# This is the authentication endpoint
API_LOGIN = os.getenv("API_LOGIN")

# Credentials for the dynamic login
API_EMAIL = os.getenv("API_EMAIL")
API_PASSWORD = os.getenv("API_PASSWORD")


# --- Destination Vector DB Connection (PostgreSQL) ---
# This part remains the same, as it's our target database.
VECTOR_DB_HOST = os.getenv("VECTOR_DB_HOST")
VECTOR_DB_NAME = os.getenv("VECTOR_DB_NAME")
VECTOR_DB_USER = os.getenv("VECTOR_DB_USER")
VECTOR_DB_PASSWORD = os.getenv("VECTOR_DB_PASSWORD")