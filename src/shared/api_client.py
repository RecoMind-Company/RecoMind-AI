# shared/api_client.py

import requests
import psycopg2
from . import config

def fetch_source_db_settings():
    """
    Fetches the source database connection details from the backend API.
    """
    if not config.API_URL or not config.API_AUTH_TOKEN: 
        raise ValueError("API_URL and API_AUTH_TOKEN must be set in the .env file.")

    headers = {
        'accept': '*/*',
        'Authorization': f'Bearer {config.API_AUTH_TOKEN}'
    }
    
    print("Fetching database settings from API...")
    try:
        response = requests.get(config.API_URL, headers=headers, timeout=30)
        # This will raise an error for 4xx or 5xx status codes
        response.raise_for_status()
        
        api_data = response.json()
        print("Successfully fetched settings from API.")
        
        return {
            "server": api_data.get("server"),
            "database": api_data.get("databaseName"),
            "username": api_data.get("user"),
            "password": api_data.get("password"),
            "company_id": api_data.get("companyId")
        }
    # This block specifically catches server/client errors and prints the response body
    except requests.exceptions.HTTPError as http_err:
        print(f"✖ HTTP error occurred: {http_err}")
        try:
            # Try to print the detailed error message from the server
            print(f"✖ Server Response Body: {http_err.response.text}")
        except Exception:
            print("✖ Could not retrieve additional error details from the server response.")
        return None
    except Exception as e:
        print(f"✖ An unexpected error occurred: {e}")
        return None


def save_settings_to_db(settings_dict):
    """
    Saves a given dictionary of settings as a new row in the 'source_connections' table.
    """
    if not all([config.VECTOR_DB_HOST, config.VECTOR_DB_NAME, config.VECTOR_DB_USER, config.VECTOR_DB_PASSWORD]):
        print("Destination DB connection details are missing. Cannot save settings.")
        return
    
    conn = None
    try:
        conn = psycopg2.connect(
            host=config.VECTOR_DB_HOST, 
            dbname=config.VECTOR_DB_NAME, 
            user=config.VECTOR_DB_USER, 
            password=config.VECTOR_DB_PASSWORD
        )
        cur = conn.cursor()
        insert_query = "INSERT INTO source_connections (server, database, username, password, company_id) VALUES (%s, %s, %s, %s, %s);"
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