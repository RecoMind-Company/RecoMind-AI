# api/routes.py
"""FastAPI route definitions."""

import logging
from fastapi import APIRouter, HTTPException
from api.schemas import ChatRequest, ChatResponse, HealthResponse
from services.chat_service import create_chat_service
from repositories.metadata_db import MetadataRepository

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Process a natural language question and return the answer.
    
    This endpoint:
    1. Fetches DB settings from metadata database using company_id
    2. Validates user access via RBAC
    3. Searches for relevant tables
    4. Generates and executes SQL
    5. Returns a formatted answer
    """
    try:
        # Fetch DB settings from metadata database
        logger.info(f"Processing chat request for company: {request.company_id}")
        db_settings = MetadataRepository.get_source_db_settings(request.company_id)
        
        if not db_settings:
            logger.warning(f"No DB config found for company: {request.company_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No database configuration found for company_id: {request.company_id}"
            )
        
        # Create chat service with fetched settings
        chat_service = create_chat_service(
            company_id=request.company_id,
            team_name=request.team_name,
            db_server=db_settings["db_server"],
            db_database=db_settings["db_database"],
            db_username=db_settings["db_username"],
            db_password=db_settings["db_password"],
        )
        
        # Process question
        result = chat_service.process_question(request.user_question)
        
        return ChatResponse(
            success=result["success"],
            answer=result["answer"],
            error=result["error"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "RecoMind NL-to-SQL Copilot",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
