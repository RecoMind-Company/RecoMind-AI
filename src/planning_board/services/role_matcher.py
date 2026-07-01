"""
Role Matcher Service
====================
Match tasks to employees using LLM
"""

import json
import math
from typing import Dict, List, Optional, Tuple
from loguru import logger

from llm.client import llm_client
from llm.prompts import ROLE_MATCHER_SYSTEM_PROMPT, ROLE_MATCHER_USER_PROMPT
from models.entities import Employee, Task, Module


class RoleMatcherService:
    """Role matching service using LLM"""

    def __init__(self):
        self.llm = llm_client

    async def batch_match_tasks(
        self,
        modules: List[Module],
        employees: List[Employee],
    ) -> Dict[str, Tuple[Optional[Employee], str]]:
        """
        Match all tasks to employees in a single batch using LLM,
        then rebalance if any employee is overloaded.

        Args:
            modules: List of Modules with tasks
            employees: List of available employees

        Returns:
            Dict[task_id, (Employee | None, reason)]
        """
        if not employees:
            all_tasks = [task for module in modules for task in module.tasks]
            return {task.task_id: (None, "No employees in the team") for task in all_tasks}

        all_tasks = [task for module in modules for task in module.tasks]
        if not all_tasks:
            return {}

        tasks_payload = json.dumps(
            [
                {
                    "task_id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "required_skill": task.required_skill or "Not specified",
                }
                for task in all_tasks
            ],
            ensure_ascii=False,
            indent=2,
        )

        employees_payload = json.dumps(
            [
                {
                    "user_id": emp.id,
                    "job_title": emp.job_title,
                }
                for emp in employees
            ],
            ensure_ascii=False,
            indent=2,
        )

        user_prompt = ROLE_MATCHER_USER_PROMPT.format(
            tasks_json=tasks_payload,
            employees_json=employees_payload,
        )

        try:
            logger.info(f"🤖 Sending {len(all_tasks)} tasks + {len(employees)} employees to LLM for matching...")

            result = await self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=ROLE_MATCHER_SYSTEM_PROMPT,
                temperature=0.2,
            )

            assignments = result.get("assignments", [])

            employee_map: Dict[str, Employee] = {emp.id: emp for emp in employees}
            matched: Dict[str, Tuple[Optional[Employee], str]] = {}

            for assignment in assignments:
                task_id = assignment.get("task_id")
                user_id = assignment.get("user_id")
                reason = assignment.get("reason", "")

                if not task_id:
                    continue

                if user_id and user_id in employee_map:
                    matched[task_id] = (employee_map[user_id], reason)
                else:
                    matched[task_id] = (None, reason or "No suitable employee")

            for task in all_tasks:
                if task.task_id not in matched:
                    matched[task.task_id] = (None, "Task not matched")

            assigned_count = sum(1 for emp, _ in matched.values() if emp is not None)
            logger.info(f"✅ LLM matching complete: {assigned_count}/{len(all_tasks)} tasks assigned")

            # Post-processing: rebalance overloaded employees
            matched = self._rebalance_assignments(matched, all_tasks, employees)

            return matched

        except Exception as e:
            logger.error(f"❌ LLM role matching failed: {str(e)}, falling back to keyword matching")
            return self._keyword_fallback(all_tasks, employees)

    def _rebalance_assignments(
        self,
        matched: Dict[str, Tuple[Optional[Employee], str]],
        all_tasks: List[Task],
        employees: List[Employee],
    ) -> Dict[str, Tuple[Optional[Employee], str]]:
        """
        Check if any employee is overloaded relative to the team average.
        If so, reassign their excess tasks to less-loaded employees who are
        also suitable based on keyword matching.

        Threshold: no employee should have more than
        ceil(total_assigned / num_employees) tasks.
        """
        task_map: Dict[str, Task] = {t.task_id: t for t in all_tasks}

        # Count current assignments per employee
        load: Dict[str, int] = {emp.id: 0 for emp in employees}
        tasks_by_employee: Dict[str, List[str]] = {emp.id: [] for emp in employees}

        for task_id, (emp, _) in matched.items():
            if emp is not None:
                load[emp.id] = load.get(emp.id, 0) + 1
                tasks_by_employee.setdefault(emp.id, []).append(task_id)

        total_assigned = sum(load.values())

        if total_assigned == 0:
            return matched

        # Fair share across ALL employees, not just those who got tasks
        fair_share = math.ceil(total_assigned / len(employees))
        max_allowed = fair_share

        # Find overloaded employees (have more than their fair share)
        overloaded = [emp_id for emp_id, count in load.items() if count > max_allowed]

        # Also find employees with 0 tasks — pull work toward them
        zero_load = [emp_id for emp_id, count in load.items() if count == 0]

        if not overloaded and not zero_load:
            logger.info(f"📊 Load balanced — max per employee: {max(load.values())}, fair share: {fair_share}")
            return matched

        logger.info(
            f"⚖️ Rebalancing — overloaded: {len(overloaded)}, "
            f"zero-load: {len(zero_load)}, fair share: {fair_share}, max allowed: {max_allowed}"
        )

        # Phase 1: Move excess from overloaded to zero-load or underloaded employees
        for over_emp_id in overloaded:
            excess = load[over_emp_id] - max_allowed
            task_ids = list(tasks_by_employee[over_emp_id])

            for task_id in task_ids:
                if excess <= 0:
                    break

                task = task_map.get(task_id)
                if not task:
                    continue

                alternatives = self._find_alternative_employees(
                    task,
                    employees,
                    load,
                    exclude={over_emp_id},
                )

                if alternatives:
                    alt_emp = alternatives[0]
                    matched[task_id] = (
                        alt_emp,
                        f"Rebalanced to {alt_emp.job_title} for even distribution "
                        f"(Job Title match for {task.required_skill or 'the task'})",
                    )
                    load[over_emp_id] -= 1
                    load[alt_emp.id] += 1
                    tasks_by_employee[over_emp_id].remove(task_id)
                    tasks_by_employee[alt_emp.id].append(task_id)
                    excess -= 1
                    logger.debug(
                        f"  Moved task '{task.title}' from {over_emp_id} "
                        f"to {alt_emp.id} (now {load[alt_emp.id]} tasks)"
                    )

        # Phase 2: If zero-load employees still exist, pull a task from the most loaded suitable employee
        remaining_zero = [emp_id for emp_id, count in load.items() if count == 0]
        if remaining_zero:
            for zero_emp_id in remaining_zero:
                zero_emp = next(e for e in employees if e.id == zero_emp_id)

                # Find the most loaded employee whose tasks match this zero employee
                best_donor = None
                best_donor_task_id = None

                for donor_id, task_ids in tasks_by_employee.items():
                    if donor_id == zero_emp_id or not task_ids:
                        continue

                    for task_id in task_ids:
                        task = task_map.get(task_id)
                        if not task:
                            continue

                        if self._is_suitable(zero_emp, task):
                            if best_donor is None or load[donor_id] > load[best_donor]:
                                best_donor = donor_id
                                best_donor_task_id = task_id

                if best_donor and best_donor_task_id:
                    task = task_map[best_donor_task_id]
                    matched[best_donor_task_id] = (
                        zero_emp,
                        f"Rebalanced to {zero_emp.job_title} to give them a task "
                        f"(Job Title match for {task.required_skill or 'the task'})",
                    )
                    load[best_donor] -= 1
                    load[zero_emp_id] += 1
                    tasks_by_employee[best_donor].remove(best_donor_task_id)
                    tasks_by_employee[zero_emp_id].append(best_donor_task_id)
                    logger.debug(
                        f"  Pulled task '{task.title}' from {best_donor} "
                        f"to {zero_emp_id} (was 0, now 1)"
                    )

        final_max = max(load.values()) if load else 0
        final_min = min(load.values()) if load else 0
        logger.info(f"✅ Rebalancing complete — min: {final_min}, max: {final_max} tasks per employee")

        return matched

    def _is_suitable(self, employee: Employee, task: Task) -> bool:
        """Check if an employee is suitable for a task based on keyword matching."""
        skill_lower = (task.required_skill or "").lower()
        job_lower = employee.job_title.lower()

        if not skill_lower:
            return True

        if skill_lower in job_lower or job_lower in skill_lower:
            return True

        skill_words = set(skill_lower.split())
        job_words = set(job_lower.split())
        common = skill_words & job_words
        return bool(common)

    def _find_alternative_employees(
        self,
        task: Task,
        employees: List[Employee],
        current_load: Dict[str, int],
        exclude: set[str],
    ) -> List[Employee]:
        """
        Find employees who are suitable for the task based on keyword matching
        and have the lowest current load. Excludes employees in the exclude set.

        Returns employees sorted by load (ascending).
        """
        candidates: List[Tuple[Employee, int]] = []

        for emp in employees:
            if emp.id in exclude:
                continue

            if self._is_suitable(emp, task):
                candidates.append((emp, current_load.get(emp.id, 0)))

        candidates.sort(key=lambda x: x[1])

        return [emp for emp, _ in candidates]

    def _keyword_fallback(
        self,
        tasks: List[Task],
        employees: List[Employee],
    ) -> Dict[str, Tuple[Optional[Employee], str]]:
        """Simple fallback if LLM fails"""
        result = {}
        assignment_counts: Dict[str, int] = {emp.id: 0 for emp in employees}

        for task in tasks:
            if not task.required_skill:
                result[task.task_id] = (None, "Required skill not specified")
                continue

            skill_lower = task.required_skill.lower()
            selected = None

            for emp in employees:
                job_lower = emp.job_title.lower()
                if skill_lower in job_lower or job_lower in skill_lower:
                    if assignment_counts[emp.id] < 3:
                        selected = emp
                        break

                common = set(skill_lower.split()) & set(job_lower.split())
                if common and assignment_counts[emp.id] < 3:
                    selected = emp
                    break

            if selected:
                result[task.task_id] = (selected, f"Job Title: {selected.job_title}")
                assignment_counts[selected.id] += 1
            else:
                result[task.task_id] = (None, f"No employee with skill {task.required_skill}")

        return result


# Service instance
role_matcher_service = RoleMatcherService()
