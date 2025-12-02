
import os
import pandas as pd
import psycopg2
import traceback
import json
from sqlalchemy import create_engine, text
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from sentence_transformers import SentenceTransformer
from typing import List
from shared.config import get_vector_db_url
from urllib.parse import quote_plus

import pyodbc
# ==================================================================
# 1) Load Embedding Model
# ==================================================================
MODEL_NAME = 'BAAI/bge-small-en-v1.5'

try:
    embedding_model = SentenceTransformer(MODEL_NAME)
except Exception as e:
    print(f"[ERROR] Failed to load embedding model: {e}")
    embedding_model = None

# ==================================================================
# 2) Pydantic Schemas
# ==================================================================
class GetTableSchemaInput(BaseModel):
    table_name: str = Field(description="The full database table name (e.g. 'schema.table')")

class RBACInput(BaseModel):
    team_name: str = Field(description="The name of the user's team for access control.")

class VectorSearchInput(BaseModel):
    query_key: str = Field(description="The metric word for semantic search.")
    allowed_tables: List[str] = Field(description="List of tables allowed by RBAC.")

class SQLInput(BaseModel):
    raw_sql_query: str = Field(description="The SELECT SQL query to execute.")

# ==================================================================
# 3) Base Tool — Provides DB Connections
# ==================================================================
class BaseSQLTool(BaseTool):
    # Source/Main DB (SQL Server)
    db_server: str = Field(default="", description="SQL Server host name.")
    db_database: str = Field(default="", description="SQL Server database name.")
    db_username: str = Field(default="", description="SQL Server user name.")
    db_password: str = Field(default="", description="SQL Server password.")

    # Metadata/Vector DB (PostgreSQL)
    vector_db_host: str = Field(default=os.getenv("VECTOR_DB_HOST"))
    vector_db_name: str = Field(default=os.getenv("VECTOR_DB_NAME"))
    vector_db_user: str = Field(default=os.getenv("VECTOR_DB_USER"))
    vector_db_password: str = Field(default=os.getenv("VECTOR_DB_PASSWORD"))
    company_id: str = Field(default="demo_company", description="The unique ID of the client company.")

    metadata_url: str = Field(default=get_vector_db_url(), description="SQLAlchemy connection URL for metadata/RBAC DB")

    # -------------------
    # Connection Helpers
    # -------------------
    def get_vector_db_conn_params(self):
        return {
            "host": self.vector_db_host,
            "database": self.vector_db_name,
            "user": self.vector_db_user,
            "password": self.vector_db_password,
            "port": 5432
        }

    # 💡 الإضافة المطلوبة: دالة لإنشاء سلسلة اتصال ODBC لـ SQL Server
    def get_sql_conn_string(self) -> str:
        """Constructs an ODBC connection string for MS SQL Server (Source DB)."""
        # Use latest installed SQL Server ODBC driver
        drivers = [d for d in pyodbc.drivers() if "ODBC Driver" in d and "SQL Server" in d]
        if not drivers:
          raise Exception("No SQL Server ODBC driver installed!")

        driver = drivers[-1]  # e.g., ODBC Driver 18 for SQL Server
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

    def get_metadata_engine(self):
        try:
            return create_engine(self.metadata_url)
        except Exception as e:
            print("[ERROR] Cannot connect to Metadata DB:", e)
            return None

    def get_metadata_engine_conn_params(self):
        if not self.metadata_url:
            raise ValueError("metadata_url is not set")
        from sqlalchemy.engine.url import make_url
        url = make_url(self.metadata_url)
        return {
            "host": url.host,
            "port": url.port or 5432,
            "database": url.database,
            "user": url.username,
            "password": url.password
        }

# ==================================================================
# 4) Get Allowed Tables Tool (يستخدم Metadata/Vector DB وهي PostgreSQL)
# ==================================================================
class GetAllowedTablesTool(BaseSQLTool):
    name: str = "get_allowed_tables"
    description: str = "Fetch allowed tables for a user team from Metadata DB."
    args_schema: type[BaseModel] = RBACInput
    company_id: str = Field(description="The company ID.")
    all_company_tables: List[str] = Field(description="List of all tables available for this company.")
    def _run(self, team_name: str) -> str:
        engine = self.get_metadata_engine()
        if engine is None:
            return "Metadata DB not available."

        try:
            team_name = team_name.strip()
            db_type = engine.url.get_backend_name() 

            if db_type == "postgresql":
                q = text("""
                    SELECT table_name
                    FROM client_schema_vectors
                    WHERE company_id = :cid
                    AND team_name @> ARRAY[:team_name]::text[]
                 """)
                params = {"cid": self.company_id, "team_name": team_name}
            else:  # SQL Server
                q = text("""
                    SELECT table_name
                    FROM client_schema_vectors
                    WHERE company_id = :cid
                    AND REPLACE(team_name,' ','') LIKE :contains
                """)
                params = {
                      "cid": self.company_id,
                      "contains": f"%{team_name}%"
                }

            with engine.connect() as conn:
                rows = conn.execute(q, params).fetchall()

            return json.dumps({"allowed_tables": [r[0] for r in rows]}, indent=2)

        except Exception as e:
            traceback.print_exc()
            return f"RBAC query failed: {e}"

# ==================================================================
# 5) Vector DB Table Search Tool (يستخدم Vector DB وهي PostgreSQL)
# ==================================================================
class VectorDBTableSearchTool(BaseSQLTool):
    name: str = "vector_db_table_search"
    description: str = "Performs semantic search on schema vectors."
    args_schema: type[BaseModel] = VectorSearchInput

    def _run(self, query_key: str, allowed_tables: list) -> str:
        if embedding_model is None:
            return json.dumps([])

        conn = None
        try:
            query_embedding = embedding_model.encode(query_key, normalize_embeddings=True)
            query_embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

            conn = psycopg2.connect(**self.get_vector_db_conn_params())
            cur = conn.cursor()

            # التعامل مع حالة عدم وجود جداول مسموحة لتجنب خطأ SQL
            if not allowed_tables:
                return json.dumps([])
                
            tables_tuple = tuple(allowed_tables)
            # psycopg2 لا يقبل tuple واحد، يجب أن يكون مع فاصلة
            if len(tables_tuple) == 1:
                tables_tuple = (tables_tuple[0],)

            search_query = """
                SELECT table_name
                FROM client_schema_vectors
                WHERE company_id = %s
                AND table_name IN %s
                ORDER BY embedding <-> %s
                LIMIT 12
            """
            cur.execute(search_query, (self.company_id, tables_tuple, query_embedding_str))
            results = cur.fetchall()

            table_names = [r[0] for r in results] if results else []
            return json.dumps(table_names, indent=2)

        except Exception as e:
            traceback.print_exc()
            return json.dumps([])

        finally:
            if conn:
                conn.close()

# ==================================================================
# 6) Get Available Columns Tool (يستخدم Metadata DB وهي PostgreSQL)
# ==================================================================
class GetAvailableColumnsTool(BaseSQLTool):
    name: str = "get_available_columns"
    description: str = "Fetch columns and types for a table from Metadata DB."
    args_schema: type[BaseModel] = GetTableSchemaInput


    def _run(self, table_name: str) -> str:
        try:
            if "." not in table_name:
                return json.dumps([])

            schema, table = table_name.split(".", 1)

            # build pyodbc SQLAlchemy engine
            odbc_connect = self.get_sql_conn_string()
            encoded = quote_plus(odbc_connect)
            conn_str = f"mssql+pyodbc:///?odbc_connect={encoded}"
            engine = create_engine(conn_str, fast_executemany=True)
            query = text("""
                SELECT 
                     c.name AS COLUMN_NAME,
                    t.name AS DATA_TYPE
                FROM sys.columns c
                JOIN sys.types t ON c.user_type_id = t.user_type_id
                JOIN sys.tables tb ON c.object_id = tb.object_id
                JOIN sys.schemas s ON tb.schema_id = s.schema_id
                WHERE s.name = :schema
                 AND tb.name = :table
                ORDER BY c.column_id
            """)
            with engine.connect() as conn:
                 rows = conn.execute(query, {"schema": schema, "table": table}).fetchall()

            columns = [
                {"name": row[0], "type": row[1]}
                for row in rows
            ]

            return json.dumps(columns, indent=2)

        except Exception as e:
            traceback.print_exc()
            return json.dumps([])



# ==================================================================
# 7) Execute SQL Query Tool (Safe)
# ==================================================================
FORBIDDEN = ["INSERT", "DELETE", "UPDATE", "DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE", "REPLACE"]

class ExecuteSQLQueryTool(BaseSQLTool):
    name: str = "execute_sql_query"
    description: str = "Executes ONLY safe SQL SELECT queries on Source DB."
    args_schema: type[BaseModel] = SQLInput

    def _run(self, raw_sql_query: str) -> str:
        query_upper = raw_sql_query.upper().strip()
        if not query_upper.startswith("SELECT") or any(word in query_upper for word in FORBIDDEN):
            return "❌ Security Error: Only safe SELECT queries are allowed."

        try:
            # ✅ التصحيح: استخدام SQLAlchemy/pyodbc للاتصال بـ MS SQL Server (قاعدة بيانات المصدر)
            
            # 1. إنشاء سلسلة اتصال ODBC من بيانات المصدر
            odbc_connect = self.get_sql_conn_string() 
            # 2. تحويلها إلى تنسيق SQLAlchemy (استبدال الفواصل المنقوطة)
            connection_string = f"mssql+pyodbc:///?odbc_connect={odbc_connect.replace(';', '%3B')}"
            # 3. إنشاء المحرك
            engine = create_engine(connection_string)
            
            # 4. قراءة الاستعلام باستخدام المحرك
            df = pd.read_sql(raw_sql_query, engine)
            
            return df.to_markdown(index=False) if not df.empty else "⚠ No data found."

        except Exception as e:
            traceback.print_exc()
            return f"❌ SQL Execution Error: {e}"




