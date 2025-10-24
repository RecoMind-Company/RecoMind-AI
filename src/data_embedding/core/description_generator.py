# src/recomind/data_embedding/core/description_generator.py

from langchain_openai import ChatOpenAI
import json
import time # <--- REQUIRED IMPORT: Added to control request rate
# We no longer need to import the global config file here
from . import embedding_config 

class DescriptionGenerator:
    """
    Uses a Large Language Model (LLM) to generate business-focused descriptions
    for a given list of table schemas.
    """
    def __init__(self):
        # ... (The __init__ method remains exactly the same)
        if not embedding_config.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found. Cannot generate descriptions.")
            
        self.llm_model = ChatOpenAI(
            model=embedding_config.LLM_MODEL_NAME,
            openai_api_key=embedding_config.OPENROUTER_API_KEY,
            openai_api_base=embedding_config.OPENROUTER_API_BASE,
            temperature=0.1
        )

    # ... The _chunk_list and _generate_batch_descriptions methods remain exactly the same ...
    def _chunk_list(self, input_list: list, chunk_size: int):
        # ... (no change)
        for i in range(0, len(input_list), chunk_size):
            yield input_list[i:i + chunk_size]

    def _generate_batch_descriptions(self, table_schemas_text: str) -> dict:
        # ... (no change)
        prompt = f"""
        Analyze the following SQL table schemas. For each table, generate a single,
        powerful, and concise business-focused description summarizing its purpose.
        This description is critical for semantic search, so it must be rich with context.

        Return the output as a JSON object with a single top-level key 'descriptions',
        which contains an array of objects. Each object in the array MUST have two keys:
        'table_name' (the exact Schema.Table name) and 'description'.
        
        Table Schemas Batch:
        ---
        {table_schemas_text}
        ---
        """
        try:
            response = self.llm_model.invoke(
                prompt,
                response_format={"type": "json_object"}
            )
            return json.loads(response.content.strip())
        except Exception as e:
            print(f"\nLLM BATCH Error (Skipping Batch): {e}")
            return {}

    def generate_for_tables(self, tables_data: list, source_settings: dict) -> list:
        """
        Orchestrates the description generation process in batches.

        Args:
            tables_data: A list of table metadata dictionaries from DatabaseScanner.
            source_settings: The dictionary containing the fetched API settings, including company_id.
        """
        data_to_ingest = []
        
        # Extract company_id from the passed dictionary
        company_id = source_settings['company_id']

        print(f"Starting batch description generation for {len(tables_data)} tables...")
        
        for i, chunk in enumerate(self._chunk_list(tables_data, embedding_config.INGESTION_CHUNK_SIZE)):
            print(f"\n--- Processing Batch {i+1} ({len(chunk)} tables) ---")
            
            batch_schema_text = "\n".join([f"--- Table: {item['full_name']} ---\n{item['schema_text']}\n" for item in chunk])
            llm_response_json = self._generate_batch_descriptions(batch_schema_text)
            
            if not llm_response_json or 'descriptions' not in llm_response_json:
                print(f"WARNING: Failed to get valid JSON for Batch {i+1}. Skipping batch.")
                # --- APPLY SLEEP EVEN ON FAILURE to respect rate limits ---
                time.sleep(1) 
                continue

            description_map = {item.get('table_name'): item.get('description') for item in llm_response_json.get('descriptions', [])}

            for table_data in chunk:
                table_name = table_data['full_name']
                description = description_map.get(table_name)
                key_info_obj = table_data['key_info']
                
                if table_name and description:
                    # Use the company_id variable that was extracted earlier
                    data_to_ingest.append(
                        (company_id, table_name, description, json.dumps(key_info_obj))
                    )
                    print(f"SUCCESS: Mapped description for {table_name}")
                else:
                    print(f"WARNING: Could not find a valid description for {table_name} in LLM response.")

            # --- RATE LIMIT FIX: Add a 1-second delay after each batch call ---
            time.sleep(1) # <--- THIS IS THE FIX for 429 errors!

        return data_to_ingest