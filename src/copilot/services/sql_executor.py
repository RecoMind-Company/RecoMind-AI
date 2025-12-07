# services/sql_executor.py
"""Direct SQL execution without CrewAI agent."""

import logging
import pyodbc
import pandas as pd
from typing import Optional, Dict
import time
import re

logger = logging.getLogger(__name__)

# Forbidden SQL keywords for security
FORBIDDEN_KEYWORDS = [
    "INSERT", "DELETE", "UPDATE", "DROP", "ALTER",
    "TRUNCATE", "CREATE", "GRANT", "REVOKE", "REPLACE"
]


def execute_sql_query(
    sql_query: str,
    db_server: str,
    db_database: str,
    db_username: str,
    db_password: str,
    max_retries: int = 3
) -> Dict[str, any]:
    """
    Execute SQL query and return results.
    
    Returns:
        dict with 'success', 'result', 'error' keys
    """
    try:
        # Clean markdown if present
        match = re.search(r'```(sql\s*)?([\s\S]*?)```', sql_query, re.IGNORECASE)
        if match:
            logger.info("Cleaning markdown from SQL query...")
            sql_query = match.group(2).strip()
        else:
            sql_query = sql_query.strip()
        
        # Security check
        query_upper = sql_query.upper().strip()
        
        if not query_upper.startswith("SELECT"):
            return {
                "success": False,
                "result": None,
                "error": "Security Error: Only SELECT queries are allowed."
            }
        
        for keyword in FORBIDDEN_KEYWORDS:
            if keyword in query_upper:
                return {
                    "success": False,
                    "result": None,
                    "error": f"Security Error: Forbidden keyword '{keyword}' detected."
                }
        
        # Build connection string
        drivers = [d for d in pyodbc.drivers() if "ODBC Driver" in d and "SQL Server" in d]
        if not drivers:
            return {
                "success": False,
                "result": None,
                "error": "No SQL Server ODBC driver installed!"
            }
        
        driver = drivers[-1]
        conn_string = (
            f"DRIVER={{{driver}}};"
            f"SERVER={db_server},1433;"
            f"DATABASE={db_database};"
            f"UID={db_username};"
            f"PWD={db_password};"
            f"LoginTimeout=30"
        )
        
        # Execute with retries
        for attempt in range(max_retries):
            cnxn = None
            try:
                logger.info(f"Executing SQL (attempt {attempt + 1}/{max_retries}): {sql_query}")
                cnxn = pyodbc.connect(conn_string)
                df = pd.read_sql(sql_query, cnxn)
                cnxn.close()
                
                if df.empty:
                    return {
                        "success": True,
                        "result": "No data found.",
                        "error": None
                    }
                
                # Convert to simple dict format
                result_dict = df.to_dict('records')
                logger.info(f"✅ Query executed successfully. Rows returned: {len(result_dict)}")
                
                return {
                    "success": True,
                    "result": result_dict,
                    "error": None
                }
                
            except Exception as e:
                if cnxn:
                    cnxn.close()
                
                logger.error(f"❌ Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    logger.info("Retrying in 1 second...")
                    time.sleep(1)
                else:
                    return {
                        "success": False,
                        "result": None,
                        "error": f"SQL Execution Error after {max_retries} attempts: {str(e)}"
                    }
        
    except Exception as e:
        logger.error(f"SQL execution failed: {e}", exc_info=True)
        return {
            "success": False,
            "result": None,
            "error": f"SQL Execution Error: {str(e)}"
        }
