"""Table schema retrieval tool querying SQL Server INFORMATION_SCHEMA."""

import logging
from typing import Type
from pydantic import BaseModel, Field
import pandas as pd
from sqlalchemy import create_engine

from tools.base import BaseSQLTool

logger = logging.getLogger(__name__)


class GetTableSchemaInput(BaseModel):
    """Input schema for table schema retrieval tool."""

    table_names: str = Field(description="Comma-separated list of fully qualified table names (e.g., 'Schema.Table')")


class GetTableSchemaTool(BaseSQLTool):
    """Tool for fetching column names and data types for specified database tables."""

    name: str = "get_table_schema"
    description: str = (
        "Fetches the schema (columns and data types) for a list of tables. "
        "Input MUST be a comma-separated string of fully qualified table names (e.g., 'Schema.Table')."
    )
    args_schema: Type[BaseModel] = GetTableSchemaInput

    def _run(self, table_names: str) -> str:
        try:
            odbc_connect = self.get_sql_conn_string()
            connection_string = f"mssql+pyodbc:///?odbc_connect={odbc_connect.replace(';', '%3B')}"
            engine = create_engine(connection_string)

            schema_info = []
            tables_list = [t.strip() for t in table_names.split(",") if t.strip()]

            for full_table_name in tables_list:
                try:
                    schema, table = full_table_name.split(".")
                except ValueError:
                    logger.warning(f"Skipping invalid table name format: '{full_table_name}'")
                    schema_info.append(f"Skipping: Invalid table name format '{full_table_name}'.")
                    continue

                query = """
                SELECT COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                """
                result = pd.read_sql_query(query, engine, params=(schema, table))

                if not result.empty:
                    schema_info.append(f"Table {full_table_name}:\n" + result.to_string(index=False))

            return "\n\n".join(schema_info) if schema_info else "No schema found for the provided tables."

        except Exception as e:
            logger.error(f"Error fetching table schema: {e}", exc_info=True)
            return f"Error fetching table schema: {e}"
