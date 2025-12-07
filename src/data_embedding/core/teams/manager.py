"""
Team assignment manager - orchestrates the team assignment process
"""
import logging
import numpy as np
from typing import List, Dict, Tuple
from core.teams.embedding_creator import TeamEmbeddingCreator
from core.teams.similarity_calculator import SimilarityCalculator
from core.teams.assigner import TeamAssigner

logger = logging.getLogger(__name__)


class TeamAssignmentManager:
    """
    Main coordinator for team assignment process.
    Orchestrates the flow: teams → embeddings → similarities → assignments
    """
    
    def __init__(
        self,
        embedding_creator: TeamEmbeddingCreator = None,
        similarity_calculator: SimilarityCalculator = None,
        team_assigner: TeamAssigner = None
    ):
        """
        Initialize manager with components.
        
        Args:
            embedding_creator: Optional team embedding creator
            similarity_calculator: Optional similarity calculator
            team_assigner: Optional team assigner
        """
        self.embedding_creator = embedding_creator or TeamEmbeddingCreator()
        self.similarity_calculator = similarity_calculator or SimilarityCalculator()
        self.team_assigner = team_assigner or TeamAssigner()
        logger.info("TeamAssignmentManager initialized")
    
    def run_assignment_pipeline(
        self,
        company_id: str,
        teams_list: List[str],
        tables_with_embeddings: List[Tuple[str, np.ndarray]],
        threshold: float = 0.6,
        max_teams: int = 3
    ) -> Tuple[Dict[str, List[str]], Dict[str, Dict[str, float]]]:
        """
        Complete team assignment pipeline.
        
        Args:
            company_id: Company UUID
            teams_list: List of team names
            tables_with_embeddings: List of (table_name, embedding) tuples
            threshold: Similarity threshold (default: 0.6)
            max_teams: Maximum teams per table (default: 3)
        
        Returns:
            Tuple of (assignments, confidence_scores):
                - assignments: {table_name: [team1, team2, ...]}
                - confidence_scores: {table_name: {team: score}}
        """
        logger.info(f"Starting team assignment pipeline for company {company_id}")
        logger.info(f"Teams: {teams_list}")
        logger.info(f"Tables: {len(tables_with_embeddings)}")
        logger.info(f"Threshold: {threshold}")
        
        try:
            # Step 1: Create team embeddings
            team_embeddings = self.embedding_creator.create(teams_list)
            
            if not team_embeddings:
                raise Exception("Failed to create any team embeddings")
            
            # Step 2: Calculate similarities
            similarities = self.similarity_calculator.calculate(
                tables_with_embeddings,
                team_embeddings,
                threshold
            )
            
            # Step 3: Assign teams
            assignments = self.team_assigner.assign(similarities, max_teams=max_teams)
            
            logger.info("✓ Team assignment pipeline completed successfully!")
            return assignments, similarities
            
        except Exception as e:
            logger.error(f"✖ Team assignment pipeline failed: {e}")
            raise
