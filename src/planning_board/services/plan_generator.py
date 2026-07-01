"""
Plan Generator Service
======================
Main Orchestrator - coordinates between all Services
"""

from datetime import date, timedelta
from loguru import logger

from models.responses import (
    PlanGenerateResponse,
    ModuleResponse,
    TaskResponse,
    SuggestedOwner,
    TimelinePhase as TimelinePhaseResponse,
)
from models.entities import Module, TimelinePhase
from services.plan_parser import plan_parser_service
from services.assignment_engine import assignment_engine_service
from services.timeline_generator import timeline_generator_service
from services.employee_service import get_employee_service
from utils.id_generator import generate_plan_id
from core.exceptions import PlanningBoardException


class PlanGeneratorService:
    """
    Main service for generating plans.
    Coordinates between all sub-services.
    """

    def __init__(self):
        self.plan_parser = plan_parser_service
        self.assignment_engine = assignment_engine_service
        self.timeline_generator = timeline_generator_service
        self.employee_service = get_employee_service()

    async def generate(
        self,
        company_id: str,
        team_id: str,
        plan_text: str,
    ) -> PlanGenerateResponse:
        """
        Generate a complete plan with tasks and assignments.

        Args:
            company_id: Company identifier
            team_id: Team identifier
            plan_text: Plan text

        Returns:
            PlanGenerateResponse
        """
        try:
            logger.info(f"🚀 Starting plan generation for team_id={team_id}")

            # Step 1: Fetch employees
            logger.info("📥 Step 1: Fetching employees...")
            employees = await self.employee_service.fetch_employees(
                company_id=company_id,
                team_id=team_id,
            )
            logger.info(f"   Found {len(employees)} employees")

            # Step 2: Parse plan with LLM (pass team info for duration estimation)
            logger.info("🤖 Step 2: Parsing plan with LLM...")
            parsed_plan = await self.plan_parser.parse(plan_text, employees)
            logger.info(
                f"   Parsed: {len(parsed_plan.modules)} modules, "
                f"{parsed_plan.total_tasks} tasks, "
                f"estimated {parsed_plan.estimated_duration_days} days"
            )

            # Step 3: Assign tasks to employees
            logger.info("👥 Step 3: Assigning tasks to employees...")
            assigned_modules = await self.assignment_engine.assign_tasks_to_employees(
                parsed_plan.modules,
                employees
            )

            # Step 4: Calculate dates for plan and tasks
            logger.info("📅 Step 4: Calculating dates...")
            plan_start_date = date.today()
            total_days = self._calculate_task_dates(assigned_modules, plan_start_date)
            plan_deadline_date = plan_start_date + timedelta(days=total_days - 1)
            logger.info(
                f"   Plan: {plan_start_date.isoformat()} → {plan_deadline_date.isoformat()} ({total_days} days)"
            )

            # Step 5: Generate timeline
            logger.info("📊 Step 5: Generating timeline...")
            timeline = self.timeline_generator.generate_timeline(assigned_modules)
            self._attach_dates_to_timeline(timeline, plan_start_date)

            # Step 6: Build response
            logger.info("📦 Step 6: Building response...")
            response = self._build_response(
                plan_id=generate_plan_id(),
                plan_title=parsed_plan.title,
                modules=assigned_modules,
                timeline=timeline,
                total_days=total_days,
                plan_start_date=plan_start_date.isoformat(),
                plan_deadline_date=plan_deadline_date.isoformat(),
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
                details={"company_id": company_id, "team_id": team_id}
            )

    def _calculate_task_dates(
        self,
        modules: list[Module],
        start_date: date,
    ) -> int:
        """
        Calculate start and end dates for each task sequentially.
        Returns the total number of days.
        """
        current_date = start_date
        for module in modules:
            for task in module.tasks:
                task.start_date = current_date.isoformat()
                task_end = current_date + timedelta(days=task.duration_days - 1)
                task.deadline_date = task_end.isoformat()
                current_date = task_end + timedelta(days=1)
        if start_date == current_date:
            return 1
        return (current_date - start_date).days

    def _attach_dates_to_timeline(
        self,
        timeline: list[TimelinePhase],
        plan_start_date: date,
    ) -> None:
        """Attach actual dates to Timeline phases."""
        for phase in timeline:
            phase.start_date = (plan_start_date + timedelta(days=phase.start_day - 1)).isoformat()
            phase.end_date = (plan_start_date + timedelta(days=phase.end_day - 1)).isoformat()

    def _build_response(
        self,
        plan_id: str,
        plan_title: str,
        modules: list[Module],
        timeline: list[TimelinePhase],
        total_days: int,
        plan_start_date: str,
        plan_deadline_date: str,
    ) -> PlanGenerateResponse:
        """Build the final response"""

        module_responses = []

        for module in modules:
            task_responses = []

            for task in module.tasks:
                suggested_owner = None
                reason = None

                if task.suggested_owner:
                    suggested_owner = SuggestedOwner(
                        user_id=task.suggested_owner.id,
                        job_title=task.suggested_owner.job_title,
                        reason=task.assignment_reason or f"Job Title: {task.suggested_owner.job_title}"
                    )
                else:
                    reason = task.assignment_reason

                task_response = TaskResponse(
                    task_id=task.task_id,
                    title=task.title,
                    description=task.description,
                    duration_days=task.duration_days,
                    start_date=task.start_date,
                    deadline_date=task.deadline_date,
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
                end_day=phase.end_day,
                start_date=phase.start_date,
                end_date=phase.end_date,
            )
            for phase in timeline
        ]

        return PlanGenerateResponse(
            plan_id=plan_id,
            plan_title=plan_title,
            status="draft",
            start_date=plan_start_date,
            deadline_date=plan_deadline_date,
            total_estimated_days=total_days,
            modules=module_responses,
            timeline=timeline_responses
        )
