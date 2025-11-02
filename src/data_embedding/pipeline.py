import logging
from celery_worker import celery_app
from dotenv import load_dotenv
import os
import sys

# --- [IMPORTANT] ---
# Import the *original* long-running function
# from your old 'core' module
try:
    # --- Adjust Python Path for Module Imports ---
    # This ensures 'core' can be found
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
        
    from core.pipeline import run_ingestion_pipeline
except ImportError as e:
    logging.error(f"FATAL: Could not import old pipeline function from core.pipeline. Error: {e}")
    # Define a placeholder if it fails
    def run_ingestion_pipeline():
        raise Exception("Failed to import core.pipeline.run_ingestion_pipeline")
# ---

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- [NEW] ---
# Wrap your old function in a Celery Task
@celery_app.task(bind=True)
def run_ingestion_pipeline_task(self) -> dict:
    """
    (This is the new Celery Task)
    It runs the old, long-running pipeline and updates its status.
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Pipeline Started...'})
        logger.info("Celery task started: Running ingestion pipeline...")
        
        # --- This is where we call your OLD code ---
        # We run the original *synchronous* function.
        # Celery handles running it in a separate process.
        run_ingestion_pipeline() 
        # ---
        
        logger.info("Celery task finished: Pipeline completed successfully.")
        return {"status": "success", "message": "Pipeline completed successfully."}
    
    except Exception as e:
        self.update_state(state='FAILURE', meta={'status': str(e)})
        logger.error(f"Pipeline task failed: {e}", exc_info=True)
        # Re-raise the exception so Celery knows it failed
        raise e