"""
Timeline Generator Service
==========================
Build the timeline for the plan
"""

from typing import List, Dict
from loguru import logger

from models.entities import Module, Task, TimelinePhase


class TimelineGeneratorService:
    """Timeline generation service"""

    def generate_timeline(
        self,
        modules: List[Module],
        start_day: int = 1
    ) -> List[TimelinePhase]:
        """
        Generate the timeline based on Modules

        Args:
            modules: List of Modules
            start_day: Start day

        Returns:
            List of timeline phases
        """
        logger.info("📅 Generating timeline...")

        timeline: List[TimelinePhase] = []
        current_day = start_day

        for module in modules:
            if not module.tasks:
                continue

            # Calculate module duration
            module_duration = sum(task.duration_days for task in module.tasks)

            # Handle dependencies (simplified - sequential within module)
            # In real scenario, we'd do proper dependency analysis

            end_day = current_day + module_duration - 1

            phase = TimelinePhase(
                phase=module.module_name,
                start_day=current_day,
                end_day=end_day
            )
            timeline.append(phase)

            # Next module starts after this one
            # Note: This is simplified. Real implementation would consider:
            # - Parallel modules
            # - Cross-module dependencies
            current_day = end_day + 1

        logger.info(f"✅ Timeline generated: {len(timeline)} phases")

        return timeline

    def calculate_total_days(self, timeline: List[TimelinePhase]) -> int:
        """
        Calculate total number of days
        """
        if not timeline:
            return 0

        return max(phase.end_day for phase in timeline)

    def generate_gantt_data(
        self,
        modules: List[Module],
        timeline: List[TimelinePhase]
    ) -> Dict:
        """
        Generate Gantt Chart data
        """
        gantt_data = {
            "phases": [],
            "tasks": []
        }

        # Add phases
        for phase in timeline:
            gantt_data["phases"].append({
                "name": phase.phase,
                "start": phase.start_day,
                "end": phase.end_day,
                "duration": phase.end_day - phase.start_day + 1
            })

        # Add tasks with their positions
        current_day = 1
        for module in modules:
            for task in module.tasks:
                gantt_data["tasks"].append({
                    "id": task.task_id,
                    "title": task.title,
                    "module": module.module_name,
                    "start": current_day,
                    "duration": task.duration_days,
                    "end": current_day + task.duration_days - 1,
                    "assignee": task.suggested_owner.name if task.suggested_owner else None,
                    "dependencies": task.dependencies
                })
                current_day += task.duration_days

        return gantt_data


# Service instance
timeline_generator_service = TimelineGeneratorService()
