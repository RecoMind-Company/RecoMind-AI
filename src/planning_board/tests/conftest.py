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
        Employee(id="usr_01", name="Ahmed", job_title="Marketing Specialist"),
        Employee(id="usr_02", name="Sara", job_title="Content Writer"),
        Employee(id="usr_03", name="Mohamed", job_title="Social Media Manager"),
        Employee(id="usr_04", name="Rana", job_title="Graphic Designer"),
    ]


@pytest.fixture
def sample_plan_text() -> str:
    """Sample plan text for testing"""
    return """
    Launch an advertising campaign on social media and measure results over two months.

    Phases:
    1. Content preparation: Write posts and design images
    2. Execution: Publish content on Facebook and Instagram
    3. Monitoring: Measure results and prepare a final report
    """


@pytest.fixture
def sample_request_data(sample_plan_text) -> dict:
    """Sample request data for testing"""
    return {
        "company_id": "comp_test",
        "team_id": "team_test",
        "plan_text": sample_plan_text,
    }
