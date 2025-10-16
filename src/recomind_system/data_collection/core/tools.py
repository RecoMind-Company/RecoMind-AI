# core/tools.py

import os
import pyodbc
from sqlalchemy import create_engine
import pandas as pd
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
import traceback
import json

# Load the embedding model globally for the search tool
MODEL_NAME = 'BAAI/bge-small-en-v1.5'
try:
    embedding_model = SentenceTransformer(MODEL_NAME)
except Exception as e:
    # Changed to a standard print warning
    print(f"Warning: Failed to load SentenceTransformer model {MODEL_NAME}. Search tool will fail. Error: {e}")


# =======================================================
# Pydantic Schemas
# =======================================================
class VectorSearchInput(BaseModel):
    query_key: str = Field(description="The user's natural language request or search key.")


class GetTableSchemaInput(BaseModel):
    table_names: str = Field(description="Comma-separated list of fully qualified table names (e.g., 'Schema.Table')")


# =======================================================
# Base Tool Setup for Parameterized Connections
# =======================================================
class BaseSQLTool(BaseTool):
    # SQL Server connection details (passed from main.py)
    db_server: str = Field(description="SQL Server host name.")
    db_database: str = Field(description="SQL Server database name.")
    db_username: str = Field(description="SQL Server user name.")
    db_password: str = Field(description="SQL Server password.")
    
    # Vector DB connection details (passed from main.py)
    vector_db_host: str = Field(description="PostgreSQL Vector DB host.")
    vector_db_name: str = Field(description="PostgreSQL Vector DB name.")
    vector_db_user: str = Field(description="PostgreSQL Vector DB user.")
    vector_db_password: str = Field(description="PostgreSQL Vector DB password.")
    company_id: int = Field(description="The unique ID of the client company.")


    def get_sql_conn_string(self):
        """
        Generates the ODBC connection string.
        """
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.db_server},1433;"
            f"DATABASE={self.db_database};UID={self.db_username};PWD={self.db_password};"
            f"LoginTimeout=30"
        )
    
    def get_vector_db_conn_params(self):
        return {
            'host': self.vector_db_host,
            'database': self.vector_db_name,
            'user': self.vector_db_user,
            'password': self.vector_db_password
        }


# =======================================================
# 1. Vector DB Table Search (The Retrieval Mechanism)
# =======================================================
class VectorDBTableSearchTool(BaseSQLTool):
    name: str = "vector_db_table_search"
    description: str = (
        "Performs a semantic search on the client's schema descriptions (vectors) "
        "to find the most relevant tables for a user query. "
        "Input MUST be the user's natural language request key. "
        "Returns a list of the top relevant tables along with their descriptions and their JOIN relationships."
    )
    args_schema: type[BaseModel] = VectorSearchInput
    
    def _run(self, query_key: str) -> str:
        conn = None
        SEARCH_LIMIT = 12 
        try:
            query_embedding = embedding_model.encode(query_key, normalize_embeddings=True)
            query_embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            conn = psycopg2.connect(**self.get_vector_db_conn_params())
            cur = conn.cursor()
            
            ### START MODIFICATION ###
            # The SQL query now also selects the 'table_relations' column.
            search_query = f"""
            SELECT table_name, table_description, table_relations
            FROM client_schema_vectors
            WHERE company_id = {self.company_id}
            ORDER BY embedding <-> '{query_embedding_str}'
            LIMIT {SEARCH_LIMIT};
            """
            ### END MODIFICATION ###
            
            cur.execute(search_query)
            results = cur.fetchall()
            
            if not results:
                return "No relevant tables found in the vector database for this query key."

            output = [f"--- Search Results (Top {SEARCH_LIMIT}) ---"]
            
            ### START MODIFICATION ###
            # The output now includes the 'table_relations' data for the agent to use.
            # The result tuple now has three items: (table_name, description, relations)
            for table_name, description, relations in results:
                # Format relations to be a clean string if it's not None
                relations_str = json.dumps(relations) if relations else "[]"
                output.append(f"Table: {table_name}, Description: {description}, Relations: {relations_str}")
            ### END MODIFICATION ###

            return "\n".join(output)
            
        except Exception as e:
            return f"Error performing vector search: {e}"
        finally:
            if conn:
                conn.close()


# =======================================================
# 2. GetTableSchemaTool 
# =======================================================
class GetTableSchemaTool(BaseSQLTool):
    name: str = "get_table_schema"
    description: str = (
        "Fetches the schema (columns and data types) for a list of tables. "
        "The input must be a comma-separated string of fully qualified table names (e.g., 'Schema.Table')."
    )
    args_schema: type[BaseModel] = GetTableSchemaInput

    def _run(self, table_names: str) -> str:
        try:
            odbc_connect = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.db_server},1433;"
                f"DATABASE={self.db_database};UID={self.db_username};PWD={self.db_password};"
                f"LoginTimeout=30"
            )
            
            connection_string = f"mssql+pyodbc:///?odbc_connect={odbc_connect}"
            engine = create_engine(connection_string)
            schema_info = []
            tables_list = [t.strip() for t in table_names.split(',')]
            
            for full_table_name in tables_list:
                try:
                    schema, table = full_table_name.split('.')
                except ValueError:
                    schema_info.append(f"Skipping: Invalid table name format '{full_table_name}'.")
                    continue
                
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