"""
Pytest fixtures for validation tests
"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def validation_request():
    """Sample validation request payload"""
    return {
        "company_id": "34293b50-0c58-4111-8fcd-b0127dd250ce",
        "team_id": "0dc1400d-a758-424b-80fb-a8ff89078522",
        "user_request": "We want to open a new physical branch in Cairo for our retail business and hire a sales team.",
    }
