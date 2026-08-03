"""Vector DB table search tool using pgvector and fastembed."""

import json
import logging
from typing import Type
from pydantic import BaseModel, Field
import psycopg2
from fastembed import TextEmbedding

from config.settings import EMBEDDING_MODEL_NAME
from tools.base import BaseSQLTool

logger = logging.getLogger(__name__)

# Initialize embedding model lazily or at module level
try:
    embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)
except Exception as err:
    logger.error(f"Failed to load embedding model '{EMBEDDING_MODEL_NAME}': {err}")
    embedding_model = None


class VectorSearchInput(BaseModel):
    """Input schema for vector search tool."""

    query_key: str = Field(description="The user's natural language request or search key.")


class VectorDBTableSearchTool(BaseSQLTool):
    """Tool for performing semantic search on client schema vectors in PostgreSQL."""

    name: str = "vector_db_table_search"
    description: str = (
        "Performs a semantic search on the client's schema descriptions (vectors) "
        "to find the most relevant tables for a user query. "
        "Input MUST be the user's natural language request key. "
        "Returns a list of top relevant tables along with descriptions and JOIN relationships."
    )
    args_schema: Type[BaseModel] = VectorSearchInput

    def _run(self, query_key: str) -> str:
        if not embedding_model:
            logger.error("Embedding model is not initialized.")
            return '{"error": "Embedding model unavailable."}'

        conn = None
        search_limit = 12
        try:
            query_embedding = next(embedding_model.embed([query_key]))
            query_embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

            conn = psycopg2.connect(**self.get_vector_db_conn_params())
            with conn.cursor() as cur:
                query_parts = [
                    "SELECT table_name, table_description, table_relations",
                    "FROM client_schema_vectors",
                    "WHERE company_id = %s",
                ]
                params = [self.company_id]

                if self.team_name:
                    logger.info(f"Filtering tables by team: {self.team_name}")
                    query_parts.append("AND EXISTS (SELECT 1 FROM unnest(team_name) t WHERE t ILIKE %s)")
                    params.append(f"%{self.team_name}%")
                else:
                    logger.info("No team filter applied. Searching all company tables.")

                query_parts.append("ORDER BY embedding <-> %s")
                query_parts.append("LIMIT %s;")
                params.extend([query_embedding_str, search_limit])

                cur.execute("\n".join(query_parts), tuple(params))
                results = cur.fetchall()

                # Fallback mechanism if team filter returns no tables
                if not results and self.team_name:
                    logger.warning(f"No tables found for team '{self.team_name}'. Falling back to global search.")
                    fallback_parts = [
                        "SELECT table_name, table_description, table_relations",
                        "FROM client_schema_vectors",
                        "WHERE company_id = %s",
                        "ORDER BY embedding <-> %s",
                        "LIMIT %s;",
                    ]
                    fallback_params = [self.company_id, query_embedding_str, search_limit]
                    cur.execute("\n".join(fallback_parts), tuple(fallback_params))
                    results = cur.fetchall()

                if not results:
                    logger.warning(f"No tables found in vector database for company {self.company_id}.")
                    return '{"error": "No tables found in vector database. Stop and report this failure."}'

                output = [f"--- Search Results (Top {search_limit}) ---"]
                for table_name, description, relations in results:
                    relations_str = json.dumps(relations) if relations else "[]"
                    output.append(f"Table: {table_name}, Description: {description}, Relations: {relations_str}")

                return "\n".join(output)

        except Exception as e:
            logger.error(f"Error performing vector search: {e}", exc_info=True)
            return f"Error performing vector search: {e}"

        finally:
            if conn:
                conn.close()
