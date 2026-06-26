"""
API Routes
==========
Endpoints for the Planning Board API
"""

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api.dependencies import verify_api_key
from models.requests import PlanGenerateRequest
from models.responses import (
    PlanGenerateResponse,
    AsyncTaskResponse,
    TaskStatusResponse,
    ErrorResponse,
)
from services.plan_generator import PlanGeneratorService
from core.exceptions import PlanningBoardException


router = APIRouter(tags=["Plans"])


@router.post(
    "/plans/generate",
    response_model=PlanGenerateResponse,
    responses={
        200: {"description": "Plan generated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        502: {"model": ErrorResponse, "description": "LLM service error"},
    },
    summary="Generate Tasks from Plan",
    description="Analyze the plan and convert it into executable tasks with employee assignment"
)
async def generate_plan(
    request: PlanGenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Generate tasks from a plan

    - **company_id**: Company ID
    - **team_id**: Team ID
    - **plan_text**: Strategic plan text
    """
    try:
        logger.info(f"Received plan generation request for team_id: {request.team_id}")

        # Initialize service
        service = PlanGeneratorService()

        # Generate plan
        result = await service.generate(
            company_id=request.company_id,
            team_id=request.team_id,
            plan_text=request.plan_text,
        )

        logger.info(f"Plan generated successfully: {result.plan_id}")
        return result

    except PlanningBoardException as e:
        logger.error(f"Planning board error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": type(e).__name__, "message": e.message, "details": e.details}
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": str(e)}
        )


@router.post(
    "/plans/generate/async",
    response_model=AsyncTaskResponse,
    summary="Generate Tasks Asynchronously",
    description="Generate tasks asynchronously (Celery)"
)
async def generate_plan_async(
    request: PlanGenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Generate tasks asynchronously - for large plans
    Returns a task_id for tracking
    """
    try:
        logger.info(f"Received async plan generation request for team_id: {request.team_id}")

        # Import Celery task
        from workers.tasks import generate_plan_task

        # Submit task to Celery
        task = generate_plan_task.delay(
            company_id=request.company_id,
            team_id=request.team_id,
            plan_text=request.plan_text,
        )

        logger.info(f"Task submitted: {task.id}")

        return AsyncTaskResponse(
            task_id=task.id,
            status="pending",
            message="Request received and processing"
        )

    except Exception as e:
        logger.exception(f"Failed to submit async task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "TaskSubmissionError", "message": str(e)}
        )


@router.get(
    "/plans/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="Check Async Task Status",
    description="Track the status of a generation task"
)
async def get_task_status(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Track the status of an asynchronous generation task
    """
    try:
        from workers.celery_app import celery_app

        task_result = celery_app.AsyncResult(task_id)

        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.status
        )

        if task_result.ready():
            if task_result.successful():
                response.result = task_result.result
                response.progress = 100
            else:
                response.error = str(task_result.result)
        elif task_result.status == "PROGRESS":
            response.progress = task_result.info.get("progress", 0)

        return response

    except Exception as e:
        logger.exception(f"Failed to get task status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "StatusCheckError", "message": str(e)}
        )


@router.get(
    "/health",
    summary="Health Check",
    description="Check API health"
)
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "planning-board"}
