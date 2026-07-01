"""
Plan Parser Service
===================
Parse the plan using LLM and convert it to Modules and Tasks
"""

from typing import List
from loguru import logger

from llm.client import llm_client
from llm.prompts import PLAN_PARSER_SYSTEM_PROMPT, PLAN_PARSER_USER_PROMPT
from models.entities import Module, Task, ParsedPlan, Employee, Priority
from utils.id_generator import generate_module_id, generate_task_id
from core.exceptions import LLMException


class PlanParserService:
    """Plan parsing service"""

    def __init__(self):
        self.llm = llm_client

    async def parse(self, plan_text: str, employees: List[Employee] = None) -> ParsedPlan:
        """
        Parse plan text and convert to ParsedPlan

        Args:
            plan_text: Strategic plan text
            employees: List of available employees (to pass to the LLM)

        Returns:
            ParsedPlan object with Modules and Tasks
        """
        try:
            logger.info("📝 Starting plan parsing...")

            # Build team info for prompt
            employee_count = len(employees) if employees else 0
            job_titles = (
                "\n".join(f"- {emp.job_title}" for emp in employees)
                if employees
                else "- Not available"
            )

            # Build prompt
            user_prompt = PLAN_PARSER_USER_PROMPT.format(
                plan_text=plan_text,
                employee_count=employee_count,
                job_titles=job_titles,
            )

            # Call LLM
            result = await self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=PLAN_PARSER_SYSTEM_PROMPT,
                temperature=0.3  # Lower for consistent output
            )

            # Convert to entities
            parsed_plan = self._convert_to_parsed_plan(result)

            logger.info(f"✅ Plan parsed: {len(parsed_plan.modules)} modules, {parsed_plan.total_tasks} tasks, estimated {parsed_plan.estimated_duration_days} days")

            return parsed_plan

        except LLMException:
            raise
        except Exception as e:
            logger.error(f"❌ Plan parsing failed: {str(e)}")
            raise LLMException(
                message=f"Failed to parse plan: {str(e)}",
                details={"plan_text_length": len(plan_text)}
            )

    def _convert_to_parsed_plan(self, llm_result: dict) -> ParsedPlan:
        """Convert LLM result to ParsedPlan"""

        modules: List[Module] = []
        task_counter = 100  # Start task IDs from 100

        for mod_idx, mod_data in enumerate(llm_result.get("modules", []), start=1):
            module_id = generate_module_id(mod_idx)

            tasks: List[Task] = []
            pending_dependencies: dict[str, list[str]] = {}
            title_to_task_id: dict[str, str] = {}

            for task_data in mod_data.get("tasks", []):
                task_counter += 1
                task_id = generate_task_id(task_counter)

                # Parse priority from LLM output
                priority_str = task_data.get("priority", "medium").lower()
                try:
                    priority = Priority(priority_str)
                except ValueError:
                    priority = Priority.MEDIUM

                # Parse duration from LLM output
                duration_days = max(1, int(task_data.get("duration_days", 1)))

                task = Task(
                    task_id=task_id,
                    title=task_data.get("title", "Untitled Task"),
                    description=task_data.get("description", ""),
                    required_skill=task_data.get("required_skill"),
                    duration_days=duration_days,
                    priority=priority,
                )
                tasks.append(task)
                title_to_task_id[task.title.strip().lower()] = task.task_id
                pending_dependencies[task.task_id] = [
                    dep.strip()
                    for dep in task_data.get("dependencies", [])
                    if isinstance(dep, str) and dep.strip()
                ]

            valid_task_ids = {task.task_id for task in tasks}
            for task in tasks:
                resolved_dependencies = []
                for dependency in pending_dependencies.get(task.task_id, []):
                    dependency_key = dependency.lower()
                    if dependency in valid_task_ids:
                        resolved_dependencies.append(dependency)
                    elif dependency_key in title_to_task_id:
                        resolved_dependencies.append(title_to_task_id[dependency_key])
                task.dependencies = resolved_dependencies

            module = Module(
                module_id=module_id,
                module_name=mod_data.get("module_name", f"Module {mod_idx}"),
                tasks=tasks
            )
            modules.append(module)

        estimated_duration = int(llm_result.get("estimated_plan_duration_days", 0))

        return ParsedPlan(
            title=llm_result.get("plan_title", "Untitled Plan"),
            modules=modules,
            estimated_duration_days=estimated_duration,
        )


# Service instance
plan_parser_service = PlanParserService()
