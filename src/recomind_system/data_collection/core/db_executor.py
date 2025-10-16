import os
import pyodbc
import pandas as pd
from typing import Any, Optional

def execute_query_to_dataframe(query: Any, config: Any) -> Optional[pd.DataFrame]: # Changed type hint to Any
    """
    Executes a SQL query against the database and returns the results as a pandas DataFrame.
    
    Args:
        query (Any): The valid SQL query to execute (can be a string or CrewOutput).
        config (Any): The loaded configuration object.
        
    Returns:
        Optional[pd.DataFrame]: A DataFrame containing the query results, or None on failure.
    """
    cnxn = None
    
    if not all(hasattr(config, attr) for attr in ["DB_SERVER", "DB_DATABASE", "DB_USERNAME", "DB_PASSWORD"]):
        raise AttributeError("Missing required DB connection attributes in config.")

    try:
        ### START MODIFICATION ###
        # Convert the incoming query object (which might be CrewOutput) to a string.
        query_str = str(query)
        ### END MODIFICATION ###
        
        # Generate the ODBC connection string
        conn_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={config.DB_SERVER},1433;"
            f"DATABASE={config.DB_DATABASE};UID={config.DB_USERNAME};PWD={config.DB_PASSWORD};"
            f"LoginTimeout=30"
        )
        
        cnxn = pyodbc.connect(conn_string)
        
        # Simple validation: ensure it's a SELECT statement
        ### MODIFIED: Use the converted string variable 'query_str'
        if not query_str.strip().upper().startswith('SELECT'):
            raise ValueError("Query is not a valid SELECT statement. Only read operations are allowed.")
            
        ### MODIFIED: Use the converted string variable 'query_str'
        df = pd.read_sql(query_str, cnxn)
        cnxn.close()
        
        return df
    
    except Exception as e:
        if cnxn:
            cnxn.close()
        # Log the error and return None to indicate failure.
        print(f"❌ Error during query execution: {str(e)}")
        return None