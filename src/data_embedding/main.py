import uvicorn
from fastapi import FastAPI, HTTPException
import logging
import os
import sys

# --- Adjust Python Path for Module Imports ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# --- Import the pipeline function ---
try:
    # Import the pipeline from the core subdirectory
    from core.pipeline import run_ingestion_pipeline
except ImportError as e:
    logging.error(f"FATAL: Could not import pipeline function from core.pipeline. Error: {e}")
    # Placeholder if import fails
    run_ingestion_pipeline = None

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Create FastAPI App ---
app = FastAPI()

# ===== Synchronous API Endpoint (Wait and Respond) =====
@app.post("/start-pipeline")
async def start_pipeline_endpoint():
    """
    API endpoint that triggers the ingestion pipeline SYNCHRONOUSLY.
    The response is delayed until the long-running pipeline is fully complete.
    """
    logger.info("--- API TRIGGERED: Starting Pipeline SYNCHRONOUSLY ---")
    
    # 1. Check if the pipeline was successfully imported
    if run_ingestion_pipeline is None:
        raise HTTPException(status_code=500, detail="Pipeline setup error: Cannot load core functions.")

    try:
        # 2. Execute the long-running function directly (this will block the request)
        run_ingestion_pipeline() 
        
        logger.info("--- API FINISHED: Pipeline Completed Successfully! ---")
        # 3. Respond after the ~3 minutes process is done
        return {"status": "success", "message": "Pipeline completed successfully."}

    except Exception as e:
        # 4. Handle exceptions and return a 500 response
        logger.error(f"--- PIPELINE FAILED ---: An error occurred during pipeline execution.", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

# --- Root Endpoint ---
@app.get("/")
def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {"status": "API is running. Send POST to /start-pipeline to begin."}

# --- Local Development Entry Point ---
if __name__ == "__main__":
    logger.info("Starting Uvicorn server for local development...")
    # Note: Use 'python -m uvicorn main:app --reload' instead of this block in your terminal
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)