"""FastAPI route definitions for reporting_system."""

import logging
import time
from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from api.schemas import AnalysisRequest, TaskSubmitResponse, TaskStatusResponse, HealthResponse
from celery_worker import celery_app
from pipeline import run_full_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/run_analysis", response_model=TaskSubmitResponse)
async def http_run_full_pipeline(request: AnalysisRequest):
    """Submits an asynchronous data analysis task to the Celery queue."""
    task_id_log = f"task_{int(time.time())}"
    logger.info(f"[{task_id_log}] Received analysis request for company: {request.company_id}")

    try:
        task = run_full_pipeline.delay(
            company_id=request.company_id,
            user_request=request.user_request,
            team_name=request.team_name,
        )
        logger.info(f"[{task_id_log}] Task submitted to Celery queue. Task ID: {task.id}")

        return TaskSubmitResponse(
            task_id=task.id,
            status="PENDING",
            message="Analysis task has been submitted.",
        )

    except Exception as e:
        logger.error(f"[{task_id_log}] Failed to submit task to Celery: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {e}")


@router.get("/get_status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Endpoint for clients to poll the status of a running analysis task."""
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        response_data = {
            "task_id": task_id,
            "status": task_result.status,
            "result": None,
        }

        if task_result.successful():
            response_data["result"] = task_result.get()

        elif task_result.failed():
            response_data["result"] = str(task_result.info)

        else:
            if task_result.info and isinstance(task_result.info, dict):
                response_data["result"] = task_result.info.get("status", "Running...")

        return TaskStatusResponse(**response_data)

    except Exception as e:
        logger.error(f"Error checking task status for {task_id}: {e}", exc_info=True)
        return TaskStatusResponse(
            task_id=task_id,
            status="ERROR",
            result=f"Failed to check task status: {str(e)}",
        )


@router.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok")
