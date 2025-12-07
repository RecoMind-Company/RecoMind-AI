"""
LLM Service for generating descriptions and content
Centralized LLM interaction layer
"""
import logging
from langchain_openai import ChatOpenAI
from config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Centralized service for LLM operations.
    Handles all LLM model initialization and interactions.
    """
    
    def __init__(self):
        """Initialize LLM model with configuration"""
        if not settings.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in configuration")
        
        self.model = ChatOpenAI(
            model=settings.LLM_MODEL_NAME,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_API_BASE,
            temperature=0.1
        )
        logger.info(f"LLM Service initialized with model: {settings.LLM_MODEL_NAME}")
    
    def generate_text(self, prompt: str, response_format: dict = None) -> str:
        """
        Generate text from LLM based on prompt.
        
        Args:
            prompt: The prompt to send to LLM
            response_format: Optional format specification (e.g., {"type": "json_object"})
        
        Returns:
            Generated text response
        """
        try:
            if response_format:
                response = self.model.invoke(prompt, response_format=response_format)
            else:
                response = self.model.invoke(prompt)
            
            return response.content.strip()
        
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise
    
    def generate_team_description(self, team_name: str) -> str:
        """
        Generate business-focused description for a team.
        
        Args:
            team_name: Name of the team
        
        Returns:
            Team description suitable for embedding
        """
        prompt = f"""
Generate a concise, business-focused description for a team named "{team_name}".

Focus on:
- What type of data this team typically works with
- What database tables or information they would need access to
- Their primary business functions

Keep it to 2-3 sentences. Be specific about data and tables.
Return only the description text, no additional formatting.
"""
        
        try:
            description = self.generate_text(prompt)
            logger.info(f"Generated description for team '{team_name}'")
            return description
        
        except Exception as e:
            logger.error(f"Failed to generate description for team '{team_name}': {e}")
            return f"{team_name} Team: Manages data and operations related to {team_name.lower()} activities."
    
    def generate_batch_table_descriptions(self, table_schemas_text: str) -> str:
        """
        Generate descriptions for multiple tables in batch.
        
        Args:
            table_schemas_text: Formatted text containing multiple table schemas
        
        Returns:
            JSON string with table descriptions
        """
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
        
        return self.generate_text(prompt, response_format={"type": "json_object"})
