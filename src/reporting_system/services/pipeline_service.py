"""Reporting pipeline orchestration service."""

import logging
from typing import Optional

from repositories.source_db import SourceDBRepository
from services.analyst_service import AnalystService
from services.crew_service import CrewService

logger = logging.getLogger(__name__)


class ReportingPipelineService:
    """Orchestrates the multi-stage AI reporting pipeline."""

    def __init__(self):
        self.analyst_service = AnalystService()

    def run_pipeline(
        self,
        company_id: str,
        user_request: str,
        team_name: Optional[str] = None,
        task_instance: Optional[object] = None,
    ) -> str:
        """
        Runs the complete 3-stage reporting pipeline.
        
        Args:
            company_id: Unique company identifier.
            user_request: User natural language request.
            team_name: Optional team scope.
            task_instance: Optional Celery Task instance for progress reporting.
            
        Returns:
            Generated analysis report string.
        """
        logger.info(f"Starting reporting pipeline for company: {company_id}, team: {team_name}")

        # === STAGE 1: CrewAI Data Collection & SQL Generation ===
        if task_instance and hasattr(task_instance, "update_state"):
            task_instance.update_state(state="PROGRESS", meta={"status": "STAGE 1: CrewAI Started..."})

        crew_service = CrewService(company_id=company_id, team_name=team_name)
        sql_query, source_db_settings = crew_service.run(user_request=user_request)

        # === STAGE 2: Execute Query to DataFrame ===
        if task_instance and hasattr(task_instance, "update_state"):
            task_instance.update_state(state="PROGRESS", meta={"status": "STAGE 2: Fetching Data..."})

        logger.info("Executing query against source database...")
        df = SourceDBRepository.execute_query_to_dataframe(
            query=sql_query,
            db_settings=source_db_settings,
        )

        if df is None or df.empty:
            logger.error("Query execution returned no data.")
            raise Exception("Error: Query returned no data.")

        # === STAGE 3: LangGraph Data Analysis & Report Generation ===
        if task_instance and hasattr(task_instance, "update_state"):
            task_instance.update_state(state="PROGRESS", meta={"status": "STAGE 3: Analyzing Data..."})

        report_text = self.analyst_service.run_analysis(df=df, user_request=user_request)
        logger.info("Reporting pipeline completed successfully.")
        return report_text
