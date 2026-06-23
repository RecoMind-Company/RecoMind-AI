# core/tools.py

import os
import pyodbc
from sqlalchemy import create_engine
import pandas as pd
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import psycopg2
import numpy as np
import traceback
import json
import re
from sentence_transformers import SentenceTransformer


# Load the embedding model globally for the search tool
MODEL_NAME = 'BAAI/bge-small-en-v1.5'
try:
    embedding_model = SentenceTransformer(MODEL_NAME)
except Exception as e:
    print(f"ERROR: Failed to load SentenceTransformer model '{MODEL_NAME}'. Search tool will fail. Error: {e}")
    embedding_model = None 

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
    # SQL Server connection details
    db_server: str = Field(description="SQL Server host name.")
    db_database: str = Field(description="SQL Server database name.")
    db_username: str = Field(description="SQL Server user name.")
    db_password: str = Field(description="SQL Server password.")
    
    # Vector DB connection details
    vector_db_host: str = Field(description="PostgreSQL Vector DB host.")
    vector_db_name: str = Field(description="PostgreSQL Vector DB name.")
    vector_db_user: str = Field(description="PostgreSQL Vector DB user.")
    vector_db_password: str = Field(description="PostgreSQL Vector DB password.")
    company_id: str = Field(description="The unique ID of the client company.")
    team_name: str | None = Field(default=None, description="Optional team name to filter tables (e.g., 'Sales').")

    def get_sql_conn_string(self):
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
            
            # Build the query dynamically based on whether team_name is provided
            query_parts = [
                "SELECT table_name, table_description, table_relations",
                "FROM client_schema_vectors",
                "WHERE company_id = %s"
            ]
            params = [self.company_id]

            # Add team filter if provided
            print(f"🔍 DEBUG: team_name received: '{self.team_name}' (Type: {type(self.team_name)})")
            
            if self.team_name:
                print(f"🔍 Filtering tables by Team: {self.team_name}")
                # Use ILIKE for case-insensitive partial match inside the array
                query_parts.append("AND EXISTS (SELECT 1 FROM unnest(team_name) t WHERE t ILIKE %s)")
                params.append(f"%{self.team_name}%")
            else:
                print("🔍 No Team filter applied. Searching all tables.")

            # Add ordering and limit
            query_parts.append("ORDER BY embedding <-> %s")
            query_parts.append("LIMIT %s;")
            
            params.append(query_embedding_str)
            params.append(SEARCH_LIMIT)
            
            final_query = "\n".join(query_parts)
            cur.execute(final_query, tuple(params))

            results = cur.fetchall()
            
            # --- FALLBACK MECHANISM ---
            if not results and self.team_name:
                print(f"⚠️ No tables found for team '{self.team_name}'. Falling back to global search (all tables).")
                query_parts_fallback = [
                    "SELECT table_name, table_description, table_relations",
                    "FROM client_schema_vectors",
                    "WHERE company_id = %s",
                    "ORDER BY embedding <-> %s",
                    "LIMIT %s;"
                ]
                params_fallback = [self.company_id, query_embedding_str, SEARCH_LIMIT]
                cur.execute("\n".join(query_parts_fallback), tuple(params_fallback))
                results = cur.fetchall()

            if not results:
                # If still no results, return a structured fallback so LLM doesn't hallucinate
                return '{"error": "No tables found in vector database. Stop and report this failure."}'

            output = [f"--- Search Results (Top {SEARCH_LIMIT}) ---"]
            
            for table_name, description, relations in results:
                relations_str = json.dumps(relations) if relations else "[]"
                output.append(f"Table: {table_name}, Description: {description}, Relations: {relations_str}")

            return "\n".join(output)
            
        except Exception as e:
            # Added traceback for better debugging
            traceback.print_exc()
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
            odbc_connect = self.get_sql_conn_string() # Re-used the method from base class
            connection_string = f"mssql+pyodbc:///?odbc_connect={odbc_connect.replace(';', '%3B')}"
            engine = create_engine(connection_string)
            schema_info = []
            tables_list = [t.strip() for t in table_names.split(',')]
            
            for full_table_name in tables_list:
                try:
                    schema, table = full_table_name.split('.')
                except ValueError:
                    schema_info.append(f"Skipping: Invalid table name format '{full_table_name}'.")
                    continue
                
                query = """
                SELECT COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                """
                params = (schema, table)
                result = pd.read_sql_query(query, engine, params=params)
                
                if not result.empty:
                    schema_info.append(f"Table {full_table_name}:\n" + result.to_string(index=False))
            
            return "\n\n".join(schema_info) if schema_info else "No schema found for the provided tables."
        except Exception as e:
            traceback.print_exc()
            return f"Error fetching table schema: {e}"

# =======================================================
# 3. ExecuteSQLQueryTool
# =======================================================
class ExecuteSQLQueryInput(BaseModel):
    query: str = Field(description="The SQL query to execute and test.")

class ExecuteSQLQueryTool(BaseSQLTool):
    name: str = "execute_sql_query"
    description: str = (
        "Executes a SQL SELECT query against the database and returns a small sample of the results, "
        "or the exact SQL error message if it fails. "
        "Use this tool to validate your generated SQL queries before giving your Final Answer."
    )
    args_schema: type[BaseModel] = ExecuteSQLQueryInput

    def _run(self, query: str) -> str:
        try:
            # Clean up the query string (e.g. remove markdown)
            query_str = str(query)
            match = re.search(r'```(sql\s*)?([\s\S]*?)```', query_str, re.IGNORECASE)
            if match:
                query_str = match.group(2).strip()
            else:
                query_str = query_str.strip()

            if not query_str.strip().upper().startswith('SELECT'):
                return "Error: Query is not a valid SELECT statement."

            odbc_connect = self.get_sql_conn_string()
            cnxn = pyodbc.connect(odbc_connect)
            
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', message='.*pandas only supports SQLAlchemy connectable.*')
                df = pd.read_sql(query_str, cnxn)
            
            cnxn.close()
            num_rows = len(df)
            return f"SUCCESS! Query returned {num_rows} rows. Sample data:\n" + df.head(3).to_string(index=False)
            
        except Exception as e:
            return f"SQL EXECUTION ERROR: {str(e)}"
