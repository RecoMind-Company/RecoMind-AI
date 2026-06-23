"""
Tests Configuration
===================
Pytest fixtures and configuration
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient

from main import app
from models.entities import Employee


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator:
    """Sync test client"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_employees() -> list[Employee]:
    """Mock employee data for testing"""
    return [
        Employee(id="emp_01", name="أحمد", job_title="Marketing Specialist"),
        Employee(id="emp_02", name="سارة", job_title="Content Writer"),
        Employee(id="emp_03", name="محمد", job_title="Social Media Manager"),
        Employee(id="emp_04", name="رنا", job_title="Graphic Designer"),
    ]


@pytest.fixture
def sample_plan_text() -> str:
    """Sample plan text for testing"""
    return """
    إطلاق حملة إعلانية على مواقع التواصل الاجتماعي وقياس النتائج خلال شهرين.
    
    المراحل:
    1. إعداد المحتوى: كتابة المنشورات وتصميم الصور
    2. التنفيذ: نشر المحتوى على فيسبوك وإنستجرام
    3. المتابعة: قياس النتائج وإعداد تقرير نهائي
    """


@pytest.fixture
def sample_request_data(sample_plan_text) -> dict:
    """Sample request data for testing"""
    return {
        "company_id": "comp_test",
        "team_name": "Marketing",
        "plan_text": sample_plan_text,
        "priority": "high"
    }
