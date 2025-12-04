# services/chat_service.py
"""High-level chat service for the API."""

import logging
from services.crew_service import CrewService

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat requests."""

    def __init__(
        self,
        company_id: str,
        team_name: str,
        db_server: str,
        db_database: str,
        db_username: str,
        db_password: str,
    ):
        """Initialize with connection parameters."""
        self.crew_service = CrewService(
            company_id=company_id,
            team_name=team_name,
            db_server=db_server,
            db_database=db_database,
            db_username=db_username,
            db_password=db_password,
        )

    def process_question(self, question: str) -> dict:
        """
        Process a user question and return the response.
        
        Args:
            question: The natural language question
            
        Returns:
            dict with 'answer' key containing the response
        """
        try:
            logger.info(f"Processing question: {question}")
            answer = self.crew_service.run(question)
            logger.info("Question processed successfully")
            return {
                "success": True,
                "answer": answer,
                "error": None,
            }
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            return {
                "success": False,
                "answer": None,
                "error": str(e),
            }


def create_chat_service(
    company_id: str,
    team_name: str,
    db_server: str,
    db_database: str,
    db_username: str,
    db_password: str,
) -> ChatService:
    """Factory function to create a ChatService."""
    return ChatService(
        company_id=company_id,
        team_name=team_name,
        db_server=db_server,
        db_database=db_database,
        db_username=db_username,
        db_password=db_password,
    )
