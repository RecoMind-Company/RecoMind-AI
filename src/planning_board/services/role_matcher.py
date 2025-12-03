"""
Role Matcher Service
====================
مطابقة المهارات المطلوبة مع الـ Job Titles
"""

from typing import Dict, List, Optional, Tuple
from loguru import logger

from models.entities import Employee, Task


# Skill to Job Title mapping
SKILL_MAPPINGS: Dict[str, List[str]] = {
    "content writing": [
        "content writer", "copywriter", "محرر محتوى", "كاتب محتوى",
        "content specialist", "content creator", "blog writer"
    ],
    "graphic design": [
        "graphic designer", "ui designer", "visual designer", 
        "مصمم جرافيك", "مصمم", "art director", "creative designer"
    ],
    "social media management": [
        "social media manager", "social media specialist",
        "digital marketing specialist", "مدير سوشيال ميديا",
        "community manager", "social media coordinator"
    ],
    "marketing": [
        "marketing specialist", "marketing manager", 
        "digital marketer", "أخصائي تسويق", "مدير تسويق",
        "growth marketer", "marketing coordinator"
    ],
    "data analysis": [
        "data analyst", "business analyst", "محلل بيانات",
        "analytics specialist", "bi analyst", "data scientist"
    ],
    "project management": [
        "project manager", "scrum master", "مدير مشروع",
        "program manager", "pmo", "delivery manager"
    ],
    "video production": [
        "video editor", "videographer", "محرر فيديو",
        "motion designer", "video producer", "filmmaker"
    ],
    "seo": [
        "seo specialist", "seo manager", "متخصص سيو",
        "search specialist", "organic marketing"
    ],
    "customer service": [
        "customer service", "support specialist", "خدمة عملاء",
        "customer success", "account manager"
    ],
    "sales": [
        "sales representative", "sales manager", "مبيعات",
        "business development", "account executive"
    ]
}


class RoleMatcherService:
    """خدمة مطابقة الأدوار"""
    
    def __init__(self):
        self.skill_mappings = SKILL_MAPPINGS
    
    def match_skill_to_job_title(
        self, 
        required_skill: str, 
        job_title: str
    ) -> Tuple[bool, float]:
        """
        التحقق من مطابقة المهارة مع المسمى الوظيفي
        
        Returns:
            Tuple[bool, float]: (is_match, confidence_score)
        """
        if not required_skill or not job_title:
            return False, 0.0
        
        skill_lower = required_skill.lower().strip()
        job_lower = job_title.lower().strip()
        
        # Direct match
        if skill_lower in job_lower or job_lower in skill_lower:
            return True, 1.0
        
        # Check mappings
        for skill_key, job_titles in self.skill_mappings.items():
            if skill_key in skill_lower or skill_lower in skill_key:
                for mapped_title in job_titles:
                    if mapped_title in job_lower:
                        return True, 0.9
        
        # Partial match
        skill_words = set(skill_lower.split())
        job_words = set(job_lower.split())
        common_words = skill_words & job_words
        
        if common_words:
            confidence = len(common_words) / max(len(skill_words), len(job_words))
            if confidence > 0.3:
                return True, confidence
        
        return False, 0.0
    
    def find_matching_employees(
        self,
        required_skill: str,
        employees: List[Employee],
        min_confidence: float = 0.5
    ) -> List[Tuple[Employee, float]]:
        """
        إيجاد الموظفين المناسبين للمهارة المطلوبة
        
        Returns:
            List of (Employee, confidence_score) sorted by confidence
        """
        matches = []
        
        for employee in employees:
            is_match, confidence = self.match_skill_to_job_title(
                required_skill,
                employee.job_title
            )
            
            if is_match and confidence >= min_confidence:
                matches.append((employee, confidence))
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def suggest_owner_for_task(
        self,
        task: Task,
        employees: List[Employee],
        assignment_counts: Dict[str, int] = None
    ) -> Tuple[Optional[Employee], str]:
        """
        اقتراح موظف للمهمة مع مراعاة التوزيع العادل
        
        Args:
            task: المهمة
            employees: قائمة الموظفين
            assignment_counts: عدد المهام المسندة لكل موظف (للتوزيع العادل)
            
        Returns:
            Tuple[Optional[Employee], str]: (الموظف المقترح, سبب الاختيار)
        """
        if not task.required_skill:
            return None, "لم يتم تحديد المهارة المطلوبة"
        
        if not employees:
            return None, "لا يوجد موظفين في الفريق"
        
        if assignment_counts is None:
            assignment_counts = {}
        
        # Find matching employees
        matches = self.find_matching_employees(
            task.required_skill,
            employees
        )
        
        if not matches:
            return None, f"لا يوجد موظف بمهارة {task.required_skill} في الفريق"
        
        # Apply Round-Robin: choose employee with least assignments
        min_assignments = float('inf')
        selected_employee = None
        selected_confidence = 0.0
        
        for employee, confidence in matches:
            emp_assignments = assignment_counts.get(employee.id, 0)
            if emp_assignments < min_assignments:
                min_assignments = emp_assignments
                selected_employee = employee
                selected_confidence = confidence
            elif emp_assignments == min_assignments and confidence > selected_confidence:
                selected_employee = employee
                selected_confidence = confidence
        
        reason = f"Job Title: {selected_employee.job_title}"
        if selected_confidence < 1.0:
            reason += f" (Match: {selected_confidence:.0%})"
        
        return selected_employee, reason


# Service instance
role_matcher_service = RoleMatcherService()
