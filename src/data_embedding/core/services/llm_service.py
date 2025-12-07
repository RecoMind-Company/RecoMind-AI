"""
LLM service for generating descriptions and team information
"""
import logging
from langchain_openai import ChatOpenAI
from config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Centralized service for all LLM operations.
    Handles description generation and team context generation.
    """
    
    def __init__(self):
        """Initialize the LLM model"""
        if not settings.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found. Cannot initialize LLM service.")
        
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL_NAME,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_API_BASE,
            temperature=0.1
        )
        logger.info(f"LLM Service initialized with model: {settings.LLM_MODEL_NAME}")
    
    def generate_team_description(self, team_name: str) -> str:
        """
        Generate a business-focused description for a team.
        
        Args:
            team_name: Name of the team
        
        Returns:
            Description string suitable for embedding
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
            response = self.llm.invoke(prompt)
            description = response.content.strip()
            logger.info(f"Generated description for team '{team_name}': {description[:100]}...")
            return description
        except Exception as e:
            logger.error(f"Failed to generate description for team '{team_name}': {e}")
            return f"{team_name} Team: Manages data and operations related to {team_name.lower()} activities."
    
    def generate_batch_descriptions(self, table_schemas_text: str) -> dict:
        """
        Generate descriptions for multiple table schemas in one batch.
        
        Args:
            table_schemas_text: Formatted text containing multiple table schemas
        
        Returns:
            Dictionary with 'descriptions' key containing list of table descriptions
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
        
        try:
            response = self.llm.invoke(
                prompt,
                response_format={"type": "json_object"}
            )
            import json
            return json.loads(response.content.strip())
        except Exception as e:
            logger.error(f"LLM batch generation error: {e}")
            return {}
