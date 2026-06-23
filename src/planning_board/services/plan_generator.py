"""
Plan Generator Service
======================
الـ Orchestrator الرئيسي - ينسق بين كل الـ Services
"""

from typing import Optional
from loguru import logger

from models.requests import PlanGenerateRequest
from models.responses import (
    PlanGenerateResponse,
    ModuleResponse,
    TaskResponse,
    SuggestedOwner,
    TimelinePhase as TimelinePhaseResponse,
)
from models.entities import Module, TimelinePhase
from services.plan_parser import plan_parser_service
from services.role_matcher import role_matcher_service
from services.assignment_engine import assignment_engine_service
from services.time_estimator import time_estimator_service
from services.timeline_generator import timeline_generator_service
from services.employee_service import get_employee_service
from utils.id_generator import generate_plan_id
from core.exceptions import PlanningBoardException


class PlanGeneratorService:
    """
    الخدمة الرئيسية لتوليد الخطط
    تنسق بين كل الـ Services الفرعية
    """
    
    def __init__(self, use_mock_employees: bool = None):
        self.plan_parser = plan_parser_service
        self.role_matcher = role_matcher_service
        self.assignment_engine = assignment_engine_service
        self.time_estimator = time_estimator_service
        self.timeline_generator = timeline_generator_service
        self.employee_service = get_employee_service(use_mock_employees)
    
    async def generate(
        self,
        company_id: str,
        team_name: str,
        plan_text: str,
        priority: Optional[str] = "medium",
        deadline_days: Optional[int] = None
    ) -> PlanGenerateResponse:
        """
        توليد خطة كاملة مع المهام والتوزيع
        
        Args:
            company_id: معرف الشركة
            team_name: اسم الفريق
            plan_text: نص الخطة
            priority: الأولوية
            deadline_days: الموعد النهائي
            
        Returns:
            PlanGenerateResponse
        """
        try:
            logger.info(f"🚀 Starting plan generation for {team_name}")
            
            # Step 1: Fetch employees
            logger.info("📥 Step 1: Fetching employees...")
            employees = await self.employee_service.fetch_employees(team_name)
            logger.info(f"   Found {len(employees)} employees")
            
            # Step 2: Parse plan with LLM
            logger.info("🤖 Step 2: Parsing plan with LLM...")
            parsed_plan = await self.plan_parser.parse(plan_text)
            logger.info(f"   Parsed: {len(parsed_plan.modules)} modules, {parsed_plan.total_tasks} tasks")
            
            # Step 3: Estimate time for each task
            logger.info("⏱️ Step 3: Estimating task durations...")
            for module in parsed_plan.modules:
                self.time_estimator.estimate_tasks_duration(module.tasks)
            
            # Step 4: Assign tasks to employees
            logger.info("👥 Step 4: Assigning tasks to employees...")
            assigned_modules = self.assignment_engine.assign_tasks_to_employees(
                parsed_plan.modules,
                employees
            )
            
            # Step 5: Generate timeline
            logger.info("📅 Step 5: Generating timeline...")
            timeline = self.timeline_generator.generate_timeline(assigned_modules)
            total_days = self.timeline_generator.calculate_total_days(timeline)
            
            # Step 6: Build response
            logger.info("📦 Step 6: Building response...")
            response = self._build_response(
                plan_id=generate_plan_id(),
                plan_title=parsed_plan.title,
                modules=assigned_modules,
                timeline=timeline,
                total_days=total_days
            )
            
            logger.info(f"✅ Plan generation complete: {response.plan_id}")
            
            return response
            
        except PlanningBoardException:
            raise
        except Exception as e:
            logger.exception(f"❌ Plan generation failed: {str(e)}")
            raise PlanningBoardException(
                message=f"Failed to generate plan: {str(e)}",
                status_code=500,
                details={"team_name": team_name}
            )
    
    def _build_response(
        self,
        plan_id: str,
        plan_title: str,
        modules: list[Module],
        timeline: list[TimelinePhase],
        total_days: int
    ) -> PlanGenerateResponse:
        """بناء الـ Response النهائي"""
        
        module_responses = []
        
        for module in modules:
            task_responses = []
            
            for task in module.tasks:
                suggested_owner = None
                reason = None
                
                if task.suggested_owner:
                    suggested_owner = SuggestedOwner(
                        id=task.suggested_owner.id,
                        name=task.suggested_owner.name,
                        reason=task.assignment_reason or f"Job Title: {task.suggested_owner.job_title}"
                    )
                else:
                    reason = task.assignment_reason
                
                task_response = TaskResponse(
                    task_id=task.task_id,
                    title=task.title,
                    description=task.description,
                    duration_days=task.duration_days,
                    suggested_owner=suggested_owner,
                    reason=reason,
                    dependencies=task.dependencies,
                    status=task.status.value,
                    priority=task.priority.value
                )
                task_responses.append(task_response)
            
            module_response = ModuleResponse(
                module_id=module.module_id,
                module_name=module.module_name,
                tasks=task_responses
            )
            module_responses.append(module_response)
        
        timeline_responses = [
            TimelinePhaseResponse(
                phase=phase.phase,
                start_day=phase.start_day,
                end_day=phase.end_day
            )
            for phase in timeline
        ]
        
        return PlanGenerateResponse(
            plan_id=plan_id,
            plan_title=plan_title,
            status="draft",
            total_estimated_days=total_days,
            modules=module_responses,
            timeline=timeline_responses
        )
