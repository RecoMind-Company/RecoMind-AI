# shared/config.py

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