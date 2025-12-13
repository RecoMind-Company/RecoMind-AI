"""
Team assigner - assigns teams to tables based on similarity scores
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class TeamAssigner:
    """
    Assigns teams to tables based on similarity scores.
    """
    
    def assign(
        self,
        tables_with_similarities: Dict[str, Dict[str, float]],
        min_teams: int = 1,
        max_teams: int = 3
    ) -> Dict[str, List[str]]:
        """
        Convert similarity scores to final team assignments.
        
        Args:
            tables_with_similarities: {table_name: {team: score}}
            min_teams: Minimum teams to assign
            max_teams: Maximum teams to assign
        
        Returns:
            Dictionary: {table_name: [team1, team2, ...]}
        """
        logger.info(f"Assigning teams to tables (min={min_teams}, max={max_teams})...")
        
        final_assignments = {}
        
        for table_name, team_scores in tables_with_similarities.items():
            if not team_scores:
                final_assignments[table_name] = []
                logger.warning(f"  ⚠ No teams assigned: {table_name}")
                continue
            
            # Take top teams up to max_teams
            assigned_teams = list(team_scores.keys())[:max_teams]
            
            # Ensure minimum teams if available
            if len(assigned_teams) < min_teams and len(team_scores) >= min_teams:
                assigned_teams = list(team_scores.keys())[:min_teams]
            
            final_assignments[table_name] = assigned_teams
            logger.info(f"  ✓ {table_name}: {assigned_teams}")
        
        logger.info(f"Team assignment complete for {len(final_assignments)} tables")
        return final_assignments
