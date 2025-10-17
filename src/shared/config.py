# shared/config.py

import os
import requests
import psycopg2
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv()

# =======================================================
# 1. API and Destination DB Connection
# =======================================================
API_URL = os.getenv("API_URL")
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN")

# Destination Vector DB Connection (PostgreSQL) - These are still needed to save the settings
VECTOR_DB_HOST = os.getenv("VECTOR_DB_HOST")
VECTOR_DB_NAME = os.getenv("VECTOR_DB_NAME")
VECTOR_DB_USER = os.getenv("VECTOR_DB_USER")
VECTOR_DB_PASSWORD = os.getenv("VECTOR_DB_PASSWORD")

# =======================================================
# 2. Function to Fetch Source Database Settings from API
# =======================================================
def fetch_source_db_settings():
    """
    Fetches the source database connection details from the backend API.
    """
    if not API_URL or not API_AUTH_TOKEN:
        raise ValueError("API_URL and API_AUTH_TOKEN must be set in the .env file.")

    headers = {
        'accept': '*/*',
        'Authorization': f'Bearer {API_AUTH_TOKEN}'
    }
    
    print("Fetching database settings from API...")
    try:
        response = requests.get(API_URL, headers=headers, timeout=30)
        response.raise_for_status()  
        
        api_data = response.json()
        print("Successfully fetched settings from API.")
        
        settings = {
            "server": api_data.get("server"),
            "database": api_data.get("databaseName"), 
            "username": api_data.get("user"),       
            "password": api_data.get("password"),
            "company_id": api_data.get("companyId")
        }
        return settings

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred while fetching API data: {http_err}")
        print(f"Response Body: {http_err.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"A critical error occurred while fetching API data: {e}")
        return None

# =======================================================
# 3. Function to Save Settings to Destination PostgreSQL DB
# =======================================================
def save_settings_to_db(settings_dict):
    """
    Saves a given dictionary of settings as a new row in the 'source_connections' table.
    """
    if not all([VECTOR_DB_HOST, VECTOR_DB_NAME, VECTOR_DB_USER, VECTOR_DB_PASSWORD]):
        print("Destination DB connection details are missing in .env file. Cannot save settings.")
        return

    conn = None
    try:
        conn = psycopg2.connect(
            host=VECTOR_DB_HOST, dbname=VECTOR_DB_NAME,
            user=VECTOR_DB_USER, password=VECTOR_DB_PASSWORD
        )
        cur = conn.cursor()

        insert_query = """
        INSERT INTO source_connections (server, database, username, password, company_id)
        VALUES (%s, %s, %s, %s, %s);
        """
        data_tuple = (
            settings_dict["server"], settings_dict["database"],
            settings_dict["username"], settings_dict["password"],
            settings_dict["company_id"]
        )
        cur.execute(insert_query, data_tuple)
        conn.commit()
        print("Connection settings have been successfully saved to the database.")

    except (Exception, psycopg2.Error) as error:
        print(f"Error while saving settings to PostgreSQL: {error}")
    finally:
        if conn:
            cur.close()
            conn.close()

# =======================================================
# 4. Initialize Source Database Variables by calling the API
# =======================================================
# This code runs automatically when the module is imported
source_settings = fetch_source_db_settings()

if source_settings:
    DB_SERVER = source_settings.get("server")
    DB_DATABASE = source_settings.get("database")
    DB_USERNAME = source_settings.get("username")
    DB_PASSWORD = source_settings.get("password")
    COMPANY_ID = source_settings.get("company_id")
else:
    DB_SERVER = DB_DATABASE = DB_USERNAME = DB_PASSWORD = COMPANY_ID = None
    print("FATAL: Could not initialize source database settings from API. Pipeline might fail.")