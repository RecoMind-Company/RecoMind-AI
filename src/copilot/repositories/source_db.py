# repositories/source_db.py
"""Source database repository - handles client database operations."""

import pyodbc
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


class SourceDBRepository:
    """Repository for source (client) database operations."""
    
    def __init__(self, db_server: str, db_database: str, db_username: str, db_password: str):
        """
        Initialize with connection parameters.
        
        Args:
            db_server: SQL Server hostname
            db_database: Database name
            db_username: Database username
            db_password: Database password
        """
        self.db_server = db_server
        self.db_database = db_database
        self.db_username = db_username
        self.db_password = db_password
    
    def _get_odbc_driver(self) -> str:
        """Get the best available ODBC driver."""
        drivers = [d for d in pyodbc.drivers() if "ODBC Driver" in d and "SQL Server" in d]
        if not drivers:
            raise Exception("No SQL Server ODBC driver installed!")
        return drivers[-1]
    
    def _get_connection_string(self) -> str:
        """Build ODBC connection string."""
        driver = self._get_odbc_driver()
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
    
    def _get_engine(self):
        """Create SQLAlchemy engine."""
        odbc_connect = self._get_connection_string()
        encoded = quote_plus(odbc_connect)
        conn_str = f"mssql+pyodbc:///?odbc_connect={encoded}"
        return create_engine(conn_str, fast_executemany=True)
    
    def get_table_columns(self, schema: str, table: str) -> list[dict]:
        """
        Get column information for a table.
        
        Args:
            schema: Database schema name
            table: Table name
            
        Returns:
            List of dicts with 'name' and 'type' keys
        """
        try:
            engine = self._get_engine()
            
            query = text("""
                SELECT c.name AS COLUMN_NAME, t.name AS DATA_TYPE
                FROM sys.columns c
                JOIN sys.types t ON c.user_type_id = t.user_type_id
                JOIN sys.tables tb ON c.object_id = tb.object_id
                JOIN sys.schemas s ON tb.schema_id = s.schema_id
                WHERE s.name = :schema AND tb.name = :table
                ORDER BY c.column_id
            """)

            with engine.connect() as conn:
                rows = conn.execute(query, {"schema": schema, "table": table}).fetchall()

            return [{"name": row[0], "type": row[1]} for row in rows]

        except Exception as e:
            print(f"Error fetching columns: {e}")
            return []
    
    def execute_query(self, sql: str) -> pd.DataFrame | str:
        """
        Execute a SELECT query and return results.
        
        Args:
            sql: The SQL query to execute
            
        Returns:
            DataFrame with results, or error message string
        """
        try:
            odbc_connect = self._get_connection_string()
            connection_string = f"mssql+pyodbc:///?odbc_connect={odbc_connect.replace(';', '%3B')}"
            engine = create_engine(connection_string)
            
            df = pd.read_sql(sql, engine)
            return df

        except Exception as e:
            return f"SQL Execution Error: {e}"
