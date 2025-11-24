# (Production-Ready Version)
# ================================================================
from crewai import Tool
from typing import List, Dict, Any
from sqlalchemy import create_engine, text, inspect
import pandas as pd
import json
import os

# ================================================================
# 1. DATABASE CONNECTIONS
# ================================================================

def create_db_engine(url: str, label: str):
    """Create SQLAlchemy engine with safe error handling."""
    try:
        engine = create_engine(url)
        return engine
    except Exception as e:
        print(f"[ERROR] Failed to connect to {label} database: {e}")
        return None

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./example.db")
METADATA_URL = os.getenv("METADATA_URL", "sqlite:///./metadata.db")

SQL_ENGINE = create_db_engine(DATABASE_URL, "MAIN")
METADATA_ENGINE = create_db_engine(METADATA_URL, "METADATA")


# ================================================================
# 2. HELPERS
# ================================================================

def format_json(payload: Dict[str, Any]) -> str:
    """Safe JSON dumping."""
    return json.dumps(payload, ensure_ascii=False, indent=2)

def safe_error(msg: str) -> str:
    return format_json({"error": msg})


# ================================================================
# 3. TOOL 1 — RBAC: Get Allowed Tables (Agent 2)
# ================================================================

def get_allowed_tables(company_id: int, team_name: str) -> str:
    """Return allowed tables based on RBAC rules."""

    if METADATA_ENGINE is None:
        return safe_error("Metadata DB connection failed.")

    query = text("""
        SELECT table_name
        FROM rbac_metadata
        WHERE company_id = :cid AND team_name LIKE :tname;
    """)

    try:
        with METADATA_ENGINE.connect() as conn:
            result = conn.execute(query, {
                "cid": company_id,
                "tname": f"%{team_name}%"
            }).fetchall()

        allowed = [row[0] for row in result]

        return format_json({
            "company_id": company_id,
            "team_name": team_name,
            "allowed_tables": allowed
        })

    except Exception as e:
        return safe_error(f"Failed to retrieve allowed tables: {e}")


GetAllowedTablesTool = Tool(
    name="GetAllowedTablesTool",
    func=get_allowed_tables,
    description=(
        "Retrieve allowed table names based on RBAC access rules using Company ID "
        "and Team Name."
    )
)


# ================================================================
# 4. TOOL 2 — Vector DB Semantic Search (Agent 3)
# ================================================================

def vector_db_table_search(metric_word: str, allowed_tables_list: List[str]) -> str:
    """
    Perform semantic table search restricted by allowed tables.
    Replace mock logic with actual Vector DB (Chroma / PgVector / Pinecone).
    """

    if not allowed_tables_list:
        return safe_error("User has no allowed tables.")

    metric_lower = metric_word.lower()

    # ---- Mock Semantic Logic (Replace with real vector search) ----
    prioritized = {
        "revenue": "Sales.FactRevenue",
        "sales": "Sales.FactRevenue",
        "orders": "Sales.FactOrders",
        "order": "Sales.FactOrders",
    }

    selected_table = None
    for key, tbl in prioritized.items():
        if key in metric_lower and tbl in allowed_tables_list:
            selected_table = tbl
            break

    if selected_table is None:
        selected_table = allowed_tables_list[0]

    return format_json({
        "metric": metric_word,
        "selected_table": selected_table,
        "reason": "Semantic match (mock) restricted to allowed tables."
    })


VectorDBTableSearchTool = Tool(
    name="VectorDBTableSearchTool",
    func=vector_db_table_search,
    description=(
        "Perform semantic table selection based on metric words, restricted to "
        "allowed tables only."
    )
)


# ================================================================
# 5. TOOL 3 — Get Table Columns (Agent 3)
# ================================================================

def get_available_columns(table_name: str) -> str:
    """Return a table's column schema (name + SQL type)."""

    if SQL_ENGINE is None:
        return safe_error("Main DB connection failed.")

    try:
        inspector = inspect(SQL_ENGINE)

        schema, table = (table_name.split('.') + [None])[:2]
        columns = inspector.get_columns(table, schema=schema)

        formatted = [
            {"column": col["name"], "type": str(col["type"])}
            for col in columns
        ]

        return format_json({
            "table": table_name,
            "columns": formatted
        })

    except Exception as e:
        return safe_error(f"Failed retrieving schema for {table_name}: {e}")


GetAvailableColumnsTool = Tool(
    name="GetAvailableColumnsTool",
    func=get_available_columns,
    description="Return full column schema (name + SQL type) for the given table."
)


# ================================================================
# 6. TOOL 4 — Execute SQL Safely (Agent 5)
# ================================================================

FORBIDDEN_SQL = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]

def execute_sql_query(raw_sql_query: str) -> str:
    """Execute SQL SELECT query and return DataFrame as Markdown."""

    if SQL_ENGINE is None:
        return safe_error("Main DB connection failed.")

    # Security: Stop dangerous queries
    if any(keyword in raw_sql_query.upper() for keyword in FORBIDDEN_SQL):
        return safe_error("Unsafe SQL detected. Query blocked.")

    try:
        with SQL_ENGINE.connect() as conn:
            df = pd.read_sql_query(text(raw_sql_query), conn)

        if df.empty:
            return format_json({"result": "No rows returned."})

        return df.to_markdown(index=False)

    except Exception as e:
        return safe_error(f"SQL execution error: {e}")


ExecuteSQLQueryTool = Tool(
    name="ExecuteSQLQueryTool",
    func=execute_sql_query,
    description="Safely execute SQL SELECT queries and return results as Markdown."
)

# ================================================================
# END OF FILE
# ================================================================
