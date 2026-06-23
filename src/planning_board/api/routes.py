"""
API Routes
==========
Endpoints للـ Planning Board API
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
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
    description="تحليل الخطة وتحويلها إلى مهام تنفيذية مع توزيع على الموظفين"
)
async def generate_plan(
    request: PlanGenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    توليد المهام من الخطة
    
    - **company_id**: معرف الشركة
    - **team_name**: اسم الفريق/القسم
    - **plan_text**: نص الخطة الاستراتيجية
    """
    try:
        logger.info(f"📥 Received plan generation request for team: {request.team_name}")
        
        # Initialize service
        service = PlanGeneratorService()
        
        # Generate plan
        result = await service.generate(
            company_id=request.company_id,
            team_name=request.team_name,
            plan_text=request.plan_text,
            priority=request.priority,
            deadline_days=request.deadline_days
        )
        
        logger.info(f"✅ Plan generated successfully: {result.plan_id}")
        return result
        
    except PlanningBoardException as e:
        logger.error(f"❌ Planning board error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": type(e).__name__, "message": e.message, "details": e.details}
        )
    except Exception as e:
        logger.exception(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": str(e)}
        )


@router.post(
    "/plans/generate/async",
    response_model=AsyncTaskResponse,
    summary="Generate Tasks Asynchronously",
    description="توليد المهام بشكل غير متزامن (Celery)"
)
async def generate_plan_async(
    request: PlanGenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    توليد المهام بشكل غير متزامن - للخطط الكبيرة
    يرجع task_id للمتابعة
    """
    try:
        logger.info(f"📥 Received async plan generation request for team: {request.team_name}")
        
        # Import Celery task
        from workers.tasks import generate_plan_task
        
        # Submit task to Celery
        task = generate_plan_task.delay(
            company_id=request.company_id,
            team_name=request.team_name,
            plan_text=request.plan_text,
            priority=request.priority,
            deadline_days=request.deadline_days
        )
        
        logger.info(f"📤 Task submitted: {task.id}")
        
        return AsyncTaskResponse(
            task_id=task.id,
            status="pending",
            message="تم استلام الطلب وجاري المعالجة"
        )
        
    except Exception as e:
        logger.exception(f"❌ Failed to submit async task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "TaskSubmissionError", "message": str(e)}
        )


@router.get(
    "/plans/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="Check Async Task Status",
    description="متابعة حالة مهمة التوليد"
)
async def get_task_status(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    متابعة حالة مهمة التوليد الغير متزامنة
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
        logger.exception(f"❌ Failed to get task status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "StatusCheckError", "message": str(e)}
        )


@router.get(
    "/health",
    summary="Health Check",
    description="فحص صحة الـ API"
)
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "planning-board"}
