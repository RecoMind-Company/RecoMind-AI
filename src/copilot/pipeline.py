# pipeline.py
"""
Celery task definitions for RecoMind Copilot.
Contains the main chat processing pipeline as a background task.
"""

import logging
from celery_worker import celery_app
from services.chat_service import create_chat_service
from repositories.metadata_db import MetadataRepository

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def process_chat_task(
    self,
    company_id: str,
    team_name: str,
    user_question: str
) -> dict:
    """
    Celery task for processing chat requests.
    
    This task runs in the background and:
    1. Fetches DB settings from metadata database
    2. Creates the chat service
    3. Processes the question through CrewAI
    4. Returns the result
    
    Args:
        company_id: Company unique identifier
        team_name: User's team for RBAC
        user_question: Natural language question
        
    Returns:
        dict with 'success', 'answer', and 'error' keys
    """
    try:
        # === STAGE 1: Fetch DB Settings ===
        self.update_state(state='PROGRESS', meta={'status': 'STAGE 1: Fetching database settings...'})
        logger.info(f"Pipeline started for company: {company_id}")
        
        db_settings = MetadataRepository.get_source_db_settings(company_id)
        
        if not db_settings:
            logger.error(f"No DB config found for company: {company_id}")
            raise Exception(f"No database configuration found for company_id: {company_id}")
        
        logger.info("✅ STAGE 1 COMPLETE. Database settings fetched.")

        # === STAGE 2: Create Chat Service ===
        self.update_state(state='PROGRESS', meta={'status': 'STAGE 2: Initializing AI agents...'})
        logger.info("🚀 STAGE 2: Creating chat service...")
        
        chat_service = create_chat_service(
            company_id=company_id,
            team_name=team_name,
            db_server=db_settings["db_server"],
            db_database=db_settings["db_database"],
            db_username=db_settings["db_username"],
            db_password=db_settings["db_password"],
        )
        
        logger.info("✅ STAGE 2 COMPLETE. Chat service created.")

        # === STAGE 3: Process Question with CrewAI ===
        self.update_state(state='PROGRESS', meta={'status': 'STAGE 3: Processing question with AI...'})
        logger.info(f"🚀 STAGE 3: Processing question: {user_question}")
        
        result = chat_service.process_question(user_question)
        
        if result["success"]:
            logger.info("✅ STAGE 3 COMPLETE. Answer generated successfully.")
            return {
                "success": True,
                "answer": result["answer"],
                "error": None
            }
        else:
            logger.error(f"❌ PIPELINE HALTED: {result['error']}")
            raise Exception(result["error"])
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        # Re-raise so Celery knows it failed
        raise e
