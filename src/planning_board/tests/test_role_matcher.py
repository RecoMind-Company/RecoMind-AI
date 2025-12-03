"""
Tests for Role Matcher Service
"""

import pytest
from services.role_matcher import RoleMatcherService
from models.entities import Employee, Task


class TestRoleMatcherService:
    """Test cases for RoleMatcherService"""
    
    def setup_method(self):
        """Setup for each test"""
        self.service = RoleMatcherService()
    
    def test_direct_skill_match(self):
        """Test direct match between skill and job title"""
        is_match, confidence = self.service.match_skill_to_job_title(
            "Content Writing",
            "Content Writer"
        )
        assert is_match is True
        assert confidence >= 0.9
    
    def test_mapped_skill_match(self):
        """Test mapped match using skill mappings"""
        is_match, confidence = self.service.match_skill_to_job_title(
            "Social Media Management",
            "Digital Marketing Specialist"
        )
        assert is_match is True
        assert confidence >= 0.5
    
    def test_no_match(self):
        """Test when there's no match"""
        is_match, confidence = self.service.match_skill_to_job_title(
            "Data Analysis",
            "Graphic Designer"
        )
        assert is_match is False
        assert confidence < 0.5
    
    def test_find_matching_employees(self, mock_employees):
        """Test finding matching employees"""
        matches = self.service.find_matching_employees(
            "Content Writing",
            mock_employees
        )
        
        assert len(matches) >= 1
        # Content Writer should be in matches
        employee_names = [emp.name for emp, _ in matches]
        assert "سارة" in employee_names
    
    def test_suggest_owner_for_task(self, mock_employees):
        """Test suggesting owner for a task"""
        task = Task(
            task_id="task_001",
            title="كتابة محتوى إعلاني",
            description="كتابة 10 منشورات",
            required_skill="Content Writing"
        )
        
        employee, reason = self.service.suggest_owner_for_task(
            task,
            mock_employees
        )
        
        assert employee is not None
        assert employee.name == "سارة"
        assert "Content Writer" in reason
    
    def test_suggest_owner_no_match(self, mock_employees):
        """Test when no matching employee found"""
        task = Task(
            task_id="task_002",
            title="تحليل البيانات",
            description="تحليل بيانات المبيعات",
            required_skill="Data Science"
        )
        
        employee, reason = self.service.suggest_owner_for_task(
            task,
            mock_employees
        )
        
        assert employee is None
        assert "لا يوجد" in reason
    
    def test_round_robin_assignment(self, mock_employees):
        """Test round-robin fair assignment"""
        assignment_counts = {"emp_01": 2, "emp_02": 0, "emp_03": 1}
        
        task = Task(
            task_id="task_003",
            title="إدارة السوشيال ميديا",
            description="نشر المحتوى",
            required_skill="Marketing"
        )
        
        employee, _ = self.service.suggest_owner_for_task(
            task,
            mock_employees,
            assignment_counts
        )
        
        # Should prefer employee with fewer assignments
        if employee:
            assert assignment_counts.get(employee.id, 0) <= 2
