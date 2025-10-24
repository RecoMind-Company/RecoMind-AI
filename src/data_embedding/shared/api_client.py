import requests
import psycopg2
from . import config

def _fetch_auth_token():
    """
    Internal helper function to log into the API dynamically.
    """
    if not all([config.API_LOGIN, config.API_EMAIL, config.API_PASSWORD]):
        raise ValueError("API_LOGIN, API_EMAIL, and API_PASSWORD must be set in the .env file.")

    login_payload = {
        "email": config.API_EMAIL,
        "password": config.API_PASSWORD
    }
    
    print("Attempting to fetch dynamic auth token...")
    try:
        # Tweak: Use .strip() to clean up URLs from .env file (removes spaces/quotes)
        login_url = config.API_LOGIN.strip().strip('"')
        response = requests.post(login_url, json=login_payload, timeout=20)
        
        response.raise_for_status() 
        
        response_data = response.json()
        token = response_data.get("token")
        
        if not token:
            print(f"✖ Login was successful, but the 'token' key was not found in the response.")
            print(f"✖ API Response Body: {response_data}")
            raise Exception("Token missing in API login response.")
        
        print("✔ Successfully fetched new auth token.")
        return token

    except requests.exceptions.HTTPError as http_err:
        print(f"✖ HTTP error occurred during login: {http_err}")
        try:
            print(f"✖ Server Response Body: {http_err.response.text}")
        except Exception:
            pass 
        raise # Final Change: Raise exception instead of return None
    except Exception as e:
        print(f"✖ An unexpected error occurred during login: {e}")
        raise # Final Change: Raise exception instead of return None


def fetch_source_db_settings():
    """
    Fetches the source database connection details from the backend API.
    """
    # Step 1: Get the dynamic authentication token first.
    try:
        auth_token = _fetch_auth_token()
    except Exception as e:
        print(f"✖ Aborting settings fetch: Login failed due to: {e}")
        raise 

    if not auth_token:
        print("✖ Aborting settings fetch: Could not retrieve auth token.")
        return  

    # Step 2: Check for the data endpoint URL.
    if not config.API_GETDATA: 
        raise ValueError("API_GETDATA must be set in the .env file.")

    # Step 3: Use the new dynamic token in the headers.
    headers = {
        'accept': '*/*',
        'Authorization': f'Bearer {auth_token}'
    }
    
    print("Fetching database settings from API...")
    try:
        # Tweak: Use .strip() to clean up URLs from .env file (removes spaces/quotes)
        data_url = config.API_GETDATA.strip().strip('"')
        response = requests.get(data_url, headers=headers, timeout=30)
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

    except requests.exceptions.HTTPError as http_err:
        print(f"✖ HTTP error occurred while fetching settings: {http_err}")
        try:
            print(f"✖ Server Response Body: {http_err.response.text}")
        except Exception:
            print("✖ Could not retrieve additional error details from the server response.")
        raise # Final Change: Raise exception instead of return None
    except Exception as e:
        print(f"✖ An unexpected error occurred while fetching settings: {e}")
        raise # Final Change: Raise exception instead of return None


def save_settings_to_db(settings_dict):
    """
    Saves a given dictionary of settings into the 'source_connections' table.
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
