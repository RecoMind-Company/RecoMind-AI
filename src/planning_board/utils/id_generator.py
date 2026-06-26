"""
ID Generator Utilities
======================
Generate unique identifiers
"""

import uuid
from datetime import datetime


def generate_plan_id() -> str:
    """Generate a unique plan ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    short_uuid = uuid.uuid4().hex[:6]
    return f"plan_{timestamp}_{short_uuid}"


def generate_module_id(index: int) -> str:
    """Generate a Module ID"""
    return f"mod_{index}"


def generate_task_id(index: int) -> str:
    """Generate a task ID"""
    return f"task_{index}"


def generate_uuid() -> str:
    """Generate a short UUID"""
    return uuid.uuid4().hex[:12]
