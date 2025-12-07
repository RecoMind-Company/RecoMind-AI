"""
Vector database repository for managing embeddings
"""
import logging
import psycopg2
import json
import numpy as np
from typing import List, Tuple, Dict
from config import settings
from core.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class VectorRepository:
    """
    Handles all database operations for the vector store.
    Responsible for CRUD operations on embeddings.
    """
    
    def __init__(self, embedding_service: EmbeddingService = None):
        """
        Initialize repository with database connection details.
        
        Args:
            embedding_service: Optional embedding service instance
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.conn_details = {
            "host": settings.VECTOR_DB_HOST,
            "database": settings.VECTOR_DB_NAME,
            "user": settings.VECTOR_DB_USER,
            "password": settings.VECTOR_DB_PASSWORD
        }
    
    def _get_connection(self):
        """Create and return a database connection"""
        return psycopg2.connect(**self.conn_details)
    
    def clear_company_data(self, company_id: str, conn=None):
        """
        Remove existing data for a company.
        
        Args:
            company_id: Company UUID
            conn: Optional existing connection
        """
        should_close = conn is None
        if conn is None:
            conn = self._get_connection()
        
        try:
            cur = conn.cursor()
            logger.info(f"Clearing existing data for Company ID {company_id}...")
            cur.execute("DELETE FROM client_schema_vectors WHERE company_id = %s", (company_id,))
            cur.close()
            logger.info("Clearing complete.")
        finally:
            if should_close:
                conn.close()
    
    def save_embeddings(self, data_to_ingest: List[Tuple]) -> int:
        """
        Save table descriptions and their embeddings to database.
        
        Args:
            data_to_ingest: List of (company_id, table_name, description, relations_json)
        
        Returns:
            Number of records inserted
        """
        if not data_to_ingest:
            logger.warning("No data provided to save. Skipping ingestion.")
            return 0
        
        company_id = data_to_ingest[0][0]
        conn = None
        inserted_count = 0
        
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            # Clear existing data
            self.clear_company_data(company_id, conn)
            
            # Prepare insertion
            insert_sql = """
            INSERT INTO client_schema_vectors 
            (company_id, table_name, table_description, table_relations, embedding) 
            VALUES (%s, %s, %s, %s::jsonb, %s::vector)
            """
            
            logger.info(f"Starting ingestion of {len(data_to_ingest)} records...")
            
            for company_id, table_name, description, relations_json in data_to_ingest:
                # Generate embedding
                embedding = self.embedding_service.encode(description, normalize=True)
                embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                
                # Insert record
                cur.execute(insert_sql, (
                    company_id, table_name, description,
                    relations_json, embedding_str
                ))
                inserted_count += 1
                logger.info(f"  -> Ingested: {table_name}")
            
            conn.commit()
            cur.close()
            logger.info(f"Data ingestion complete! Inserted {inserted_count} records.")
            
        except Exception as error:
            logger.error(f"Error during ingestion: {error}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
        
        return inserted_count
    
    def get_table_embeddings(self, company_id: str) -> List[Tuple[str, np.ndarray]]:
        """
        Retrieve table embeddings for a company.
        
        Args:
            company_id: Company UUID
        
        Returns:
            List of (table_name, embedding_array) tuples
        """
        conn = None
        
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            query = """
            SELECT table_name, embedding
            FROM client_schema_vectors
            WHERE company_id = %s
            """
            
            cur.execute(query, (company_id,))
            results = cur.fetchall()
            
            # Parse embeddings
            table_embeddings = []
            for table_name, embedding_str in results:
                embedding_values = embedding_str.strip('[]').split(',')
                embedding_array = np.array([float(v) for v in embedding_values])
                table_embeddings.append((table_name, embedding_array))
            
            logger.info(f"Retrieved {len(table_embeddings)} table embeddings for company {company_id}")
            cur.close()
            return table_embeddings
            
        except Exception as error:
            logger.error(f"Error retrieving table embeddings: {error}")
            raise
        finally:
            if conn:
                conn.close()
    
    def update_team_assignments(
        self,
        company_id: str,
        table_assignments: Dict[str, List[str]],
        confidence_scores: Dict[str, Dict[str, float]] = None
    ) -> int:
        """
        Update team assignments for tables.
        
        Args:
            company_id: Company UUID
            table_assignments: {table_name: [team1, team2, ...]}
            confidence_scores: Optional {table_name: {team: score}}
        
        Returns:
            Number of tables updated
        """
        if not table_assignments:
            logger.warning("No team assignments provided. Skipping update.")
            return 0
        
        conn = None
        updated_count = 0
        
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            logger.info(f"Updating team assignments for {len(table_assignments)} tables...")
            
            # Update team_name column
            update_sql = """
            UPDATE client_schema_vectors
            SET team_name = %s
            WHERE company_id = %s AND table_name = %s
            """
            
            # Audit insertion
            audit_sql = """
            INSERT INTO team_assignment_audit 
            (company_id, table_name, assigned_teams, confidence_scores, assignment_method, created_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """
            
            for table_name, teams in table_assignments.items():
                # Update main table
                cur.execute(update_sql, (teams, company_id, table_name))
                if cur.rowcount > 0:
                    updated_count += 1
                    logger.info(f"  ✓ Updated: {table_name} → {teams}")
                
                # Insert audit record
                if confidence_scores and table_name in confidence_scores:
                    cur.execute(audit_sql, (
                        company_id, table_name, teams,
                        json.dumps(confidence_scores[table_name]),
                        'embedding'
                    ))
            
            conn.commit()
            cur.close()
            logger.info(f"Team assignment update complete! Updated {updated_count} tables.")
            
        except Exception as error:
            logger.error(f"Error during team assignment update: {error}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
        
        return updated_count
