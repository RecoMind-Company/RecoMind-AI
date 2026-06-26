"""
Pydantic Request Models
=======================
API input models
"""

from typing import Optional
from pydantic import BaseModel, Field


class PlanGenerateRequest(BaseModel):
    """
    Request model for generating tasks from a plan
    The request coming from .NET Backend
    """

    company_id: str = Field(
        ...,
        description="Company ID",
        examples=["comp_A", "comp_123"]
    )

    team_id: str = Field(
        ...,
        description="Team ID",
        examples=["team_123", "6f0e9b2c-1d7a-4a6e-9a0e-1c7c9f2a1111"]
    )

    plan_text: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Strategic plan text",
        examples=["Launch an advertising campaign on social media platforms and measure results over two months"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "34293b50-0c58-4111-8fcd-b0127dd250ce",
                "team_id": "0dc1400d-a758-424b-80fb-a8ff89078522",
                "plan_text": "Increase company sales by 20% in the next quarter by targeting new customers, following up with potential customers, conducting product presentations, negotiating contracts, completing sales, then preparing a final report showing sales results and performance indicators"
            }
        }


class TaskStatusUpdateRequest(BaseModel):
    """Request for updating task status (for future use)"""

    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="New status")
    comment: Optional[str] = Field(None, description="Optional comment")
