"""Celery background task definition for running the reporting pipeline."""

import logging
from celery_worker import celery_app
from services.pipeline_service import ReportingPipelineService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def run_full_pipeline(self, company_id: str, user_request: str, team_name: str = None) -> str:
    """
    Celery background task orchestrating the full reporting pipeline.
    
    Args:
        company_id: Unique company identifier.
        user_request: User natural language analysis request.
        team_name: Optional team name for RBAC scope.
        
    Returns:
        Generated report markdown string.
    """
    logger.info(f"Pipeline task started for company: {company_id}, team: {team_name}")
    try:
        pipeline_service = ReportingPipelineService()
        report = pipeline_service.run_pipeline(
            company_id=company_id,
            user_request=user_request,
            team_name=team_name,
            task_instance=self,
        )
        logger.info(f"Pipeline task finished successfully for company: {company_id}")
        return report

    except Exception as e:
        logger.error(f"Pipeline task failed for company {company_id}: {e}", exc_info=True)
        raise
