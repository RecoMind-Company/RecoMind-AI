"""
Similarity calculator for team assignment
"""
import logging
import numpy as np
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class SimilarityCalculator:
    """
    Calculates cosine similarity between table and team embeddings.
    """
    
    def calculate(
        self,
        table_embeddings: List[Tuple[str, np.ndarray]],
        team_embeddings: Dict[str, np.ndarray],
        threshold: float = 0.6
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate similarity scores between tables and teams.
        
        Args:
            table_embeddings: List of (table_name, embedding) tuples
            team_embeddings: Dictionary of {team_name: embedding}
            threshold: Minimum similarity score (0.0 - 1.0)
        
        Returns:
            Dictionary: {table_name: {team: score}}
        """
        logger.info(f"Calculating similarities for {len(table_embeddings)} tables (threshold={threshold})...")
        
        results = {}
        
        for table_name, table_emb in table_embeddings:
            similarities = {}
            
            # Calculate similarity with each team
            for team_name, team_emb in team_embeddings.items():
                similarity = float(np.dot(table_emb, team_emb))
                
                if similarity >= threshold:
                    similarities[team_name] = similarity
            
            if similarities:
                # Sort by score (highest first)
                sorted_teams = dict(sorted(
                    similarities.items(),
                    key=lambda x: x[1],
                    reverse=True
                ))
                results[table_name] = sorted_teams
            else:
                # No teams passed threshold
                results[table_name] = self._assign_fallback_team(team_embeddings)
        
        logger.info(f"Similarity calculation complete for {len(results)} tables")
        return results
    
    def _assign_fallback_team(self, team_embeddings: Dict[str, np.ndarray]) -> Dict[str, float]:
        """
        Assign a fallback team when no similarities pass threshold.
        
        Args:
            team_embeddings: Available team embeddings
        
        Returns:
            Dictionary with fallback team assignment
        """
        # Try to find a "Shared" or "General" team
        for fallback_name in ["Shared/General", "Shared", "General"]:
            if fallback_name in team_embeddings:
                return {fallback_name: 0.0}
        
        # No fallback team available
        return {}
