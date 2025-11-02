# This is the new API file (replaces main.py)
# It defines the Celery-based async endpoints.

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import time
from typing import Optional, Any
from dotenv import load_dotenv

# Load .env variables (like CELERY_BROKER_URL)
load_dotenv()

# Import the task AND the celery_app
from pipeline import run_ingestion_pipeline_task
from celery_worker import celery_app
from celery.result import AsyncResult

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Data Ingestion API (with Celery)",
    description="API to trigger the long-running data ingestion pipeline via a task queue.",
    version="2.0.0"
)

# --- Pydantic Models ---
# (No request body needed for this pipeline)

class TaskSubmitResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None

@app.on_event("startup")
async def startup_event():
    logger.info("Ingestion API starting up...")

@app.post("/start-pipeline", response_model=TaskSubmitResponse)
async def http_run_full_pipeline():
    """
    [MODIFIED]
    Submits the ingestion task to the Celery queue.
    This endpoint returns *immediately*.
    """
    task_id_log = f"task_{int(time.time())}"
    logger.info(f"[{task_id_log}] Received pipeline start request.")
    
    try:
        # Send the task to the Redis queue
        # Note: .delay() does not take any arguments here
        task = run_ingestion_pipeline_task.delay()
        
        logger.info(f"[{task_id_log}] Task submitted to Celery. Task ID: {task.id}")

        return TaskSubmitResponse(
            task_id=task.id,
            status="PENDING",
            message="Ingestion task has been submitted."
        )

    except Exception as e:
        logger.error(f"[{task_id_log}] Failed to submit task to Celery: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {e}")

@app.get("/get_status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    New endpoint for the client to poll
    and check the status of a running task.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    response_data = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None
    }
    
    if task_result.successful():
        response_data["result"] = task_result.get() # Should be {"status": "success", ...}
    elif task_result.failed():
        response_data["result"] = str(task_result.info) # Get the exception info
    else:
        # Task is PENDING or PROGRESS
        if task_result.info:
             response_data["result"] = task_result.info.get('status', 'Running...')
            
    return TaskStatusResponse(**response_data)

@app.get("/health", tags=["Monitoring"])
async def health_check():
    return {"status": "ok"}