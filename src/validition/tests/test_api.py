"""
API endpoint tests for the Validation feature
"""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test the root health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "validation"


def test_api_health_check(client: TestClient):
    """Test the API-level health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "validation"


def test_validation_request_validation(client: TestClient):
    """Test that the validation endpoint rejects invalid requests"""
    response = client.post(
        "/api/v1/validate",
        json={"company_id": "", "team_id": "", "user_request": "short"},
    )
    assert response.status_code == 422


def test_validation_request_missing_fields(client: TestClient):
    """Test that the validation endpoint requires all fields"""
    response = client.post(
        "/api/v1/validate",
        json={"company_id": "test-id"},
    )
    assert response.status_code == 422
