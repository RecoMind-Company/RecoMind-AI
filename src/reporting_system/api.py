# This is the main API file, designed to be run from the *root* of the project.
# Example: uvicorn src.reporting_system.api:app

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import logging
import time
import asyncio
from typing import Optional

# === [MODIFICATION] ===
# Use a simple relative import. Since api.py and pipeline.py
# are in the same directory (reporting_system), this is the
# correct and most robust way.
from .pipeline import run_full_pipeline
# === [MODIFICATION END] ===

# --- Logging Setup ---
# (This setup is good practice for an API)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler() # Output logs to console
    ]
)
logger = logging.getLogger(__name__)
# --- End Logging Setup ---

app = FastAPI(
    title="RecoMind AI Analyst API",
    description="API to trigger the full data analysis pipeline.",
    version="1.0.0"
)

class AnalysisRequest(BaseModel):
    """
    The input model for the API request.
    """
    company_id: str
    user_request: str

class AnalysisResponse(BaseModel):
    """
    The output model for the API response.
    """
    company_id: str
    user_request: str
    status: str
    analysis_report: str
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    logger.info("RecoMind API starting up...")

@app.post("/run_analysis", response_model=AnalysisResponse)
async def http_run_full_pipeline(request: AnalysisRequest):
    """
    Main endpoint to run the full analysis pipeline asynchronously.
    """
    task_id = f"task_{int(time.time())}" # A simple ID for logging
    logger.info(f"[{task_id}] Received analysis request for company: {request.company_id}")
    
    try:
        start_time = time.time()
        
        # --- Run the Async Pipeline ---
        # This calls the modified run_full_pipeline from pipeline.py
        report_text = await run_full_pipeline(
            company_id=request.company_id,
            user_request=request.user_request
        )
        
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"[{task_id}] Pipeline finished successfully. Duration: {duration:.2f}s")
        
        if not report_text:
            logger.warning(f"[{task_id}] Pipeline ran but returned an empty report.")
            raise HTTPException(status_code=500, detail="Pipeline ran but returned no report.")
            
        # --- Return the successful response ---
        return AnalysisResponse(
            company_id=request.company_id,
            user_request=request.user_request,
            status="success",
            analysis_report=report_text
        )

    except HTTPException as http_err:
        # Re-raise HTTPExceptions (like validation errors)
        raise http_err
        
    except Exception as e:
        # --- Handle all other pipeline errors ---
        logger.error(f"[{task_id}] An unexpected error occurred in the pipeline.", exc_info=True)
        # Return a 500 Internal Server Error
        return AnalysisResponse(
            company_id=request.company_id,
            user_request=request.user_request,
            status="error",
            analysis_report="",
            error=f"Internal Server Error: {str(e)}"
        )

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}

# This check is useful if you ever want to run this file directly,
# but using 'uvicorn api:app' is the standard.
if __name__ == "__main__":
    print("--- Starting Uvicorn server (for testing) ---")
    print("--- DO NOT run this way in production ---")
    print("--- Use: uvicorn src.reporting_system.api:app --reload --port 8000 ---")
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)

