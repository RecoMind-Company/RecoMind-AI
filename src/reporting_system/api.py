# This is the main API file, designed to be run from the *root* of the project.
# Example: uvicorn api:app

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import logging
import time
import asyncio
from typing import Optional, Any, Dict

# === [MODIFICATION] ===
# Load environment variables *before* any other module
# This ensures all keys (OPENROUTER_API_KEY, etc.) are loaded
# before pipeline.py (and crewai) are imported.
from dotenv import load_dotenv
load_dotenv()
# === [MODIFICATION END] ===

# [MODIFICATION] Import the task AND the celery_app
from pipeline import run_full_pipeline
from celery_worker import celery_app
from celery.result import AsyncResult
# ---

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
# --- End Logging Setup ---

app = FastAPI(
    title="RecoMind AI Analyst API (with Celery)",
    description="API to trigger the full data analysis pipeline via a task queue.",
    version="1.1.0"
)

# --- [MODIFICATION] Updated Pydantic Models ---

class AnalysisRequest(BaseModel):
    """
    The input model for the API request.
    """
    company_id: str
    user_request: str

class TaskSubmitResponse(BaseModel):
    """
    The response sent *immediately* after submitting a task.
    """
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    """
    The response model for checking the status of a task.
    """
    task_id: str
    status: str
    result: Optional[Any] = None # This will hold the report (or error)

# --- End Pydantic Models ---

@app.on_event("startup")
async def startup_event():
    logger.info("RecoMind API starting up...")

@app.post("/run_analysis", response_model=TaskSubmitResponse)
async def http_run_full_pipeline(request: AnalysisRequest):
    """
    [MODIFIED]
    Main endpoint to *submit* an analysis task to the Celery queue.
    This endpoint returns *immediately*.
    """
    task_id_log = f"task_{int(time.time())}"
    logger.info(f"[{task_id_log}] Received analysis request for company: {request.company_id}")
    
    try:
        # --- [MODIFICATION] ---
        # Instead of 'await run_full_pipeline(...)', we use '.delay()'.
        # This sends the task to the Redis queue and returns *immediately*.
        task = run_full_pipeline.delay(
            company_id=request.company_id,
            user_request=request.user_request
        )
        # --- [MODIFICATION END] ---
        
        logger.info(f"[{task_id_log}] Task submitted to Celery. Task ID: {task.id}")

        # --- Return the successful submission response ---
        return TaskSubmitResponse(
            task_id=task.id,
            status="PENDING",
            message="Analysis task has been submitted."
        )

    except Exception as e:
        # --- Handle errors (e.g., if Redis is down) ---
        logger.error(f"[{task_id_log}] Failed to submit task to Celery: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {e}")

# --- [NEW ENDPOINT] ---
@app.get("/get_status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    New endpoint for the client (.NET/Flutter) to poll
    and check the status of a running task.
    """
    
    # Get the task result from the Celery backend (Redis)
    task_result = AsyncResult(task_id, app=celery_app)
    
    response_data = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None
    }
    
    if task_result.successful():
        # Task finished successfully
        # The 'result' is the final report string
        response_data["result"] = task_result.get()
        
    elif task_result.failed():
        # Task failed with an exception
        # 'result' will contain the error message
        response_data["result"] (str(task_result.info)) # Get the exception info
        
    else:
        # Task is still running (PENDING) or in progress
        # 'result' will be the status update (e.g., "STAGE 2: Fetching Data...")
        if task_result.info:
            response_data["result"] = task_result.info.get('status', 'Running...')
            
    return TaskStatusResponse(**response_data)
# --- [NEW ENDPOINT END] ---

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}

# ... (if __name__ == "__main__" block remains the same) ...
if __name__ == "__main__":
    print("--- Starting Uvicorn server (for testing) ---")
    print("--- DO NOT run this way in production ---")
    print("--- Use: uvicorn api:app --reload --port 8000 ---")
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)

