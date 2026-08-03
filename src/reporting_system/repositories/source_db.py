"""Source database repository - handles SQL Server query execution to pandas DataFrames."""

import asyncio
import logging
import re
import time
import warnings
from typing import Any, Dict, Optional

import aioodbc
import pandas as pd
import pyodbc

from exceptions import QueryExecutionError

logger = logging.getLogger(__name__)


class SourceDBRepository:
    """Repository for executing queries against source MS SQL Server databases."""

    @staticmethod
    def _clean_sql_query(query: Any) -> str:
        """Strips markdown formatting and extra whitespace from SQL query strings."""
        query_str = str(query).strip()
        match = re.search(r"```(?:sql\s*)?([\s\S]*?)```", query_str, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return query_str

    @staticmethod
    def _validate_select_query(query_str: str) -> None:
        """Validates that query is a SELECT statement."""
        if not query_str.strip().upper().startswith("SELECT"):
            logger.error(f"Invalid SQL Query submission:\n{query_str}")
            raise QueryExecutionError("Query is not a valid SELECT statement. Only read operations are allowed.")

    @staticmethod
    def _build_conn_string(db_settings: Dict[str, str]) -> str:
        """Builds ODBC connection string from db_settings dictionary."""
        required_keys = ["db_server", "db_database", "db_username", "db_password"]
        missing = [k for k in required_keys if k not in db_settings or not db_settings[k]]
        if missing:
            raise ValueError(f"Missing required DB connection settings: {missing}")

        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={db_settings['db_server']},1433;"
            f"DATABASE={db_settings['db_database']};"
            f"UID={db_settings['db_username']};"
            f"PWD={db_settings['db_password']};"
            f"LoginTimeout=30"
        )

    @classmethod
    def execute_query_to_dataframe(
        cls, query: Any, db_settings: Dict[str, str], max_retries: int = 3
    ) -> Optional[pd.DataFrame]:
        """
        Executes a SQL SELECT query synchronously against SQL Server and returns a DataFrame.
        """
        query_str = cls._clean_sql_query(query)
        cls._validate_select_query(query_str)
        conn_string = cls._build_conn_string(db_settings)

        cnxn = None
        for attempt in range(1, max_retries + 1):
            try:
                cnxn = pyodbc.connect(conn_string)
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy connectable.*")
                    df = pd.read_sql(query_str, cnxn)
                cnxn.close()
                logger.info(f"Synchronous query execution successful. Returned shape: {df.shape}")
                return df

            except Exception as e:
                if cnxn:
                    try:
                        cnxn.close()
                    except Exception:
                        pass
                logger.warning(f"Attempt {attempt}/{max_retries} failed executing query: {e}")
                if attempt < max_retries:
                    time.sleep(1)

        logger.error(f"All {max_retries} attempts to execute query synchronously failed.")
        raise QueryExecutionError("Database query execution failed after retries.")

    @classmethod
    async def execute_query_to_dataframe_async(
        cls, query: Any, db_settings: Dict[str, str], max_retries: int = 3
    ) -> Optional[pd.DataFrame]:
        """
        Executes a SQL SELECT query asynchronously against SQL Server and returns a DataFrame.
        """
        query_str = cls._clean_sql_query(query)
        cls._validate_select_query(query_str)
        conn_string = cls._build_conn_string(db_settings)

        for attempt in range(1, max_retries + 1):
            cnxn = None
            cursor = None
            try:
                cnxn = await aioodbc.connect(dsn=conn_string)
                cursor = await cnxn.cursor()
                await cursor.execute(query_str)

                rows = await cursor.fetchall()
                columns = [column[0] for column in cursor.description]

                await cursor.close()
                await cnxn.close()

                df = pd.DataFrame.from_records(rows, columns=columns)
                logger.info(f"Async query execution successful. Returned shape: {df.shape}")
                return df

            except Exception as e:
                if cursor:
                    try:
                        await cursor.close()
                    except Exception:
                        pass
                if cnxn:
                    try:
                        await cnxn.close()
                    except Exception:
                        pass
                logger.warning(f"Async attempt {attempt}/{max_retries} failed executing query: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(1)

        logger.error(f"All {max_retries} async attempts to execute query failed.")
        raise QueryExecutionError("Async database query execution failed after retries.")
