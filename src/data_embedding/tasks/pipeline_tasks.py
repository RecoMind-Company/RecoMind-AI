"""
Celery tasks for the ingestion pipeline
"""
import logging
import os
import sys
from dotenv import load_dotenv

from tasks.celery_app import celery_app

# Adjust Python path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the ingestion pipeline
try:
    from core.ingestion_pipeline import run_ingestion_pipeline
except ImportError as e:
    logging.error(f"FATAL: Could not import ingestion pipeline. Error: {e}")
    def run_ingestion_pipeline(company_id: str):
        raise Exception("Failed to import core.ingestion_pipeline.run_ingestion_pipeline")

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.run_ingestion_pipeline")
def run_ingestion_pipeline_task(self, company_id: str) -> dict:
    """
    Celery task wrapper for the data ingestion and team assignment pipeline.
    
    Args:
        company_id: The company UUID to process
    
    Returns:
        dict: Task result with status and message
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'status': f'Pipeline started for company {company_id}...'}
        )
        
        logger.info(f"Celery task started: Running ingestion pipeline for company {company_id}")
        
        # Execute the pipeline
        run_ingestion_pipeline(company_id)
        
        logger.info(f"Celery task completed: Pipeline finished successfully for company {company_id}")
        
        return {
            "status": "success",
            "message": f"Pipeline completed successfully for company {company_id}",
            "company_id": company_id
        }
    
    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': str(e), 'company_id': company_id}
        )
        logger.error(f"Pipeline task failed for company {company_id}: {e}", exc_info=True)
        raise e
