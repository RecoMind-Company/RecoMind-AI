"""
Tests for Role Matcher Service
"""

import pytest
from services.role_matcher import RoleMatcherService
from models.entities import Employee, Task, Module


class TestRoleMatcherService:
    """Test cases for RoleMatcherService"""

    def setup_method(self):
        """Setup for each test"""
        self.service = RoleMatcherService()

    def test_keyword_fallback_direct_match(self):
        """Test keyword fallback with direct skill match"""
        task = Task(
            task_id="task_001",
            title="Write Advertising Content",
            description="Write posts",
            required_skill="Sales",
        )
        employees = [
            Employee(id="usr_01", name="Ahmed", job_title="Sales Manager"),
        ]
        result = self.service._keyword_fallback([task], employees)
        assert result["task_001"][0] is not None
        assert result["task_001"][0].job_title == "Sales Manager"

    def test_keyword_fallback_no_match(self):
        """Test keyword fallback when no match exists"""
        task = Task(
            task_id="task_002",
            title="Software Development",
            description="Write code",
            required_skill="Quantum Computing",
        )
        employees = [
            Employee(id="usr_01", name="Ahmed", job_title="Sales Manager"),
        ]
        result = self.service._keyword_fallback([task], employees)
        assert result["task_002"][0] is None

    def test_keyword_fallback_no_skill(self):
        """Test keyword fallback when task has no required_skill"""
        task = Task(
            task_id="task_003",
            title="General Task",
            description="Description",
            required_skill=None,
        )
        employees = [
            Employee(id="usr_01", name="Ahmed", job_title="Sales Manager"),
        ]
        result = self.service._keyword_fallback([task], employees)
        assert result["task_003"][0] is None
        assert "Skill" in result["task_003"][1]

    def test_keyword_fallback_empty_employees(self):
        """Test keyword fallback with no employees"""
        task = Task(
            task_id="task_004",
            title="Task",
            description="Description",
            required_skill="Sales",
        )
        result = self.service._keyword_fallback([task], [])
        assert result["task_004"][0] is None
