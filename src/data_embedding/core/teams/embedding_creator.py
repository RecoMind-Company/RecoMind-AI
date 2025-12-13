"""
Team embedding creator
"""
import logging
import numpy as np
from typing import List, Dict
from core.services.embedding_service import EmbeddingService
from core.teams.description_generator import TeamDescriptionGenerator

logger = logging.getLogger(__name__)


class TeamEmbeddingCreator:
    """
    Creates embeddings for teams based on their descriptions.
    """
    
    def __init__(
        self,
        embedding_service: EmbeddingService = None,
        description_generator: TeamDescriptionGenerator = None
    ):
        """
        Initialize with services.
        
        Args:
            embedding_service: Optional embedding service
            description_generator: Optional team description generator
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.description_generator = description_generator or TeamDescriptionGenerator()
    
    def create(self, teams: List[str]) -> Dict[str, np.ndarray]:
        """
        Create embeddings for all teams.
        
        Args:
            teams: List of team names
        
        Returns:
            Dictionary of {team_name: embedding_vector}
        """
        logger.info(f"Creating embeddings for {len(teams)} teams...")
        
        # Generate descriptions
        descriptions = self.description_generator.generate_batch(teams)
        
        # Create embeddings
        team_embeddings = {}
        for team, description in descriptions.items():
            try:
                embedding = self.embedding_service.encode(description, normalize=True)
                team_embeddings[team] = embedding
                logger.info(f"  ✓ Embedded: {team}")
            except Exception as e:
                logger.error(f"  ✖ Failed to embed {team}: {e}")
        
        logger.info(f"Created {len(team_embeddings)} team embeddings")
        return team_embeddings
