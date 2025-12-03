"""
Time Estimator Service
======================
تقدير المدة الزمنية لكل مهمة
"""

from typing import Dict, List
from loguru import logger

from models.entities import Task


# Duration estimates by skill/task type (in days)
DURATION_ESTIMATES: Dict[str, Dict[str, int]] = {
    "content writing": {"low": 3, "medium": 5, "high": 7},
    "content creation": {"low": 3, "medium": 5, "high": 7},
    "copywriting": {"low": 2, "medium": 4, "high": 6},
    
    "graphic design": {"low": 2, "medium": 4, "high": 6},
    "design": {"low": 2, "medium": 4, "high": 6},
    "ui design": {"low": 3, "medium": 5, "high": 8},
    
    "social media management": {"low": 2, "medium": 5, "high": 10},
    "social media": {"low": 2, "medium": 5, "high": 10},
    "community management": {"low": 3, "medium": 7, "high": 14},
    
    "video production": {"low": 3, "medium": 5, "high": 10},
    "video editing": {"low": 2, "medium": 4, "high": 7},
    
    "data analysis": {"low": 3, "medium": 5, "high": 10},
    "analytics": {"low": 2, "medium": 4, "high": 7},
    "reporting": {"low": 2, "medium": 4, "high": 6},
    
    "marketing": {"low": 3, "medium": 7, "high": 14},
    "campaign management": {"low": 5, "medium": 14, "high": 30},
    
    "project management": {"low": 2, "medium": 5, "high": 10},
    "planning": {"low": 2, "medium": 4, "high": 7},
    
    "research": {"low": 3, "medium": 5, "high": 10},
    "strategy": {"low": 3, "medium": 7, "high": 14},
    
    "review": {"low": 1, "medium": 2, "high": 3},
    "approval": {"low": 1, "medium": 2, "high": 3},
    
    "default": {"low": 2, "medium": 4, "high": 7}
}


class TimeEstimatorService:
    """خدمة تقدير المدة الزمنية"""
    
    def __init__(self):
        self.estimates = DURATION_ESTIMATES
    
    def estimate_task_duration(
        self,
        task: Task,
        complexity: str = "medium"
    ) -> int:
        """
        تقدير مدة مهمة واحدة
        
        Args:
            task: المهمة
            complexity: مستوى التعقيد (low, medium, high)
            
        Returns:
            المدة بالأيام
        """
        complexity = complexity.lower()
        if complexity not in ["low", "medium", "high"]:
            complexity = "medium"
        
        # Try to match skill
        if task.required_skill:
            skill_lower = task.required_skill.lower()
            
            for skill_key, durations in self.estimates.items():
                if skill_key in skill_lower or skill_lower in skill_key:
                    return durations[complexity]
        
        # Try to match from task title
        title_lower = task.title.lower()
        for skill_key, durations in self.estimates.items():
            if skill_key in title_lower:
                return durations[complexity]
        
        # Default estimate
        return self.estimates["default"][complexity]
    
    def estimate_tasks_duration(
        self,
        tasks: List[Task],
        complexity_map: Dict[str, str] = None
    ) -> Dict[str, int]:
        """
        تقدير مدة مجموعة من المهام
        
        Args:
            tasks: قائمة المهام
            complexity_map: خريطة التعقيد لكل مهمة (task_id -> complexity)
            
        Returns:
            Dict[task_id, duration_days]
        """
        if complexity_map is None:
            complexity_map = {}
        
        result = {}
        
        for task in tasks:
            complexity = complexity_map.get(task.task_id, "medium")
            duration = self.estimate_task_duration(task, complexity)
            result[task.task_id] = duration
            task.duration_days = duration  # Update task object
        
        return result
    
    def calculate_total_duration(self, tasks: List[Task]) -> int:
        """
        حساب إجمالي المدة مع مراعاة التبعيات
        
        Note: هذه نسخة مبسطة - في الواقع نحتاج لحساب Critical Path
        """
        if not tasks:
            return 0
        
        # Simple sum for now (can be enhanced with dependency analysis)
        return sum(task.duration_days for task in tasks)
    
    def _detect_complexity_from_description(self, description: str) -> str:
        """
        استنتاج مستوى التعقيد من الوصف
        """
        desc_lower = description.lower()
        
        high_indicators = ["معقد", "شامل", "كبير", "متعدد", "comprehensive", "complex", "large"]
        low_indicators = ["بسيط", "سريع", "صغير", "simple", "quick", "small", "basic"]
        
        for indicator in high_indicators:
            if indicator in desc_lower:
                return "high"
        
        for indicator in low_indicators:
            if indicator in desc_lower:
                return "low"
        
        return "medium"


# Service instance
time_estimator_service = TimeEstimatorService()
