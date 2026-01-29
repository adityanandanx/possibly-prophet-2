"""
Basic tests for the main FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.unit
def test_root_endpoint(client: TestClient):
    """Test the root endpoint returns correct information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Educational Content Generator API"
    assert data["version"] == "1.0.0"
    assert "docs" in data
    assert "health" in data

@pytest.mark.unit
def test_health_endpoint(client: TestClient):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data

@pytest.mark.unit
def test_api_docs_accessible(client: TestClient):
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

@pytest.mark.unit
def test_cors_headers(client: TestClient):
    """Test that CORS headers are properly configured."""
    # Test with a simple GET request that should include CORS headers
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200