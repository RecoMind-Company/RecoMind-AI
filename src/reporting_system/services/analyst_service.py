"""LangGraph data analysis service."""

import logging
from typing import Dict, Any, Optional
import pandas as pd

from analyst.workflow import get_analysis_app
from exceptions import AnalysisError

logger = logging.getLogger(__name__)


class AnalystService:
    """Service for running the LangGraph data analysis pipeline."""

    def __init__(self):
        """Initializes the AnalystService with a compiled workflow app."""
        self.app = get_analysis_app()

    def run_analysis(self, df: pd.DataFrame, user_request: str) -> str:
        """
        Executes the LangGraph analysis pipeline on a DataFrame.
        
        Args:
            df: Pandas DataFrame returned from query execution.
            user_request: Original user request.
            
        Returns:
            The generated markdown analysis report string.
        """
        if df is None or df.empty:
            logger.error("Attempted to run analysis on empty or None DataFrame.")
            raise AnalysisError("Cannot perform analysis on empty or null DataFrame.")

        logger.info(f"Running LangGraph analysis pipeline on DataFrame with shape {df.shape}")
        initial_state: Dict[str, Any] = {
            "dataframe": df,
            "user_request": user_request,
        }

        final_state = self.app.invoke(initial_state)

        if final_state and final_state.get("analysis_report"):
            logger.info("LangGraph analysis pipeline completed successfully.")
            return final_state["analysis_report"]

        logger.error("LangGraph pipeline failed to generate an analysis report.")
        raise AnalysisError("Analysis graph failed to produce a valid report.")
