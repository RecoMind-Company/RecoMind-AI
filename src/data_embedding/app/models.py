"""
Pydantic models for API request/response schemas
"""
from pydantic import BaseModel
from typing import Optional, Any


class PipelineRequest(BaseModel):
    """Request model for starting the ingestion pipeline"""
    company_id: str


class TaskSubmitResponse(BaseModel):
    """Response model when a task is submitted"""
    task_id: str
    status: str
    message: str
    company_id: str


class TaskStatusResponse(BaseModel):
    """Response model for task status check"""
    task_id: str
    status: str
    result: Optional[Any] = None
