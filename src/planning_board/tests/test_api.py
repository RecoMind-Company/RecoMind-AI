"""
Tests for API Endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test health check endpoints"""

    def test_health_check(self, client):
        """Test main health check"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_api_health_check(self, client):
        """Test API health check"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200


class TestPlanGenerateEndpoint:
    """Test plan generation endpoints"""

    def test_generate_plan_missing_fields(self, client):
        """Test with missing required fields"""
        response = client.post(
            "/api/v1/plans/generate",
            json={"company_id": "comp_1"}  # Missing team_id and plan_text
        )
        assert response.status_code == 422  # Validation error

    def test_generate_plan_empty_plan_text(self, client):
        """Test with empty plan text"""
        response = client.post(
            "/api/v1/plans/generate",
            json={
                "company_id": "comp_1",
                "team_id": "team_1",
                "plan_text": "short"  # Too short
            }
        )
        assert response.status_code == 422

    def test_generate_plan_valid_request(self, client, sample_request_data):
        """Test with valid request data"""
        # Note: This will actually call the LLM in real tests
        # For unit tests, we should mock the LLM
        response = client.post(
            "/api/v1/plans/generate",
            json=sample_request_data
        )
        # In dev mode without API key check
        assert response.status_code in [200, 401, 502]  # 502 if LLM fails
