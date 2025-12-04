# tools/vector_search_tool.py
"""Vector Search Tool - semantic table search with keyword boosting."""

import json
import logging
import traceback
import psycopg2
from pydantic import BaseModel, Field
from typing import List
from tools.base import BaseSQLTool
from utils.embeddings import get_embedding_model

logger = logging.getLogger(__name__)


class VectorSearchInput(BaseModel):
    """Input schema for vector search tool."""
    query_key: str = Field(description="The metric word for semantic search")
    allowed_tables: List[str] = Field(description="List of tables allowed by RBAC")


# Keyword-to-table mappings for boosting
KEYWORD_MAPPINGS = {
    'revenue': ['SalesOrderHeader', 'SalesOrderDetail', 'Order'],
    'sales': ['SalesOrderHeader', 'SalesOrderDetail', 'Sales', 'Order'],
    'order': ['SalesOrderHeader', 'SalesOrderDetail', 'Order'],
    'customer': ['Customer', 'Person'],
    'product': ['Product', 'ProductCategory', 'ProductSubcategory'],
    'employee': ['Employee', 'Person', 'HumanResources'],
}


class VectorDBTableSearchTool(BaseSQLTool):
    """Performs semantic search on schema vectors with keyword boosting."""
    
    name: str = "vector_db_table_search"
    description: str = "Performs semantic search on schema vectors."
    args_schema: type[BaseModel] = VectorSearchInput

    def _run(self, query_key: str, allowed_tables: list) -> str:
        """Execute the tool."""
        embedding_model = get_embedding_model()
        if embedding_model is None:
            return json.dumps([])

        conn = None
        try:
            # Generate embedding
            query_embedding = embedding_model.encode(query_key, normalize_embeddings=True)
            query_embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

            # Connect to vector DB
            conn = psycopg2.connect(**self.get_vector_db_params())
            cur = conn.cursor()

            if not allowed_tables:
                return json.dumps([])

            # Prepare tuple for IN clause
            tables_tuple = tuple(allowed_tables)
            if len(tables_tuple) == 1:
                tables_tuple = (tables_tuple[0],)

            # Semantic search
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
            
            # Apply keyword boosting
            boosted_tables = self._apply_keyword_boosting(query_key, allowed_tables)
            
            # Combine boosted tables with semantic results
            final_results = boosted_tables.copy()
            for t in table_names:
                if t not in final_results:
                    final_results.append(t)
            
            return json.dumps(final_results[:12], indent=2)

        except Exception as e:
            traceback.print_exc()
            return json.dumps([])

        finally:
            if conn:
                conn.close()

    def _apply_keyword_boosting(self, query_key: str, allowed_tables: list) -> list:
        """Apply keyword-based boosting to prioritize relevant tables."""
        query_lower = query_key.lower()
        boosted_tables = []
        
        for keyword, table_patterns in KEYWORD_MAPPINGS.items():
            if keyword in query_lower:
                for table in allowed_tables:
                    for pattern in table_patterns:
                        if pattern in table and table not in boosted_tables:
                            boosted_tables.append(table)
        
        return boosted_tables
