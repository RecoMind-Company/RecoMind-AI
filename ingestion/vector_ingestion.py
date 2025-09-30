import os
import psycopg2
from sentence_transformers import SentenceTransformer
import pyodbc 
import numpy as np
from langchain_openai import ChatOpenAI
import json 
import config 

# =======================================================
# 1. Embedding Model Setup 
# =======================================================

MODEL_NAME = 'BAAI/bge-small-en-v1.5'
print(f"Loading embedding model: {MODEL_NAME}...")
embedding_model = SentenceTransformer(MODEL_NAME) 
print("Embedding Model loaded successfully.")

# =======================================================
# 2. LLM Initialization 
# =======================================================

# LLM is initialized once using config
llm_model = ChatOpenAI(
    model=config.LLM_MODEL_NAME,
    openai_api_key=config.OPENROUTER_API_KEY,
    openai_api_base=config.OPENROUTER_API_BASE,
    temperature=0.1 
)

# =======================================================
# 3. Utility Function: Chunking
# =======================================================

def chunk_list(input_list: list, chunk_size: int):
    """Yield successive n-sized chunks from input_list."""
    for i in range(0, len(input_list), chunk_size):
        yield input_list[i:i + chunk_size]

# =======================================================
# 4. Batch Description Generation and Data Fetching
# 
# NOTE: This function now accepts ALL connection details
# to be ready for the Backend API call in the future.
# =======================================================

def generate_batch_descriptions_with_llm(table_schemas_text: str) -> dict:
    # ... (Implementation remains the same as before)
    prompt = f"""
    Analyze the following SQL table schemas. For each table, generate a single, comprehensive, and business-focused description (exactly ONE sentence). The description must be highly effective for retrieval.
    
    Return the output as a JSON object with a single top-level key 'descriptions', which contains an array of objects. Each object in the array MUST have two keys: 'table_name' (the exact Schema.Table name) and 'description'.
    
    Table Schemas Batch:
    ---
    {table_schemas_text}
    ---
    """
    
    try:
        response = llm_model.invoke(
            prompt, 
            response_format={"type": "json_object"} 
        )
        return json.loads(response.content.strip())
        
    except Exception as e:
        print(f"\nLLM BATCH Error (Skipping Batch): {e}")
        return {}


def fetch_and_describe_tables(db_server: str, db_database: str, db_username: str, db_password: str, company_id: int):
    """
    Fetches all table schemas from SQL Server and generates descriptions.
    Uses the provided connection details and company ID.
    """
    try:
        # Use provided connection details
        conn_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={db_server};DATABASE={db_database};UID={db_username};PWD={db_password}"
        )
        cnxn = pyodbc.connect(conn_string)
        cursor = cnxn.cursor()
        
        # 1. Fetch all table names (Schema.Table)
        cursor.execute("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        all_tables_meta = cursor.fetchall()
        
        table_schema_details = []
        
        # 2. Prepare schema details for all tables
        for table_schema, table_name in all_tables_meta:
            full_table_name = f"{table_schema}.{table_name}"
            
            schema_query = f"""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{table_schema}' AND TABLE_NAME = '{table_name}'
            """
            cursor.execute(schema_query)
            
            schema_details = []
            for col_name, data_type, is_nullable in cursor.fetchall():
                schema_details.append(f"{col_name} ({data_type}, Nullable: {is_nullable})")
            
            table_schema_text = "\n".join(schema_details)
            table_schema_details.append({
                'full_name': full_table_name,
                'schema_text': table_schema_text
            })

        cnxn.close()
        
        print(f"Total tables found: {len(all_tables_meta)}. Starting batch processing...")

        data_to_ingest = []
        CHUNK_SIZE = 15 
        
        # 3. Process data in chunks
        for i, chunk in enumerate(chunk_list(table_schema_details, CHUNK_SIZE)):
            print(f"\n--- Processing Batch {i+1} ({len(chunk)} tables) ---")
            
            all_schema_text_parts = []
            for item in chunk:
                 all_schema_text_parts.append(f"--- Table: {item['full_name']} ---\n{item['schema_text']}\n")
            
            all_schema_text = "\n".join(all_schema_text_parts)
            
            llm_response_json = generate_batch_descriptions_with_llm(all_schema_text)
            
            if not llm_response_json or 'descriptions' not in llm_response_json:
                print(f"WARNING: Failed to get valid JSON for Batch {i+1}. Skipping this batch.")
                continue

            for item in llm_response_json.get('descriptions', []):
                table_name = item.get('table_name')
                description = item.get('description')
                
                if table_name and description:
                    data_to_ingest.append((company_id, table_name, description)) # Use passed company_id
                    print(f"SUCCESS: Mapped {table_name}")
                else:
                    print(f"WARNING: Skipping invalid/missing entry from LLM response in Batch {i+1}.")

        return data_to_ingest

    except Exception as e:
        print(f"\nFATAL ERROR DETAILS: Error during fetching or connecting to SQL Server: {e}")
        return []

# =======================================================
# 5. Ingestion Function (PG Vector Storage)
# =======================================================

def ingest_data_to_pgvector(data_to_ingest: list):
    """Generates embeddings and stores them in the PostgreSQL Vector DB."""
    conn = None
    if not data_to_ingest:
        return
        
    # Get the company ID to clear the relevant data ONLY (Production Safe)
    company_id_to_clear = data_to_ingest[0][0] 
    
    try:
        # Use config. variables for PostgreSQL connection
        conn = psycopg2.connect(
            host=config.VECTOR_DB_HOST,
            database=config.VECTOR_DB_NAME,
            user=config.VECTOR_DB_USER,
            password=config.VECTOR_DB_PASSWORD
        )
        cur = conn.cursor()
        
        # Production Safety: Conditional Delete (Clear only vectors for this Company ID)
        delete_sql = f"DELETE FROM client_schema_vectors WHERE company_id = {company_id_to_clear};"
        cur.execute(delete_sql)
        print(f"Cleaned existing data for Company ID {company_id_to_clear} from client_schema_vectors.")
        
        insert_sql = """
        INSERT INTO client_schema_vectors 
        (company_id, table_name, table_description, embedding) 
        VALUES (%s, %s, %s, %s::vector)
        """
        
        for company_id, table_name, table_description in data_to_ingest:
            embedding = embedding_model.encode(table_description, normalize_embeddings=True) 
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            cur.execute(insert_sql, 
                        (company_id, table_name, table_description, embedding_str))
            
            print(f"Ingested: {table_name} | Desc: {table_description[:50]}...")

        conn.commit()
        cur.close()
        print("Data ingestion complete and committed successfully!")

    except Exception as error:
        print(f"Error during ingestion to PostgreSQL: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# =======================================================
# 6. Execution Block (Mocks the Backend API call)
# =======================================================

def run_ingestion():
    # ⚠️ This function simulates receiving data from the Backend API call.
    # Currently, it reads from config.py for mocking purposes.
    
    # Check API key first
    if not config.OPENROUTER_API_KEY:
        print("FATAL ERROR: OPENROUTER_API_KEY not found in .env. Cannot generate rich descriptions.")
        return

    # Mock the connection details that the Backend will provide
    connection_details = {
        'db_server': config.DB_SERVER,
        'db_database': config.DB_DATABASE,
        'db_username': config.DB_USERNAME,
        'db_password': config.DB_PASSWORD,
        'company_id': config.COMPANY_ID # Use the mocked ID from config
    }

    # 1. Fetch data from SQL Server and generate rich descriptions
    data_to_ingest = fetch_and_describe_tables(
        db_server=connection_details['db_server'],
        db_database=connection_details['db_database'],
        db_username=connection_details['db_username'],
        db_password=connection_details['db_password'],
        company_id=connection_details['company_id']
    )
    
    if data_to_ingest:
        # 2. Ingest data and vectors into PostgreSQL (Vector DB)
        ingest_data_to_pgvector(data_to_ingest)
    else:
        print("Ingestion aborted.")

if __name__ == "__main__":
    run_ingestion()