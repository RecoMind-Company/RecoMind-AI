"""SQL execution tool for testing generated SQL queries against the source database."""

import logging
import re
import warnings
from typing import Type
from pydantic import BaseModel, Field
import pandas as pd
import pyodbc

from tools.base import BaseSQLTool

logger = logging.getLogger(__name__)


class ExecuteSQLQueryInput(BaseModel):
    """Input schema for SQL execution tool."""

    query: str = Field(description="The SQL query to execute and test.")


class ExecuteSQLQueryTool(BaseSQLTool):
    """Tool for validating generated SQL queries against the target database."""

    name: str = "execute_sql_query"
    description: str = (
        "Executes a SQL SELECT query against the database and returns a small sample of the results, "
        "or the exact SQL error message if it fails. "
        "Use this tool to validate your generated SQL queries before giving your Final Answer."
    )
    args_schema: Type[BaseModel] = ExecuteSQLQueryInput

    def _run(self, query: str) -> str:
        try:
            query_str = str(query).strip()
            match = re.search(r"```(?:sql\s*)?([\s\S]*?)```", query_str, re.IGNORECASE)
            if match:
                query_str = match.group(1).strip()

            if not query_str.upper().startswith("SELECT"):
                return "Error: Query is not a valid SELECT statement."

            odbc_connect = self.get_sql_conn_string()
            cnxn = pyodbc.connect(odbc_connect)

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy connectable.*")
                df = pd.read_sql(query_str, cnxn)

            cnxn.close()
            num_rows = len(df)
            return f"SUCCESS! Query returned {num_rows} rows. Sample data:\n" + df.head(3).to_string(index=False)

        except Exception as e:
            logger.warning(f"SQL execution test failed: {e}")
            return f"SQL EXECUTION ERROR: {str(e)}"
