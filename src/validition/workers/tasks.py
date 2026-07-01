"""
Celery Tasks
=============
Async tasks for validation pipeline
"""

import asyncio
from loguru import logger

from workers.celery_app import celery_app
from services.validation_pipeline import ValidationPipelineService


def run_async(coro):
    """Helper to run async code in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="run_validation_task")
def run_validation_task(
    self,
    company_id: str,
    team_id: str,
    user_request: str,
):
    """
    Celery task for running the full validation pipeline.
    Used for large requests that require long processing time.
    """
    try:
        logger.info(f"[Celery] Starting validation task: {self.request.id}")

        self.update_state(
            state="PROGRESS",
            meta={"progress": 10, "status": "Authenticating and fetching company data..."},
        )

        service = ValidationPipelineService()

        self.update_state(
            state="PROGRESS",
            meta={"progress": 30, "status": "Structuring strategy and searching for precedents..."},
        )

        result = run_async(
            service.run(
                company_id=company_id,
                team_id=team_id,
                user_request=user_request,
            )
        )

        self.update_state(
            state="PROGRESS",
            meta={"progress": 90, "status": "Building validation report..."},
        )

        logger.info(f"[Celery] Task completed: {self.request.id}")

        return result.model_dump()

    except Exception as e:
        logger.exception(f"[Celery] Task failed: {str(e)}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)},
        )
        raise


@celery_app.task(name="health_check_task")
def health_check_task():
    """Task to check worker health"""
    return {"status": "healthy", "worker": "validation"}
