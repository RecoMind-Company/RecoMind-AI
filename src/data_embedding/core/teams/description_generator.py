"""
Team description generator
"""
import logging
import time
from typing import List, Dict
from core.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class TeamDescriptionGenerator:
    """
    Generates business-focused descriptions for teams using LLM.
    """
    
    def __init__(self, llm_service: LLMService = None):
        """
        Initialize with an LLM service.
        
        Args:
            llm_service: Optional LLM service instance
        """
        self.llm_service = llm_service or LLMService()
    
    def generate(self, team_name: str) -> str:
        """
        Generate description for a single team.
        
        Args:
            team_name: Name of the team
        
        Returns:
            Description string
        """
        return self.llm_service.generate_team_description(team_name)
    
    def generate_batch(self, teams: List[str]) -> Dict[str, str]:
        """
        Generate descriptions for multiple teams.
        
        Args:
            teams: List of team names
        
        Returns:
            Dictionary of {team_name: description}
        """
        logger.info(f"Generating descriptions for {len(teams)} teams...")
        
        descriptions = {}
        for team in teams:
            try:
                description = self.generate(team)
                descriptions[team] = description
                logger.info(f"  ✓ Generated: {team}")
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"  ✖ Failed for {team}: {e}")
                # Provide fallback
                descriptions[team] = f"{team} Team: Manages {team.lower()} operations."
        
        return descriptions
