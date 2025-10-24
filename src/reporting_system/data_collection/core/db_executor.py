import os
import pyodbc
import pandas as pd
from typing import Any, Optional, Dict
import time # === MODIFICATION START: Added import for retry logic ===
import re # === MODIFICATION START: Added import for regex cleaning ===

def execute_query_to_dataframe(query: Any, db_settings: Dict[str, str]) -> Optional[pd.DataFrame]:
    """
    Executes a SQL query against the database and returns the results as a pandas DataFrame.
    
    Args:
        query (Any): The valid SQL query to execute.
        db_settings (Dict[str, str]): A dictionary with DB connection details.
        
    Returns:
        Optional[pd.DataFrame]: A DataFrame containing the query results, or None on failure.
    """
    
    # === MODIFICATION START: Added retry logic ===
    MAX_RETRIES = 3
    # === MODIFICATION END ===

    cnxn = None
    
    # === FIX 1: Check for the correct key names with the 'db_' prefix ===
    required_keys = ["db_server", "db_database", "db_username", "db_password"]
    if not all(k in db_settings for k in required_keys):
        raise ValueError("Missing required DB connection keys in db_settings dictionary.")

    query_str = str(query)

    # === MODIFICATION START: Clean potential markdown from the query string ===
    # This searches for a SQL block, extracts it, and strips whitespace.
    match = re.search(r'```(sql\s*)?([\s\S]*?)```', query_str, re.IGNORECASE)
    if match:
        print("   (Cleaning markdown from SQL query...)")
        query_str = match.group(2).strip()
    else:
        # If no markdown block is found, just strip whitespace as a fallback
        query_str = query_str.strip()
    # === MODIFICATION END ===

    
    # === FIX 2: Use the correct key names to build the connection string ===
    conn_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={db_settings['db_server']},1433;"
        f"DATABASE={db_settings['db_database']};"
        f"UID={db_settings['db_username']};"
        f"PWD={db_settings['db_password']};"
        f"LoginTimeout=30"
    )

    if not query_str.strip().upper().startswith('SELECT'):
        # This error is now much more reliable
        print(f"--- FAILED QUERY CHECK ---\n{query_str}\n--------------------------")
        raise ValueError("Query is not a valid SELECT statement. Only read operations are allowed.")

    # === MODIFICATION START: Wrapped execution in a retry loop ===
    for attempt in range(MAX_RETRIES):
        try:
            cnxn = pyodbc.connect(conn_string)
            
            df = pd.read_sql(query_str, cnxn)
            cnxn.close()
            
            return df # Success, exit the function
        
        except Exception as e:
            if cnxn:
                cnxn.close()
            
            print(f"❌ Attempt {attempt + 1}/{MAX_RETRIES} failed: Error during query execution: {str(e)}")
            
            if attempt < MAX_RETRIES - 1:
                print(f"     Retrying in 1 second...")
                time.sleep(1) # Wait 1 second before retrying
            else:
                print(f"❌ All {MAX_RETRIES} attempts failed.")
    # === MODIFICATION END ===
    
    return None # Return None if all retries fail

