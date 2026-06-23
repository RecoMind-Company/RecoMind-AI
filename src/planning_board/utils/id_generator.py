"""
ID Generator Utilities
======================
توليد معرفات فريدة
"""

import uuid
from datetime import datetime


def generate_plan_id() -> str:
    """توليد معرف فريد للخطة"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    short_uuid = uuid.uuid4().hex[:6]
    return f"plan_{timestamp}_{short_uuid}"


def generate_module_id(index: int) -> str:
    """توليد معرف للـ Module"""
    return f"mod_{index}"


def generate_task_id(index: int) -> str:
    """توليد معرف للمهمة"""
    return f"task_{index}"


def generate_uuid() -> str:
    """توليد UUID قصير"""
    return uuid.uuid4().hex[:12]
