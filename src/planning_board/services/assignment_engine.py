"""
Assignment Engine Service
=========================
Assign tasks to employees using LLM-based matching
"""

from typing import Dict, List, Optional
from loguru import logger

from models.entities import Employee, Task, Module
from services.role_matcher import role_matcher_service


class AssignmentEngineService:
    """Task assignment service"""

    def __init__(self):
        self.role_matcher = role_matcher_service

    async def assign_tasks_to_employees(
        self,
        modules: List[Module],
        employees: List[Employee]
    ) -> List[Module]:
        """
        Assign tasks to employees using LLM

        Args:
            modules: List of Modules with tasks
            employees: List of available employees

        Returns:
            Modules with assigned tasks
        """
        logger.info(f"🎯 Assigning tasks to {len(employees)} employees using LLM")

        matches = await self.role_matcher.batch_match_tasks(modules, employees)

        total_assigned = 0
        total_unassigned = 0

        for module in modules:
            for task in module.tasks:
                employee, reason = matches.get(task.task_id, (None, "Task not matched"))

                if employee:
                    task.suggested_owner = employee
                    task.assignment_reason = reason
                    total_assigned += 1
                    logger.debug(f"✅ Task '{task.title}' → {employee.name} ({employee.job_title})")
                else:
                    task.suggested_owner = None
                    task.assignment_reason = reason
                    total_unassigned += 1
                    logger.debug(f"⚠️ Task '{task.title}' → Unassigned ({reason})")

        logger.info(f"📊 Assignment complete: {total_assigned} assigned, {total_unassigned} unassigned")

        return modules

    def get_assignment_summary(
        self,
        modules: List[Module],
        employees: List[Employee]
    ) -> Dict:
        """
        Assignment summary
        """
        summary = {
            "total_tasks": 0,
            "assigned_tasks": 0,
            "unassigned_tasks": 0,
            "by_employee": {}
        }

        # Initialize employee counts
        for emp in employees:
            summary["by_employee"][emp.id] = {
                "name": emp.name,
                "job_title": emp.job_title,
                "task_count": 0,
                "tasks": []
            }

        summary["by_employee"]["unassigned"] = {
            "name": "Unassigned",
            "task_count": 0,
            "tasks": []
        }

        # Count assignments
        for module in modules:
            for task in module.tasks:
                summary["total_tasks"] += 1

                if task.suggested_owner:
                    summary["assigned_tasks"] += 1
                    emp_id = task.suggested_owner.id
                    if emp_id in summary["by_employee"]:
                        summary["by_employee"][emp_id]["task_count"] += 1
                        summary["by_employee"][emp_id]["tasks"].append(task.title)
                else:
                    summary["unassigned_tasks"] += 1
                    summary["by_employee"]["unassigned"]["task_count"] += 1
                    summary["by_employee"]["unassigned"]["tasks"].append(task.title)

        return summary


# Service instance
assignment_engine_service = AssignmentEngineService()
