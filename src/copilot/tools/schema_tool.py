# tools/schema_tool.py
"""Schema Tool - fetches table columns from source database."""

import json
import traceback
import pyodbc
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from tools.base import BaseSQLTool


class GetTableSchemaInput(BaseModel):
    """Input schema for schema tool."""
    table_name: str = Field(description="The full database table name (e.g. 'schema.table')")


class GetAvailableColumnsTool(BaseSQLTool):
    """Fetch columns and types for a table from Source DB."""
    
    name: str = "get_available_columns"
    description: str = "Fetch columns and types for a table from Source DB."
    args_schema: type[BaseModel] = GetTableSchemaInput

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

    def _run(self, table_name: str) -> str:
        """Execute the tool."""
        try:
            if "." not in table_name:
                return json.dumps([])

            schema, table = table_name.split(".", 1)

            # Build connection
            odbc_connect = self._get_sql_connection_string()
            encoded = quote_plus(odbc_connect)
            conn_str = f"mssql+pyodbc:///?odbc_connect={encoded}"
            engine = create_engine(conn_str, fast_executemany=True)

            # Query columns
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

            columns = [{"name": row[0], "type": row[1]} for row in rows]
            return json.dumps(columns, indent=2)

        except Exception as e:
            traceback.print_exc()
            return json.dumps([])
