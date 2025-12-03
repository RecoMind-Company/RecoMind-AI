"""
Internal Entity Models
======================
النماذج الداخلية للـ Business Logic
"""

from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(str, Enum):
    """حالات المهمة"""
    TO_DO = "to_do"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class Priority(str, Enum):
    """مستويات الأولوية"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Employee:
    """نموذج الموظف (من .NET API)"""
    
    id: str
    name: str
    job_title: str
    skills: List[str] = field(default_factory=list)
    current_workload: int = 0  # عدد المهام الحالية
    
    def matches_skill(self, required_skill: str) -> bool:
        """التحقق من مطابقة المهارة"""
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
    """نموذج المهمة الداخلي"""
    
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
    
    def to_dict(self) -> dict:
        """تحويل لـ dictionary"""
        result = {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "duration_days": self.duration_days,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "priority": self.priority.value
        }
        
        if self.suggested_owner:
            result["suggested_owner"] = {
                "id": self.suggested_owner.id,
                "name": self.suggested_owner.name,
                "reason": self.assignment_reason or f"Job Title: {self.suggested_owner.job_title}"
            }
        else:
            result["suggested_owner"] = None
            result["reason"] = self.assignment_reason
        
        return result


@dataclass
class Module:
    """نموذج الـ Module الداخلي"""
    
    module_id: str
    module_name: str
    tasks: List[Task] = field(default_factory=list)
    
    @property
    def total_duration(self) -> int:
        """حساب إجمالي المدة"""
        return sum(task.duration_days for task in self.tasks)
    
    def to_dict(self) -> dict:
        """تحويل لـ dictionary"""
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "tasks": [task.to_dict() for task in self.tasks]
        }


@dataclass
class ParsedPlan:
    """الخطة بعد التحليل"""
    
    title: str
    modules: List[Module] = field(default_factory=list)
    
    @property
    def total_tasks(self) -> int:
        """إجمالي عدد المهام"""
        return sum(len(module.tasks) for module in self.modules)
    
    @property
    def total_duration(self) -> int:
        """إجمالي المدة"""
        return sum(module.total_duration for module in self.modules)


@dataclass
class TimelinePhase:
    """مرحلة في الـ Timeline"""
    
    phase: str
    start_day: int
    end_day: int
    
    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "start_day": self.start_day,
            "end_day": self.end_day
        }
