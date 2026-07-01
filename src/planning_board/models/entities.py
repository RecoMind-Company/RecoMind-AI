"""
Internal Entity Models
======================
Internal models for the Business Logic
"""

from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(str, Enum):
    """Task statuses"""
    TO_DO = "to_do"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class Priority(str, Enum):
    """Priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Employee:
    """Employee model (from .NET API)"""

    id: str  # user_id from .NET API
    name: str
    job_title: str
    skills: List[str] = field(default_factory=list)
    current_workload: int = 0  # number of current tasks

    def matches_skill(self, required_skill: str) -> bool:
        """Check if the skill matches"""
        job_title_lower = self.job_title.lower()
        skill_lower = required_skill.lower()

        # Direct match
        if skill_lower in job_title_lower:
            return True

        # Check skills list
        for skill in self.skills:
            if skill_lower in skill.lower():
                return True

        return False


@dataclass
class Task:
    """Internal task model"""

    task_id: str
    title: str
    description: str
    required_skill: Optional[str] = None
    duration_days: int = 1
    suggested_owner: Optional[Employee] = None
    assignment_reason: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.TO_DO
    priority: Priority = Priority.MEDIUM
    start_date: Optional[str] = None  # ISO date string (YYYY-MM-DD)
    deadline_date: Optional[str] = None  # ISO date string (YYYY-MM-DD)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        result = {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "duration_days": self.duration_days,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "priority": self.priority.value,
            "start_date": self.start_date,
            "deadline_date": self.deadline_date,
        }

        if self.suggested_owner:
            result["suggested_owner"] = {
                "user_id": self.suggested_owner.id,
                "job_title": self.suggested_owner.job_title,
                "reason": self.assignment_reason or f"Job Title: {self.suggested_owner.job_title}"
            }
        else:
            result["suggested_owner"] = None
            result["reason"] = self.assignment_reason

        return result


@dataclass
class Module:
    """Internal Module model"""

    module_id: str
    module_name: str
    tasks: List[Task] = field(default_factory=list)

    @property
    def total_duration(self) -> int:
        """Calculate total duration"""
        return sum(task.duration_days for task in self.tasks)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "tasks": [task.to_dict() for task in self.tasks]
        }


@dataclass
class ParsedPlan:
    """Parsed plan"""

    title: str
    modules: List[Module] = field(default_factory=list)
    estimated_duration_days: int = 0

    @property
    def total_tasks(self) -> int:
        """Total number of tasks"""
        return sum(len(module.tasks) for module in self.modules)

    @property
    def total_duration(self) -> int:
        """Total duration"""
        return sum(module.total_duration for module in self.modules)


@dataclass
class TimelinePhase:
    """A phase in the timeline"""

    phase: str
    start_day: int
    end_day: int
    start_date: Optional[str] = None  # ISO date string (YYYY-MM-DD)
    end_date: Optional[str] = None  # ISO date string (YYYY-MM-DD)

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "start_day": self.start_day,
            "end_day": self.end_day,
            "start_date": self.start_date,
            "end_date": self.end_date,
        }
