"""Pydantic schemas for API request and response DTOs."""

from typing import Optional, Any
from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Input model for analysis request endpoint."""

    company_id: str = Field(default="34293b50-0c58-4111-8fcd-b0127dd250ce", description="Company unique identifier")
    user_request: str = Field(default="Employees Performance Analysis", description="Natural language analysis request")
    team_name: Optional[str] = Field(default="HR", description="Optional team name for RBAC filtering")

    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "34293b50-0c58-4111-8fcd-b0127dd250ce",
                "user_request": "Employees Performance Analysis",
                "team_name": "HR",
            }
        }


class TaskSubmitResponse(BaseModel):
    """Response model returned immediately upon submitting a task to the queue."""

    task_id: str = Field(..., description="Unique Celery task identifier")
    status: str = Field(..., description="Task submission status")
    message: str = Field(..., description="Human-readable submission message")


class TaskStatusResponse(BaseModel):
    """Response model for polling task status."""

    task_id: str = Field(..., description="Unique Celery task identifier")
    status: str = Field(..., description="Current Celery task state")
    result: Optional[Any] = Field(default=None, description="Task result string, progress status, or error details")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service health status")
