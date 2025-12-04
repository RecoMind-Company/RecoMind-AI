# tools/sql_executor_tool.py
"""SQL Executor Tool - safely executes SELECT queries."""

import logging
import traceback
import pyodbc
import pandas as pd
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from tools.base import BaseSQLTool

logger = logging.getLogger(__name__)


class SQLInput(BaseModel):
    """Input schema for SQL executor tool."""
    raw_sql_query: str = Field(description="The SELECT SQL query to execute")


# Forbidden SQL keywords for security
FORBIDDEN_KEYWORDS = [
    "INSERT", "DELETE", "UPDATE", "DROP", "ALTER", 
    "TRUNCATE", "CREATE", "GRANT", "REVOKE", "REPLACE"
]


class ExecuteSQLQueryTool(BaseSQLTool):
    """Executes ONLY safe SQL SELECT queries on Source DB."""
    
    name: str = "execute_sql_query"
    description: str = "Executes ONLY safe SQL SELECT queries on Source DB."
    args_schema: type[BaseModel] = SQLInput

    def _get_sql_connection_string(self) -> str:
        """Build ODBC connection string for SQL Server."""
        drivers = [d for d in pyodbc.drivers() if "ODBC Driver" in d and "SQL Server" in d]
        if not drivers:
            raise Exception("No SQL Server ODBC driver installed!")
        
        driver = drivers[-1]
        return (
            f"DRIVER={{{driver}}};"
            f"SERVER={self.db_server};"
            f"DATABASE={self.db_database};"
            f"UID={self.db_username};"
            f"PWD={self.db_password};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )

    def _run(self, raw_sql_query: str) -> str:
        """Execute the tool."""
        # Security check
        query_upper = raw_sql_query.upper().strip()
        
        if not query_upper.startswith("SELECT"):
            return "Security Error: Only SELECT queries are allowed."
        
        for keyword in FORBIDDEN_KEYWORDS:
            if keyword in query_upper:
                return f"Security Error: Forbidden keyword '{keyword}' detected."

        try:
            # Build connection
            odbc_connect = self._get_sql_connection_string()
            connection_string = f"mssql+pyodbc:///?odbc_connect={odbc_connect.replace(';', '%3B')}"
            engine = create_engine(connection_string)
            
            # Execute query
            df = pd.read_sql(raw_sql_query, engine)
            
            if df.empty:
                return "No data found."
            
            return df.to_markdown(index=False)

        except Exception as e:
            traceback.print_exc()
            return f"SQL Execution Error: {e}"
