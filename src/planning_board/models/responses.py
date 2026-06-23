"""
Pydantic Response Models
========================
نماذج الـ Output للـ API
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SuggestedOwner(BaseModel):
    """الموظف المقترح للمهمة"""
    
    id: str = Field(..., description="معرف الموظف")
    name: str = Field(..., description="اسم الموظف")
    reason: str = Field(..., description="سبب الاختيار")


class TaskResponse(BaseModel):
    """نموذج المهمة في الـ Response"""
    
    task_id: str = Field(..., description="معرف المهمة")
    title: str = Field(..., description="عنوان المهمة")
    description: str = Field(..., description="وصف المهمة")
    duration_days: int = Field(..., ge=1, description="المدة المقدرة بالأيام")
    suggested_owner: Optional[SuggestedOwner] = Field(
        None, 
        description="الموظف المقترح (null لو مفيش مناسب)"
    )
    reason: Optional[str] = Field(
        None,
        description="سبب عدم وجود موظف مناسب (لو suggested_owner = null)"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="قائمة الـ task_ids اللي المهمة دي تعتمد عليها"
    )
    status: str = Field(default="to_do", description="حالة المهمة")
    priority: Optional[str] = Field(default="medium", description="الأولوية")


class ModuleResponse(BaseModel):
    """نموذج الـ Module في الـ Response"""
    
    module_id: str = Field(..., description="معرف الـ Module")
    module_name: str = Field(..., description="اسم الـ Module")
    tasks: List[TaskResponse] = Field(..., description="قائمة المهام")


class TimelinePhase(BaseModel):
    """مرحلة في الـ Timeline"""
    
    phase: str = Field(..., description="اسم المرحلة")
    start_day: int = Field(..., ge=1, description="يوم البداية")
    end_day: int = Field(..., ge=1, description="يوم النهاية")


class PlanGenerateResponse(BaseModel):
    """
    Response model for generated plan
    الـ Response اللي بيرجع لـ .NET Backend
    """
    
    plan_id: str = Field(..., description="معرف الخطة")
    plan_title: str = Field(..., description="عنوان الخطة")
    status: str = Field(default="draft", description="حالة الخطة")
    total_estimated_days: int = Field(..., description="إجمالي الأيام المقدرة")
    modules: List[ModuleResponse] = Field(..., description="قائمة الـ Modules")
    timeline: List[TimelinePhase] = Field(..., description="الجدول الزمني")
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "plan_701",
                "plan_title": "Social Media Campaign Launch",
                "status": "draft",
                "total_estimated_days": 60,
                "modules": [
                    {
                        "module_id": "mod_1",
                        "module_name": "Content Preparation",
                        "tasks": [
                            {
                                "task_id": "task_101",
                                "title": "كتابة محتوى الإعلانات",
                                "description": "كتابة 10 منشورات إعلانية لفيسبوك وإنستجرام",
                                "duration_days": 7,
                                "suggested_owner": {
                                    "id": "emp_02",
                                    "name": "سارة",
                                    "reason": "Job Title: Content Writer"
                                },
                                "dependencies": [],
                                "status": "to_do"
                            }
                        ]
                    }
                ],
                "timeline": [
                    {"phase": "Content Prep", "start_day": 1, "end_day": 12}
                ]
            }
        }


class AsyncTaskResponse(BaseModel):
    """Response for async task submission (Celery)"""
    
    task_id: str = Field(..., description="Celery Task ID")
    status: str = Field(default="pending", description="حالة المهمة")
    message: str = Field(..., description="رسالة توضيحية")


class TaskStatusResponse(BaseModel):
    """Response for checking async task status"""
    
    task_id: str = Field(..., description="Celery Task ID")
    status: str = Field(..., description="حالة المهمة")
    progress: Optional[int] = Field(None, ge=0, le=100, description="نسبة الإنجاز")
    result: Optional[PlanGenerateResponse] = Field(None, description="النتيجة النهائية")
    error: Optional[str] = Field(None, description="رسالة الخطأ لو فيه")


class ErrorResponse(BaseModel):
    """نموذج رسالة الخطأ"""
    
    error: str = Field(..., description="نوع الخطأ")
    message: str = Field(..., description="رسالة الخطأ")
    details: Optional[dict] = Field(None, description="تفاصيل إضافية")
