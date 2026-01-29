"""
Tests for error handling and logging functionality
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.unit
def test_validation_error_handling(client: TestClient):
    """Test that validation errors are properly handled."""
    # Send invalid JSON to trigger validation error
    response = client.post(
        "/api/v1/content/generate",
        json={"invalid": "data"}
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "validation_error"
    assert data["error"]["code"] == 422

@pytest.mark.unit
def test_404_error_handling(client: TestClient):
    """Test that 404 errors are properly handled."""
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Not Found"

@pytest.mark.unit
def test_method_not_allowed_handling(client: TestClient):
    """Test that method not allowed errors are properly handled."""
    response = client.post("/")  # Root only accepts GET
    assert response.status_code == 405
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Method Not Allowed"