"""
Celery Tasks
============
Async tasks for Plan Generation
"""

import asyncio
from loguru import logger

from workers.celery_app import celery_app
from services.plan_generator import PlanGeneratorService


def run_async(coro):
    """Helper to run async code in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="generate_plan_task")
def generate_plan_task(
    self,
    company_id: str,
    team_id: str,
    plan_text: str,
):
    """
    Celery task for plan generation
    Used for large plans that require long processing time
    """
    try:
        logger.info(f"[Celery] Starting plan generation task: {self.request.id}")

        # Update state to PROGRESS
        self.update_state(
            state="PROGRESS",
            meta={"progress": 10, "status": "Fetching employee data..."}
        )

        # Initialize service
        service = PlanGeneratorService()

        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"progress": 30, "status": "Analyzing plan..."}
        )

        # Run async generation
        result = run_async(
            service.generate(
                company_id=company_id,
                team_id=team_id,
                plan_text=plan_text,
            )
        )

        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"progress": 90, "status": "Preparing result..."}
        )

        logger.info(f"[Celery] Task completed: {self.request.id}")

        # Return result as dict
        return result.model_dump()

    except Exception as e:
        logger.exception(f"[Celery] Task failed: {str(e)}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise


@celery_app.task(name="health_check_task")
def health_check_task():
    """Task to check worker health"""
    return {"status": "healthy", "worker": "planning_board"}
