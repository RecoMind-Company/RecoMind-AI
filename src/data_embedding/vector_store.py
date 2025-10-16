# embedding/vector_store.py

import psycopg2
from sentence_transformers import SentenceTransformer
from ..shared import config
from . import embedding_config

class VectorStore:
    """
    Handles the connection to the PostgreSQL vector database,
    generates embeddings, and ingests the final data.
    """
    def __init__(self):
        """Initializes the embedding model and database connection details."""
        print(f"Loading embedding model: {embedding_config.EMBEDDING_MODEL_NAME}...")
        self.embedding_model = SentenceTransformer(embedding_config.EMBEDDING_MODEL_NAME)
        print("Embedding Model loaded successfully.")
        
        self.conn_details = {
            "host": config.VECTOR_DB_HOST,
            "database": config.VECTOR_DB_NAME,
            "user": config.VECTOR_DB_USER,
            "password": config.VECTOR_DB_PASSWORD
        }

    def save(self, data_to_ingest: list):
        """
        Generates embeddings and stores them in the PostgreSQL Vector DB.
        
        Args:
            data_to_ingest: A list of tuples containing the data to be stored.
        """
        if not data_to_ingest:
            print("No data provided to save. Skipping ingestion.")
            return
            
        company_id_to_clear = data_to_ingest[0][0] 
        conn = None
        
        try:
            conn = psycopg2.connect(**self.conn_details)
            cur = conn.cursor()
            
            # 1. Clean existing data for the company to ensure freshness
            print(f"Cleaning existing data for Company ID {company_id_to_clear}...")
            delete_sql = "DELETE FROM client_schema_vectors WHERE company_id = %s;"
            cur.execute(delete_sql, (company_id_to_clear,))
            print("Cleaning complete.")
            
            # 2. Prepare and execute the insertion
            insert_sql = """
            INSERT INTO client_schema_vectors 
            (company_id, table_name, table_description, table_relations, embedding) 
            VALUES (%s, %s, %s, %s::jsonb, %s::vector)
            """
            
            print(f"Starting ingestion of {len(data_to_ingest)} records...")
            for company_id, table_name, table_description, relations_json in data_to_ingest:
                # Generate embedding for the description
                embedding = self.embedding_model.encode(table_description, normalize_embeddings=True)
                
                # Convert numpy array to string format for PGVector, e.g., '[1.2,3.4,...]'
                embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                
                cur.execute(insert_sql, 
                            (company_id, table_name, table_description, relations_json, embedding_str))
                print(f"  -> Ingested: {table_name}")

            conn.commit()
            cur.close()
            print("\nData ingestion complete and committed successfully!")

        except Exception as error:
            print(f"Error during ingestion to PostgreSQL: {error}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()