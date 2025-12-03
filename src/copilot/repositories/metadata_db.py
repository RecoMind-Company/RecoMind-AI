# repositories/metadata_db.py
"""Metadata database repository - handles Vector DB operations."""

import logging
import psycopg2
from config.settings import (
    VECTOR_DB_HOST,
    VECTOR_DB_NAME,
    VECTOR_DB_USER,
    VECTOR_DB_PASSWORD,
    VECTOR_DB_PORT,
)

logger = logging.getLogger(__name__)


class MetadataRepository:
    """Repository for metadata database operations."""
    
    @staticmethod
    def _get_connection():
        """Create a new database connection."""
        return psycopg2.connect(
            host=VECTOR_DB_HOST,
            database=VECTOR_DB_NAME,
            user=VECTOR_DB_USER,
            password=VECTOR_DB_PASSWORD,
            port=VECTOR_DB_PORT
        )
    
    @staticmethod
    def get_source_db_settings(company_id: str) -> dict | None:
        """
        Retrieve source database connection settings for a company.
        
        Args:
            company_id: The company's unique identifier
            
        Returns:
            Dictionary with db_server, db_database, db_username, db_password
            or None if not found
        """
        conn = None
        try:
            conn = MetadataRepository._get_connection()
            cur = conn.cursor()
            
            query = """
                SELECT server, database, username, password 
                FROM source_connections 
                WHERE company_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1;
            """
            
            cur.execute(query, (company_id,))
            record = cur.fetchone()

            if record:
                return {
                    "db_server": record[0],
                    "db_database": record[1],
                    "db_username": record[2],
                    "db_password": record[3]
                }
            return None

        except Exception as err:
            logger.error(f"Error loading source DB settings: {err}")
            return None

        finally:
            if conn:
                cur.close()
                conn.close()

    @staticmethod
    def get_company_tables(company_id: str) -> list[str]:
        """
        Fetch all tables belonging to a company.
        
        Args:
            company_id: The company's unique identifier
            
        Returns:
            List of table names
        """
        conn = None
        try:
            conn = MetadataRepository._get_connection()
            cur = conn.cursor()

            query = """
                SELECT table_name
                FROM rbac_table_metadata
                WHERE company_id = %s;
            """
            
            cur.execute(query, (company_id,))
            rows = cur.fetchall()

            return [r[0] for r in rows]

        except Exception as e:
            logger.error(f"Error fetching company tables: {e}")
            return []

        finally:
            if conn:
                cur.close()
                conn.close()
