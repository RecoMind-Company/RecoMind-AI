"""
Description generator using LLM service
"""
import logging
import json
import time
from typing import List, Tuple
from config import settings
from core.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class DescriptionGenerator:
    """
    Generates business-focused descriptions for table schemas using LLM.
    """
    
    def __init__(self, llm_service: LLMService = None):
        """
        Initialize with an LLM service.
        
        Args:
            llm_service: Optional LLM service instance (creates new one if not provided)
        """
        self.llm_service = llm_service or LLMService()
    
    def _chunk_list(self, input_list: list, chunk_size: int):
        """Split a list into chunks of specified size"""
        for i in range(0, len(input_list), chunk_size):
            yield input_list[i:i + chunk_size]
    
    def generate_for_tables(self, tables_data: list, source_settings: dict) -> list:
        """
        Generate descriptions for all tables in batches.
        
        Args:
            tables_data: List of table metadata from DatabaseScanner
            source_settings: Dictionary containing company_id
        
        Returns:
            List of tuples ready for ingestion: (company_id, table_name, description, relations_json)
        """
        data_to_ingest = []
        company_id = source_settings['company_id']
        
        logger.info(f"Starting batch description generation for {len(tables_data)} tables...")
        
        for i, chunk in enumerate(self._chunk_list(tables_data, settings.INGESTION_CHUNK_SIZE)):
            logger.info(f"Processing Batch {i+1} ({len(chunk)} tables)")
            
            # Prepare batch schema text
            batch_schema_text = "\n".join([
                f"--- Table: {item['full_name']} ---\n{item['schema_text']}\n"
                for item in chunk
            ])
            
            # Generate descriptions via LLM
            llm_response = self.llm_service.generate_batch_descriptions(batch_schema_text)
            
            if not llm_response or 'descriptions' not in llm_response:
                logger.warning(f"Failed to get valid JSON for Batch {i+1}. Skipping batch.")
                time.sleep(1)
                continue
            
            # Map descriptions back to tables
            description_map = {
                item.get('table_name'): item.get('description')
                for item in llm_response.get('descriptions', [])
            }
            
            # Prepare data for ingestion
            for table_data in chunk:
                table_name = table_data['full_name']
                description = description_map.get(table_name)
                key_info_obj = table_data['key_info']

                if table_name and description:
                    if isinstance(description, (dict, list)):
                        logger.warning(
                            f"LLM returned non-string description for {table_name} "
                            f"(type={type(description).__name__}), serializing to JSON"
                        )
                        description = json.dumps(description)
                    elif not isinstance(description, str):
                        description = str(description)

                    data_to_ingest.append((
                        company_id,
                        table_name,
                        description,
                        json.dumps(key_info_obj)
                    ))
                    logger.info(f"SUCCESS: Mapped description for {table_name}")
                else:
                    logger.warning(f"Could not find description for {table_name}")
            
            # Rate limiting
            time.sleep(1)
        
        logger.info(f"Description generation complete. Generated {len(data_to_ingest)} descriptions.")
        return data_to_ingest
