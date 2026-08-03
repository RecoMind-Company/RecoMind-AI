"""Metadata database repository - handles vector DB and source connection metadata."""

import logging
from typing import Optional, Dict
import psycopg2
from config.database import get_vector_db_params
from exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)


class MetadataRepository:
    """Repository for managing metadata operations in PostgreSQL."""

    @staticmethod
    def _get_connection():
        """Creates a new PostgreSQL connection."""
        params = get_vector_db_params()
        return psycopg2.connect(**params)

    @staticmethod
    def get_source_db_settings(company_id: str) -> Optional[Dict[str, str]]:
        """
        Retrieves source database connection settings for a given company.
        
        Args:
            company_id: Unique identifier for the client company.
            
        Returns:
            Dictionary containing db_server, db_database, db_username, db_password
            or None if no record is found.
        """
        if not company_id:
            logger.warning("Attempted to fetch source DB settings with empty company_id.")
            return None

        conn = None
        try:
            conn = MetadataRepository._get_connection()
            with conn.cursor() as cur:
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
                    logger.info(f"Successfully retrieved source DB settings for company: {company_id}")
                    return {
                        "db_server": record[0],
                        "db_database": record[1],
                        "db_username": record[2],
                        "db_password": record[3],
                    }

                logger.warning(f"No source DB settings found for company: {company_id}")
                return None

        except (Exception, psycopg2.Error) as err:
            logger.error(f"Error loading source DB settings for company '{company_id}': {err}")
            raise DatabaseConnectionError(f"Failed to fetch metadata from database: {err}") from err

        finally:
            if conn:
                conn.close()
