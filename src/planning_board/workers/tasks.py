"""
Celery Tasks
============
المهام الـ Async للـ Plan Generation
"""

import asyncio
from celery import current_task
from loguru import logger

from workers.celery_app import celery_app
from services.plan_generator import PlanGeneratorService


def run_async(coro):
    """Helper to run async code in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="generate_plan_task")
def generate_plan_task(
    self,
    company_id: str,
    team_name: str,
    plan_text: str,
    priority: str = "medium",
    deadline_days: int = None
):
    """
    Celery task لتوليد الخطة
    يُستخدم للخطط الكبيرة التي تحتاج وقت طويل
    """
    try:
        logger.info(f"🚀 [Celery] Starting plan generation task: {self.request.id}")
        
        # Update state to PROGRESS
        self.update_state(
            state="PROGRESS",
            meta={"progress": 10, "status": "جاري جلب بيانات الموظفين..."}
        )
        
        # Initialize service
        service = PlanGeneratorService()
        
        # Update progress
        self.update_state(
            state="PROGRESS", 
            meta={"progress": 30, "status": "جاري تحليل الخطة..."}
        )
        
        # Run async generation
        result = run_async(
            service.generate(
                company_id=company_id,
                team_name=team_name,
                plan_text=plan_text,
                priority=priority,
                deadline_days=deadline_days
            )
        )
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"progress": 90, "status": "جاري إعداد النتيجة..."}
        )
        
        logger.info(f"✅ [Celery] Task completed: {self.request.id}")
        
        # Return result as dict
        return result.model_dump()
        
    except Exception as e:
        logger.exception(f"❌ [Celery] Task failed: {str(e)}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise


@celery_app.task(name="health_check_task")
def health_check_task():
    """Task للتحقق من صحة الـ Worker"""
    return {"status": "healthy", "worker": "planning_board"}
