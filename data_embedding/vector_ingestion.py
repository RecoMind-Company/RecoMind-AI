# vector_ingestion.py

import os
import psycopg2
from sentence_transformers import SentenceTransformer
import pyodbc 
import numpy as np
from langchain_openai import ChatOpenAI
import json 
import config 
from collections import defaultdict

# ... (ส่วนของ Embedding Model และ LLM Initialization ไม่มีการเปลี่ยนแปลง) ...
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
# 4. Description Generation and Data Fetching
# =======================================================

def generate_batch_descriptions_with_llm(table_schemas_text: str) -> dict:
    prompt = f"""
    Analyze the following SQL table schemas, paying close attention to the column names and data types. 
    For each table, generate a single, powerful, and concise business-focused description that summarizes its purpose based on its columns. 
    This description is critical for semantic search, so it must be rich with context.

    Return the output as a JSON object with a single top-level key 'descriptions', which contains an array of objects. 
    Each object in the array MUST have two keys: 'table_name' (the exact Schema.Table name) and 'description'.
    
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

### START MODIFICATION ###

def fetch_primary_keys(cursor) -> dict:
    """
    Fetches the primary key for each table in the database.
    Returns a dictionary mapping each table to its primary key column name.
    """
    query = """
    SELECT 
        s.name AS schema_name,
        t.name AS table_name,
        c.name AS column_name
    FROM sys.tables t
    INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
    INNER JOIN sys.indexes i ON t.object_id = i.object_id
    INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
    INNER JOIN sys.columns c ON ic.object_id = c.object_id AND c.column_id = ic.column_id
    WHERE i.is_primary_key = 1;
    """
    cursor.execute(query)
    primary_keys = {}
    for row in cursor.fetchall():
        full_table_name = f"{row.schema_name}.{row.table_name}"
        primary_keys[full_table_name] = row.column_name
    
    print(f"Successfully fetched {len(primary_keys)} primary keys.")
    return primary_keys

def fetch_foreign_key_relationships(cursor) -> dict:
    """ Fetches all foreign key relationships from the SQL Server database. """
    query = """
    SELECT
        fk.name AS constraint_name,
        OBJECT_SCHEMA_NAME(fk.parent_object_id) AS from_schema,
        OBJECT_NAME(fk.parent_object_id) AS from_table,
        c1.name AS from_column,
        OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS to_schema,
        OBJECT_NAME(fk.referenced_object_id) AS to_table,
        c2.name AS to_column
    FROM
        sys.foreign_keys AS fk
    INNER JOIN
        sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
    INNER JOIN
        sys.columns AS c1 ON fkc.parent_object_id = c1.object_id AND fkc.parent_column_id = c1.column_id
    INNER JOIN
        sys.columns AS c2 ON fkc.referenced_object_id = c2.object_id AND fkc.referenced_column_id = c2.column_id;
    """
    cursor.execute(query)
    relationships = defaultdict(list)
    for row in cursor.fetchall():
        from_table_full = f"{row.from_schema}.{row.from_table}"
        to_table_full = f"{row.to_schema}.{row.to_table}"
        relationships[from_table_full].append({
            "from_column": row.from_column,
            "to_table": to_table_full,
            "to_column": row.to_column
        })
    print(f"Successfully fetched {sum(len(v) for v in relationships.values())} foreign key relationships.")
    return dict(relationships)

def fetch_and_describe_tables(db_server: str, db_database: str, db_username: str, db_password: str, company_id: int):
    """
    Fetches schemas, primary keys, and foreign keys, then generates descriptions.
    """
    try:
        conn_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={db_server};DATABASE={db_database};UID={db_username};PWD={db_password}"
        )
        cnxn = pyodbc.connect(conn_string)
        cursor = cnxn.cursor()
        
        # 1. Fetch all key information
        all_pks = fetch_primary_keys(cursor)
        all_fks = fetch_foreign_key_relationships(cursor)
        
        # 2. Fetch all table names
        cursor.execute("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        all_tables_meta = cursor.fetchall()
        
        table_schema_details = []
        
        # 3. Prepare schema and combined key details for all tables
        for table_schema, table_name in all_tables_meta:
            full_table_name = f"{table_schema}.{table_name}"
            
            schema_query = "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?"
            cursor.execute(schema_query, table_schema, table_name)
            
            schema_details_text = "\n".join([f"{col[0]} ({col[1]}, Nullable: {col[2]})" for col in cursor.fetchall()])
            
            # Combine PK and FK info into a single object
            key_info = {
                "pk": all_pks.get(full_table_name),
                "fks": all_fks.get(full_table_name, [])
            }
            
            table_schema_details.append({
                'full_name': full_table_name,
                'schema_text': schema_details_text,
                'key_info': key_info 
            })

        cnxn.close()
        
        print(f"Total tables found: {len(all_tables_meta)}. Starting batch description generation...")

        data_to_ingest = []
        CHUNK_SIZE = 10
        
        # 4. Process data in chunks to generate descriptions
        for i, chunk in enumerate(chunk_list(table_schema_details, CHUNK_SIZE)):
            print(f"\n--- Processing Batch {i+1} ({len(chunk)} tables) ---")
            
            batch_schema_text = "\n".join([f"--- Table: {item['full_name']} ---\n{item['schema_text']}\n" for item in chunk])
            llm_response_json = generate_batch_descriptions_with_llm(batch_schema_text)
            
            if not llm_response_json or 'descriptions' not in llm_response_json:
                print(f"WARNING: Failed to get valid JSON for Batch {i+1}. Skipping batch.")
                continue

            description_map = {item.get('table_name'): item.get('description') for item in llm_response_json.get('descriptions', [])}

            # 5. Combine descriptions with schemas and key_info
            for table_data in chunk:
                table_name = table_data['full_name']
                description = description_map.get(table_name)
                key_info_obj = table_data['key_info']
                
                if table_name and description:
                    data_to_ingest.append((company_id, table_name, description, json.dumps(key_info_obj)))
                    print(f"SUCCESS: Mapped {table_name}")
                else:
                    print(f"WARNING: Could not find a valid description for {table_name}.")

        return data_to_ingest

    except Exception as e:
        print(f"\nFATAL ERROR DETAILS: Error during fetching data: {e}")
        import traceback
        traceback.print_exc()
        return []
### END MODIFICATION ###

# ... (ส่วนของ ingest_data_to_pgvector และ run_ingestion ไม่มีการเปลี่ยนแปลง) ...
# =======================================================
# 5. Ingestion Function (PG Vector Storage)
# =======================================================
def ingest_data_to_pgvector(data_to_ingest: list):
    """Generates embeddings and stores them in the PostgreSQL Vector DB."""
    conn = None
    if not data_to_ingest:
        return
        
    company_id_to_clear = data_to_ingest[0][0] 
    
    try:
        conn = psycopg2.connect(
            host=config.VECTOR_DB_HOST,
            database=config.VECTOR_DB_NAME,
            user=config.VECTOR_DB_USER,
            password=config.VECTOR_DB_PASSWORD
        )
        cur = conn.cursor()
        
        delete_sql = "DELETE FROM client_schema_vectors WHERE company_id = %s;"
        cur.execute(delete_sql, (company_id_to_clear,))
        print(f"Cleaned existing data for Company ID {company_id_to_clear} from client_schema_vectors.")
        
        insert_sql = """
        INSERT INTO client_schema_vectors 
        (company_id, table_name, table_description, table_relations, embedding) 
        VALUES (%s, %s, %s, %s::jsonb, %s::vector)
        """
        
        for company_id, table_name, table_description, relations_json in data_to_ingest:
            embedding = embedding_model.encode(table_description, normalize_embeddings=True) 
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            cur.execute(insert_sql, 
                        (company_id, table_name, table_description, relations_json, embedding_str))
            
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
# 6. Execution Block
# =======================================================
def run_ingestion():
    if not config.OPENROUTER_API_KEY:
        print("FATAL ERROR: OPENROUTER_API_KEY not found in .env. Cannot generate rich descriptions.")
        return

    connection_details = {
        'db_server': config.DB_SERVER,
        'db_database': config.DB_DATABASE,
        'db_username': config.DB_USERNAME,
        'db_password': config.DB_PASSWORD,
        'company_id': config.COMPANY_ID
    }

    data_to_ingest = fetch_and_describe_tables(
        db_server=connection_details['db_server'],
        db_database=connection_details['db_database'],
        db_username=connection_details['db_username'],
        db_password=connection_details['db_password'],
        company_id=int(connection_details['company_id'])
    )
    
    if data_to_ingest:
        ingest_data_to_pgvector(data_to_ingest)
    else:
        print("Ingestion aborted as no data was prepared.")

if __name__ == "__main__":
    run_ingestion()