import os
import pyodbc
import pandas as pd
from crewai import Tool
from typing import Any, Optional, Dict, List
import time 
import re 
import asyncio
import aioodbc
import json

# ================================================================
# 1. Asynchronous Data Access Layer
# ================================================================

# Forbidden SQL keywords (for additional safety checks aligned with Agent 5)
FORBIDDEN_SQL: List[str] = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]
MAX_RETRIES: int = 3

def _build_conn_string(settings: Dict[str, str]) -> str:
    """
    Helper function to build the ODBC connection string using dynamic DB settings.
    Values are provided through the 'db_settings' dictionary.
    """
    return (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={settings['db_server']},1433;"
        f"DATABASE={settings['db_database']};"
        f"UID={settings['db_username']};"
        f"PWD={settings['db_password']};"
        f"LoginTimeout=30"
    )

def _clean_query(query: Any) -> str:
    """
    Extracts the SQL query safely by removing Markdown formatting
    (e.g., ```sql ... ``` blocks).
    Ensures the returned query is clean and ready for execution.
    """
    query_str = str(query)
    
    # Detect SQL inside Markdown format ```sql ... ```
    match = re.search(r'```(sql\s*)?([\s\S]*?)```', query_str, re.IGNORECASE)
    if match:
        return match.group(2).strip()
    
    # If no Markdown block found, return stripped raw value
    return query_str.strip()

def _format_error(msg: str) -> str:
    """
    Returns a standard JSON error object to the final answer agent.
    Used for consistent error formatting.
    """
    return json.dumps({"error": msg}, ensure_ascii=False)


async def execute_query_to_dataframe_async(query: Any, db_settings: Dict[str, str]) -> Optional[pd.DataFrame]:
    """
    Execute a SQL SELECT query asynchronously using aioodbc.
    Returns a pandas DataFrame or raises an exception if all retries fail.
    """

    # Validate required DB configuration parameters
    required_keys = ["db_server", "db_database", "db_username", "db_password"]
    if not all(k in db_settings for k in required_keys):
        raise ValueError("Missing required DB connection keys in db_settings.")

    query_str = _clean_query(query)
    conn_string = _build_conn_string(db_settings)

    # Double security check (Agent 5 already performs this too)
    if not query_str.strip().upper().startswith('SELECT') or \
       any(keyword in query_str.upper() for keyword in FORBIDDEN_SQL):
        raise ValueError("Query is not a valid SELECT statement or contains forbidden keywords.")

    # --- Asynchronous execution attempts with retry mechanism ---
    for attempt in range(MAX_RETRIES):
        cnxn = None
        cursor = None
        try:
            # Open async DB connection
            cnxn = await aioodbc.connect(dsn=conn_string)
            cursor = await cnxn.cursor()
            
            # Execute SQL query
            await cursor.execute(query_str)
            
            # Fetch resulting rows
            rows = await cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            
            # Close resources asynchronously
            await cursor.close()
            await cnxn.close()
            
            # Convert to DataFrame
            df = pd.DataFrame.from_records(rows, columns=columns)
            return df
        
        except Exception as e:
            # Attempt to close connection on failure
            if cursor: 
                await cursor.close()
            if cnxn: 
                await cnxn.close()
            
            print(f"❌ Async Attempt {attempt + 1}/{MAX_RETRIES} failed: {str(e)}")
            
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(1)  # Async wait before retry
            else:
                # Final error after exhausting retries
                raise Exception(f"All {MAX_RETRIES} attempts failed. Last error: {str(e)}")

    return None  # Technically unreachable due to the exception logic


# ================================================================
# 2. CrewAI Tool Wrapper (Sync function calling async logic)
# ================================================================

def execute_sql_query_tool_func(raw_sql_query: str, db_settings: Dict[str, str]) -> str:
    """
    Synchronous wrapper used by CrewAI agents to execute SQL queries safely.
    Runs the async execution function inside asyncio.run().
    """

    print(f"\n🚀 Agent 5: Executing query with dynamic settings...")

    try:
        # Execute async DB function inside sync context
        df: Optional[pd.DataFrame] = asyncio.run(
            execute_query_to_dataframe_async(raw_sql_query, db_settings)
        )
        
        if df is None or df.empty:
            print("✔ Query executed: No rows or null result.")
            return _format_error("No rows returned from the database matching the criteria.")
        
        print(f"✔ Query executed successfully. Returning {len(df)} rows.")
        return df.to_markdown(index=False)
        
    except ValueError as e:
        # Validation / security-related errors
        return _format_error(f"Security/Validation Error: {str(e)}")
        
    except Exception as e:
        # Execution or connection errors
        return _format_error(f"SQL Execution Failure: {str(e)}")


# ================================================================
# 3. CrewAI Tool Definition (for Agent 5)
# ================================================================

ExecuteSQLQueryTool = Tool(
    name="ExecuteSQLQueryTool",
    func=execute_sql_query_tool_func,
    description=(
        "Safely execute a SQL SELECT query against the dynamic Source Database. "
        "The input MUST be the raw SQL query string and the 'db_settings' dictionary "
        "containing server, database, username, and password for connection."
    )
)
