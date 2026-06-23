# main.py
"""
RecoMind NL-to-SQL Copilot API
FastAPI application entry point with Celery task queue support.
"""

import os
import time
import logging
from typing import Optional, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from celery.result import AsyncResult

# Load environment variables FIRST
load_dotenv()

from api.routes import router
from pipeline import process_chat_task
from celery_worker import celery_app

# =============================================================================
# Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# =============================================================================
# Pydantic Models
# =============================================================================

class AsyncChatRequest(BaseModel):
    """Request model for async chat endpoint."""
    company_id: str = Field(..., description="Company unique identifier")
    team_name: str = Field(..., description="User's team for RBAC")
    user_question: str = Field(..., description="Natural language question")

    model_config = {
        "json_schema_extra": {
            "example": {
                "company_id": "34293b50-0c58-4111-8fcd-b0127dd250ce",
                "team_name": "Sales",
                "user_question": "What is the total revenue in 2014?"
            }
        }
    }


class TaskSubmitResponse(BaseModel):
    """Response sent immediately after submitting a task."""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response model for checking task status."""
    task_id: str
    status: str
    result: Optional[Any] = None

# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="RecoMind NL-to-SQL Copilot",
    description="Natural Language to SQL query generation with CrewAI agents",
    version="2.0.0",
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None,
    root_path="/copilot",
    servers=[{"url": "/copilot"}]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include sync routes
app.include_router(router)

# =============================================================================
# Async Celery Endpoints
# =============================================================================

@app.post("/chat/async", response_model=TaskSubmitResponse, tags=["Async Chat"])
async def submit_chat_task(request: AsyncChatRequest):
    """Submit a chat request to the background task queue."""
    task_id_log = f"task_{int(time.time())}"
    logger.info(f"[{task_id_log}] Received async chat request for company: {request.company_id}")
    
    try:
        task = process_chat_task.delay(
            company_id=request.company_id,
            team_name=request.team_name,
            user_question=request.user_question
        )
        logger.info(f"[{task_id_log}] Task submitted to Celery. Task ID: {task.id}")
        
        return TaskSubmitResponse(
            task_id=task.id,
            status="PENDING",
            message="Chat task has been submitted to the queue."
        )
    except Exception as e:
        logger.error(f"[{task_id_log}] Failed to submit task to Celery: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {e}")


@app.get("/chat/status/{task_id}", response_model=TaskStatusResponse, tags=["Async Chat"])
async def get_chat_task_status(task_id: str):
    """Check the status of a submitted chat task."""
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        # Safely get status
        try:
            status = task_result.status
        except (ValueError, KeyError) as e:
            logger.warning(f"Failed to get task status for {task_id}: {e}")
            return TaskStatusResponse(
                task_id=task_id,
                status="FAILURE",
                result={"error": "Task failed - unable to retrieve error details."}
            )
        except Exception as e:
            logger.warning(f"Unexpected error getting task status for {task_id}: {e}")
            return TaskStatusResponse(
                task_id=task_id,
                status="FAILURE", 
                result={"error": f"Task status check failed: {str(e)}"}
            )
        
        # Build response
        response_data = {"task_id": task_id, "status": status, "result": None}
        
        # Check task state safely
        is_successful = _safe_call(task_result.successful, False)
        is_failed = _safe_call(task_result.failed, status == "FAILURE")
        
        if is_successful:
            response_data["result"] = _safe_call(task_result.get, {"error": "Failed to get result"})
        elif is_failed:
            response_data["result"] = _get_error_info(task_result)
        else:
            response_data["result"] = _get_progress_info(task_result)
                
        return TaskStatusResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error checking task status {task_id}: {e}", exc_info=True)
        return TaskStatusResponse(
            task_id=task_id,
            status="FAILURE",
            result={"error": f"Failed to check task status: {str(e)}"}
        )


# =============================================================================
# Helper Functions
# =============================================================================

def _safe_call(func, default):
    """Safely call a function and return default on exception."""
    try:
        return func()
    except Exception:
        return default


def _get_error_info(task_result) -> dict:
    """Extract error info from failed task."""
    try:
        error_info = task_result.info
        if isinstance(error_info, Exception):
            return {"error": str(error_info)}
        elif isinstance(error_info, dict):
            return {"error": error_info.get('error', str(error_info))}
        return {"error": str(error_info) if error_info else "Unknown error"}
    except Exception:
        return {"error": "Task failed - unable to retrieve error details"}


def _get_progress_info(task_result) -> Optional[str]:
    """Get progress info for running task."""
    try:
        if task_result.info:
            if isinstance(task_result.info, dict):
                return task_result.info.get('status', 'Running...')
            return str(task_result.info)
    except Exception:
        pass
    return "Processing..."


# =============================================================================
# Startup
# =============================================================================

logger.info(f"Starting RecoMind Copilot API in {ENVIRONMENT} mode")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8002")),
        reload=True,
    )
