"""
Assignment Engine Service
=========================
توزيع المهام على الموظفين بشكل عادل
"""

from typing import Dict, List, Optional
from loguru import logger

from models.entities import Employee, Task, Module
from services.role_matcher import role_matcher_service


class AssignmentEngineService:
    """خدمة توزيع المهام"""
    
    def __init__(self):
        self.role_matcher = role_matcher_service
    
    def assign_tasks_to_employees(
        self,
        modules: List[Module],
        employees: List[Employee]
    ) -> List[Module]:
        """
        توزيع المهام على الموظفين
        
        Args:
            modules: قائمة الـ Modules مع المهام
            employees: قائمة الموظفين المتاحين
            
        Returns:
            Modules مع المهام الموزعة
        """
        logger.info(f"🎯 Assigning tasks to {len(employees)} employees")
        
        # Track assignment counts for Round-Robin
        assignment_counts: Dict[str, int] = {emp.id: 0 for emp in employees}
        
        total_assigned = 0
        total_unassigned = 0
        
        for module in modules:
            for task in module.tasks:
                employee, reason = self.role_matcher.suggest_owner_for_task(
                    task=task,
                    employees=employees,
                    assignment_counts=assignment_counts
                )
                
                if employee:
                    task.suggested_owner = employee
                    task.assignment_reason = reason
                    assignment_counts[employee.id] += 1
                    total_assigned += 1
                    logger.debug(f"✅ Task '{task.title}' → {employee.name}")
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
        ملخص التوزيع
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
                "task_count": 0,
                "tasks": []
            }
        
        summary["by_employee"]["unassigned"] = {
            "name": "غير مُسند",
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
