import os
from dotenv import load_dotenv
import pyodbc
from sqlalchemy import create_engine
import pandas as pd
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

load_dotenv()

db_password = os.getenv("DB_PASSWORD")
server = "recomindserver.database.windows.net"
database = "AdventureWorks2014"
username = "recomind"

class GetAllTablesInput(BaseModel):
    pass

class GetTableSchemaInput(BaseModel):
    table_names: str = Field(description="Comma-separated list of fully qualified table names (e.g., 'Schema.Table')")

class ExecuteSQLQueryInput(BaseModel):
    query: str = Field(description="SQL query to execute")

class GetAllTablesTool(BaseTool):
    name: str = "get_all_tables"
    description: str = (
        "Fetches a comma-separated list of all fully qualified table names (Schema.Table) from the database. "
        "This tool is useful for getting an overview of the database structure."
    )
    args_schema: type[BaseModel] = GetAllTablesInput

    def _run(self) -> str:
        try:
            conn_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};DATABASE={database};UID={username};PWD={db_password}"
            )
            cnxn = pyodbc.connect(conn_string)
            cursor = cnxn.cursor()
            cursor.execute("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
            tables = [f"{row[0]}.{row[1]}" for row in cursor.fetchall()]
            return ", ".join(tables)
        except Exception as e:
            return f"Error connecting to database or fetching tables: {e}"

class GetTableSchemaTool(BaseTool):
    name: str = "get_table_schema"
    description: str = (
        "Fetches the schema (columns and data types) for a list of tables. "
        "The input must be a comma-separated string of fully qualified table names (e.g., 'Schema.Table')."
    )
    args_schema: type[BaseModel] = GetTableSchemaInput

    def _run(self, table_names: str) -> str:
        try:
            connection_string = (
                f"mssql+pyodbc:///?odbc_connect=DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};"
                f"DATABASE={database};UID={username};PWD={db_password}"
            )
            engine = create_engine(connection_string)
            schema_info = []
            tables_list = [t.strip() for t in table_names.split(',')]
            for full_table_name in tables_list:
                try:
                    schema, table = full_table_name.split('.')
                except ValueError:
                    return f"Error: Invalid table name format '{full_table_name}'. Expected 'Schema.Table'."
                query = f"""
                SELECT COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'
                """
                result = pd.read_sql_query(query, engine)
                if not result.empty:
                    schema_info.append(f"Table {full_table_name}:\n" + result.to_string(index=False))
            return "\n\n".join(schema_info) if schema_info else "No schema found for the provided tables."
        except Exception as e:
            return f"Error fetching table schema: {e}"

class ExecuteSQLQueryTool(BaseTool):
    name: str = "execute_sql_query"
    description: str = (
        "Executes a SQL query against the database and returns the results as a pandas DataFrame. "
        "The input must be a valid SQL query string."
    )
    args_schema: type[BaseModel] = ExecuteSQLQueryInput

    def _run(self, query: str) -> pd.DataFrame:
        try:
            conn_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};DATABASE={database};UID={username};PWD={db_password}"
            )
            cnxn = pyodbc.connect(conn_string)
            df = pd.read_sql(query, cnxn)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [f"Error executing query: {e}"]})