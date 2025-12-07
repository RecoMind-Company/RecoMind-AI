"""
API routes for the ingestion pipeline
"""
import logging
import time
from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from app.models import PipelineRequest, TaskSubmitResponse, TaskStatusResponse
from tasks.celery_app import celery_app
from tasks.pipeline_tasks import run_ingestion_pipeline_task

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/start-pipeline", response_model=TaskSubmitResponse)
async def start_pipeline(request: PipelineRequest):
    """
    Submits the ingestion task to the Celery queue with company_id.
    This endpoint returns immediately.
    
    Args:
        request: PipelineRequest containing company_id
    
    Returns:
        TaskSubmitResponse with task_id and status
    """
    company_id = request.company_id
    task_id_log = f"task_{int(time.time())}"
    logger.info(f"[{task_id_log}] Received pipeline start request for company: {company_id}")
    
    if not company_id:
        raise HTTPException(status_code=400, detail="company_id is required")
    
    try:
        # Send the task to the Redis queue with company_id parameter
        task = run_ingestion_pipeline_task.delay(company_id)
        
        logger.info(f"[{task_id_log}] Task submitted to Celery. Task ID: {task.id}")

        return TaskSubmitResponse(
            task_id=task.id,
            status="PENDING",
            message="Ingestion task has been submitted.",
            company_id=company_id
        )

    except Exception as e:
        logger.error(f"[{task_id_log}] Failed to submit task to Celery: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {e}")


@router.get("/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Endpoint for the client to poll and check the status of a running task.
    
    Args:
        task_id: The Celery task ID
    
    Returns:
        TaskStatusResponse with current task status and result
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    response_data = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None
    }
    
    if task_result.successful():
        response_data["result"] = task_result.get()
    elif task_result.failed():
        response_data["result"] = str(task_result.info)
    else:
        # Task is PENDING or PROGRESS
        if task_result.info:
            response_data["result"] = task_result.info.get('status', 'Running...')
            
    return TaskStatusResponse(**response_data)


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "data-embedding-pipeline"}
