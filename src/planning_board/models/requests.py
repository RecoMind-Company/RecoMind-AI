"""
Pydantic Request Models
=======================
نماذج الـ Input للـ API
"""

from typing import Optional
from pydantic import BaseModel, Field


class PlanGenerateRequest(BaseModel):
    """
    Request model for generating tasks from a plan
    الـ Request اللي بييجي من .NET Backend
    """
    
    company_id: str = Field(
        ...,
        description="معرف الشركة",
        examples=["comp_A", "comp_123"]
    )
    
    team_name: str = Field(
        ...,
        description="اسم الفريق/القسم",
        examples=["Marketing", "Sales", "Engineering"]
    )
    
    plan_text: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="نص الخطة الاستراتيجية",
        examples=["إطلاق حملة إعلانية على مواقع التواصل الاجتماعي وقياس النتائج خلال شهرين"]
    )
    
    # Optional: لو هنستخدمهم لاحقاً
    priority: Optional[str] = Field(
        default="medium",
        description="أولوية الخطة",
        examples=["low", "medium", "high"]
    )
    
    deadline_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="الموعد النهائي بالأيام (اختياري)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "comp_A",
                "team_name": "Marketing",
                "plan_text": "إطلاق حملة إعلانية على مواقع التواصل الاجتماعي وقياس النتائج خلال شهرين",
                "priority": "high",
                "deadline_days": 60
            }
        }


class TaskStatusUpdateRequest(BaseModel):
    """Request for updating task status (للمستقبل)"""
    
    task_id: str = Field(..., description="معرف المهمة")
    status: str = Field(..., description="الحالة الجديدة")
    comment: Optional[str] = Field(None, description="تعليق اختياري")
