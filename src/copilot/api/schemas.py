# api/schemas.py
"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    company_id: str = Field(..., description="Company unique identifier")
    team_name: str = Field(..., description="User's team for RBAC")
    user_question: str = Field(..., description="Natural language question")

    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "fb140d33-7e96-474d-a06d-ab3a6c65d1a9",
                "team_name": "Sales",
                "user_question": "What is the total revenue in 2014?"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    success: bool = Field(..., description="Whether the request succeeded")
    answer: Optional[str] = Field(None, description="The formatted answer")
    error: Optional[str] = Field(None, description="Error message if failed")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
