"""
Tests for Time Estimator Service
"""

import pytest
from services.time_estimator import TimeEstimatorService
from models.entities import Task


class TestTimeEstimatorService:
    """Test cases for TimeEstimatorService"""

    def setup_method(self):
        """Setup for each test"""
        self.service = TimeEstimatorService()

    def test_estimate_content_writing(self):
        """Test estimation for content writing task"""
        task = Task(
            task_id="task_001",
            title="Write Content",
            description="Write articles",
            required_skill="Content Writing"
        )

        duration = self.service.estimate_task_duration(task, "medium")
        assert 3 <= duration <= 7

    def test_estimate_design(self):
        """Test estimation for design task"""
        task = Task(
            task_id="task_002",
            title="Design Images",
            description="Design advertising images",
            required_skill="Graphic Design"
        )

        duration = self.service.estimate_task_duration(task, "medium")
        assert 2 <= duration <= 6

    def test_estimate_low_complexity(self):
        """Test estimation with low complexity"""
        task = Task(
            task_id="task_003",
            title="Review",
            description="Review content",
            required_skill="Review"
        )

        duration_low = self.service.estimate_task_duration(task, "low")
        duration_high = self.service.estimate_task_duration(task, "high")

        assert duration_low < duration_high

    def test_estimate_unknown_skill(self):
        """Test estimation for unknown skill (uses default)"""
        task = Task(
            task_id="task_004",
            title="Unknown Task",
            description="Description",
            required_skill="Unknown Skill XYZ"
        )

        duration = self.service.estimate_task_duration(task, "medium")
        assert duration == 4  # Default medium

    def test_estimate_multiple_tasks(self, mock_employees):
        """Test estimating multiple tasks"""
        tasks = [
            Task(task_id="t1", title="Writing", description="", required_skill="Content Writing"),
            Task(task_id="t2", title="Design", description="", required_skill="Design"),
            Task(task_id="t3", title="Publishing", description="", required_skill="Social Media"),
        ]

        durations = self.service.estimate_tasks_duration(tasks)

        assert len(durations) == 3
        assert all(d > 0 for d in durations.values())

    def test_total_duration(self):
        """Test calculating total duration"""
        tasks = [
            Task(task_id="t1", title="t1", description="", duration_days=5),
            Task(task_id="t2", title="t2", description="", duration_days=3),
            Task(task_id="t3", title="t3", description="", duration_days=7),
        ]

        total = self.service.calculate_total_duration(tasks)
        assert total == 15
