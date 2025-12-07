"""
Client for fetching database connection settings from the backend API
"""
import requests
import psycopg2
from config import settings


def fetch_source_db_settings(company_id: str):
    """
    Fetches the source database connection details from the backend API.
    
    Args:
        company_id: The company UUID to fetch settings for
        
    Returns:
        Dictionary with database connection settings
    """
    if not company_id:
        raise ValueError("company_id is required to fetch database settings")
    
    # Build the API URL with company_id
    api_url = settings.API_DB_SETTINGS_TEMPLATE.replace("{company_id}", company_id)
    
    print(f"Fetching database settings from API for company: {company_id}...")
    
    try:
        # No authentication needed based on test results
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        
        api_data = response.json()
        
        # API returns an array with one object
        if isinstance(api_data, list) and len(api_data) > 0:
            data = api_data[0]
        else:
            data = api_data
        
        print("✔ Successfully fetched database settings from API.")
        
        # Map the API response to our expected format
        return {
            "server": data.get("server"),
            "database": data.get("dbName"),
            "username": data.get("user"),
            "password": data.get("password"),
            "company_id": data.get("companyId")
        }

    except requests.exceptions.HTTPError as http_err:
        print(f"✖ HTTP error occurred while fetching settings: {http_err}")
        try:
            print(f"✖ Server Response Body: {http_err.response.text}")
        except Exception:
            print("✖ Could not retrieve additional error details from the server response.")
        raise
    except Exception as e:
        print(f"✖ An unexpected error occurred while fetching settings: {e}")
        raise


def save_settings_to_db(settings_dict):
    """
    Saves a given dictionary of settings into the 'source_connections' table.
    """
    if not all([settings.VECTOR_DB_HOST, settings.VECTOR_DB_NAME, settings.VECTOR_DB_USER, settings.VECTOR_DB_PASSWORD]):
        print("Destination DB connection details are missing. Cannot save settings.")
        return
    
    conn = None
    try:
        conn = psycopg2.connect(
            host=settings.VECTOR_DB_HOST, 
            dbname=settings.VECTOR_DB_NAME, 
            user=settings.VECTOR_DB_USER, 
            password=settings.VECTOR_DB_PASSWORD
        )
        cur = conn.cursor()
        
        company_id = settings_dict.get("company_id")
        
        if not company_id:
              print("✖ Error: 'company_id' is missing from settings dictionary. Cannot proceed with save/update.")
              return

        # DELETE existing entry for this company_id
        delete_query = "DELETE FROM source_connections WHERE company_id = %s;"
        cur.execute(delete_query, (company_id,))
        
        if cur.rowcount > 0:
              print(f"✔ Successfully deleted {cur.rowcount} old connection settings for company ID: {company_id}.")
        else:
              print(f"ℹ No existing connection settings found for company ID: {company_id}. Proceeding to insert.")


        # INSERT the new settings
        insert_query = "INSERT INTO source_connections (server, database, username, password, company_id) VALUES (%s, %s, %s, %s, %s);"
        data_tuple = (
            settings_dict["server"], settings_dict["database"],
            settings_dict["username"], settings_dict["password"],
            company_id 
        )
        cur.execute(insert_query, data_tuple)
        
        conn.commit()
        print("✔ New connection settings have been successfully saved to the database.")
        
    except (Exception, psycopg2.Error) as error:
        print(f"✖ Error while saving settings to PostgreSQL: {error}")
        if conn:
            conn.rollback()
            print("ℹ Transaction rolled back due to error.")
        raise 
    finally:
        if conn:
            cur.close()
            conn.close()
