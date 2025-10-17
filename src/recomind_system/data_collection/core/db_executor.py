# data_collection/core/db_executor.py (Corrected Version)

import os
import pyodbc
import pandas as pd
from typing import Any, Optional, Dict

def execute_query_to_dataframe(query: Any, db_settings: Dict[str, str]) -> Optional[pd.DataFrame]:
    """
    Executes a SQL query against the database and returns the results as a pandas DataFrame.
    
    Args:
        query (Any): The valid SQL query to execute.
        db_settings (Dict[str, str]): A dictionary with DB connection details.
        
    Returns:
        Optional[pd.DataFrame]: A DataFrame containing the query results, or None on failure.
    """
    cnxn = None
    
    # === FIX 1: Check for the correct key names with the 'db_' prefix ===
    required_keys = ["db_server", "db_database", "db_username", "db_password"]
    if not all(k in db_settings for k in required_keys):
        raise ValueError("Missing required DB connection keys in db_settings dictionary.")

    try:
        query_str = str(query)
        
        # === FIX 2: Use the correct key names to build the connection string ===
        conn_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={db_settings['db_server']},1433;"
            f"DATABASE={db_settings['db_database']};"
            f"UID={db_settings['db_username']};"
            f"PWD={db_settings['db_password']};"
            f"LoginTimeout=30"
        )
        
        cnxn = pyodbc.connect(conn_string)
        
        if not query_str.strip().upper().startswith('SELECT'):
            raise ValueError("Query is not a valid SELECT statement. Only read operations are allowed.")
            
        df = pd.read_sql(query_str, cnxn)
        cnxn.close()
        
        return df
    
    except Exception as e:
        if cnxn:
            cnxn.close()
        print(f"❌ Error during query execution: {str(e)}")
        return None