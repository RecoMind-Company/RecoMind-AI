"""
Pydantic Response Models
========================
API output models
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class SuggestedOwner(BaseModel):
    """Suggested owner for the task"""

    user_id: str = Field(..., description="User ID from .NET API")
    job_title: str = Field(..., description="Job title")
    reason: str = Field(..., description="Reason for selection")


class TaskResponse(BaseModel):
    """Task model in the response"""

    task_id: str = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    duration_days: int = Field(..., ge=1, description="Estimated duration in days")
    start_date: str = Field(..., description="Task start date (YYYY-MM-DD)")
    deadline_date: str = Field(..., description="Task deadline date (YYYY-MM-DD)")
    suggested_owner: Optional[SuggestedOwner] = Field(
        None,
        description="Suggested owner (null if no suitable match)"
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for no suitable owner (when suggested_owner = null)"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of task_ids this task depends on"
    )
    status: str = Field(default="to_do", description="Task status")
    priority: str = Field(..., description="Task priority (high/low)")


class ModuleResponse(BaseModel):
    """Module model in the response"""

    module_id: str = Field(..., description="Module ID")
    module_name: str = Field(..., description="Module name")
    tasks: List[TaskResponse] = Field(..., description="List of tasks")


class TimelinePhase(BaseModel):
    """A phase in the timeline"""

    phase: str = Field(..., description="Phase name")
    start_day: int = Field(..., ge=1, description="Start day")
    end_day: int = Field(..., ge=1, description="End day")
    start_date: Optional[str] = Field(None, description="Phase start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Phase end date (YYYY-MM-DD)")


class PlanGenerateResponse(BaseModel):
    """
    Response model for generated plan
    The response returned to .NET Backend
    """

    plan_id: str = Field(..., description="Plan ID")
    plan_title: str = Field(..., description="Plan title")
    status: str = Field(default="draft", description="Plan status")
    start_date: str = Field(..., description="Plan start date (YYYY-MM-DD)")
    deadline_date: str = Field(..., description="Plan deadline date (YYYY-MM-DD)")
    total_estimated_days: int = Field(..., description="Total estimated days")
    modules: List[ModuleResponse] = Field(..., description="List of modules")
    timeline: List[TimelinePhase] = Field(..., description="Timeline")

    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "plan_701",
                "plan_title": "Social Media Campaign Launch",
                "status": "draft",
                "start_date": "2026-06-26",
                "deadline_date": "2026-08-25",
                "total_estimated_days": 60,
                "modules": [
                    {
                        "module_id": "mod_1",
                        "module_name": "Content Preparation",
                        "tasks": [
                            {
                                "task_id": "task_101",
                                "title": "Write ad content",
                                "description": "Write 10 advertising posts for Facebook and Instagram",
                                "duration_days": 7,
                                "start_date": "2026-06-26",
                                "deadline_date": "2026-07-02",
                                "suggested_owner": {
                                    "user_id": "usr_02",
                                    "job_title": "Content Writer",
                                    "reason": "Job Title: Content Writer"
                                },
                                "dependencies": [],
                                "status": "to_do",
                                "priority": "high"
                            }
                        ]
                    }
                ],
                "timeline": [
                    {
                        "phase": "Content Prep",
                        "start_day": 1,
                        "end_day": 12,
                        "start_date": "2026-06-26",
                        "end_date": "2026-07-07"
                    }
                ]
            }
        }


class AsyncTaskResponse(BaseModel):
    """Response for async task submission (Celery)"""

    task_id: str = Field(..., description="Celery Task ID")
    status: str = Field(default="pending", description="Task status")
    message: str = Field(..., description="Informational message")


class TaskStatusResponse(BaseModel):
    """Response for checking async task status"""

    task_id: str = Field(..., description="Celery Task ID")
    status: str = Field(..., description="Task status")
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    result: Optional[Any] = Field(None, description="Final result")
    error: Optional[str] = Field(None, description="Error message if any")


class ErrorResponse(BaseModel):
    """Error message model"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional details")
