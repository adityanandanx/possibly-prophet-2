"""
Tests for input storage API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime

from app.main import app
from app.models.content import ContentType


class TestInputStorageEndpoints:
    """Test cases for input storage API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_stored_input_data(self):
        """Sample stored input data for testing"""
        return {
            "storage_id": "test-storage-123",
            "content": "This is sample educational content about photosynthesis.",
            "metadata": {
                "storage_id": "test-storage-123",
                "content_type": "text",
                "content_hash": "abc123hash",
                "stored_at": "2024-01-01T12:00:00",
                "generation_id": "gen-123",
                "content_length": 58,
                "validation_result": {"is_valid": True},
                "processing_metadata": {"status": "completed"}
            },
            "similarity_score": 0.95,
            "search_snippet": "This is sample educational content..."
        }
    
    @pytest.fixture
    def sample_input_list_data(self):
        """Sample input list data for testing"""
        return [
            {
                "storage_id": "test-storage-1",
                "content_type": "text",
                "content_hash": "hash1",
                "stored_at": "2024-01-01T12:00:00",
                "generation_id": "gen-1",
                "content_length": 100,
                "validation_status": True,
                "processing_status": "completed"
            },
            {
                "storage_id": "test-storage-2",
                "content_type": "file",
                "content_hash": "hash2",
                "stored_at": "2024-01-01T13:00:00",
                "generation_id": "gen-2",
                "content_length": 200,
                "validation_status": True,
                "processing_status": "completed"
            }
        ]
    
    def test_search_stored_inputs_get(self, client, sample_stored_input_data):
        """Test GET /input-storage/search endpoint"""
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.search_inputs = AsyncMock(return_value=[sample_stored_input_data])
            
            response = client.get(
                "/api/v1/input-storage/search",
                params={
                    "query": "photosynthesis",
                    "content_type": "text",
                    "limit": 10
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["storage_id"] == "test-storage-123"
        assert data[0]["content"] == sample_stored_input_data["content"]
        assert data[0]["metadata"]["content_type"] == "text"
        assert data[0]["similarity_score"] == 0.95
        
        # Verify service was called with correct parameters
        mock_service.search_inputs.assert_called_once_with(
            query="photosynthesis",
            content_type=ContentType.TEXT,
            generation_id=None,
            limit=10
        )
    
    def test_search_stored_inputs_post(self, client, sample_stored_input_data):
        """Test POST /input-storage/search endpoint"""
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.search_inputs = AsyncMock(return_value=[sample_stored_input_data])
            
            response = client.post(
                "/api/v1/input-storage/search",
                json={
                    "query": "photosynthesis",
                    "content_type": "text",
                    "generation_id": "gen-123",
                    "limit": 5
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["storage_id"] == "test-storage-123"
        
        # Verify service was called with correct parameters
        mock_service.search_inputs.assert_called_once_with(
            query="photosynthesis",
            content_type=ContentType.TEXT,
            generation_id="gen-123",
            limit=5
        )
    
    def test_list_stored_inputs_get(self, client, sample_input_list_data):
        """Test GET /input-storage/list endpoint"""
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.list_inputs = AsyncMock(return_value=sample_input_list_data)
            
            response = client.get(
                "/api/v1/input-storage/list",
                params={
                    "content_type": "text",
                    "limit": 50,
                    "offset": 0
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["storage_id"] == "test-storage-1"
        assert data[1]["storage_id"] == "test-storage-2"
        
        # Verify service was called with correct parameters
        mock_service.list_inputs.assert_called_once_with(
            content_type=ContentType.TEXT,
            generation_id=None,
            limit=50,
            offset=0
        )
    
    def test_list_stored_inputs_post(self, client, sample_input_list_data):
        """Test POST /input-storage/list endpoint"""
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.list_inputs = AsyncMock(return_value=sample_input_list_data)
            
            response = client.post(
                "/api/v1/input-storage/list",
                json={
                    "content_type": "file",
                    "generation_id": "gen-2",
                    "limit": 25,
                    "offset": 10
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Verify service was called with correct parameters
        mock_service.list_inputs.assert_called_once_with(
            content_type=ContentType.FILE,
            generation_id="gen-2",
            limit=25,
            offset=10
        )
    
    def test_get_stored_input(self, client, sample_stored_input_data):
        """Test GET /input-storage/{storage_id} endpoint"""
        storage_id = "test-storage-123"
        
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.retrieve_input = AsyncMock(return_value=sample_stored_input_data)
            
            response = client.get(f"/api/v1/input-storage/{storage_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["storage_id"] == storage_id
        assert data["content"] == sample_stored_input_data["content"]
        assert data["metadata"]["content_type"] == "text"
        
        # Verify service was called with correct parameters
        mock_service.retrieve_input.assert_called_once_with(storage_id)
    
    def test_get_stored_input_not_found(self, client):
        """Test GET /input-storage/{storage_id} endpoint when input not found"""
        storage_id = "nonexistent-storage-id"
        
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.retrieve_input = AsyncMock(return_value=None)
            
            response = client.get(f"/api/v1/input-storage/{storage_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_get_input_history(self, client):
        """Test GET /input-storage/{storage_id}/history endpoint"""
        storage_id = "test-storage-123"
        
        # Mock stored input data
        stored_input_data = {
            "content": "test content",
            "metadata": {"content_hash": "test-hash-123"}
        }
        
        # Mock history data
        history_data = [
            {
                "storage_id": "test-storage-123",
                "stored_at": "2024-01-01T12:00:00",
                "generation_id": "gen-1",
                "validation_result": {"is_valid": True},
                "processing_metadata": {"status": "completed"}
            },
            {
                "storage_id": "test-storage-456",
                "stored_at": "2024-01-01T13:00:00",
                "generation_id": "gen-2",
                "validation_result": {"is_valid": True},
                "processing_metadata": {"status": "completed"}
            }
        ]
        
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.retrieve_input = AsyncMock(return_value=stored_input_data)
            mock_service.get_input_history = AsyncMock(return_value=history_data)
            
            response = client.get(f"/api/v1/input-storage/{storage_id}/history")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["storage_id"] == "test-storage-123"
        assert data[1]["storage_id"] == "test-storage-456"
        
        # Verify service calls
        mock_service.retrieve_input.assert_called_once_with(storage_id)
        mock_service.get_input_history.assert_called_once_with("test-hash-123")
    
    def test_get_input_history_not_found(self, client):
        """Test GET /input-storage/{storage_id}/history endpoint when input not found"""
        storage_id = "nonexistent-storage-id"
        
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.retrieve_input = AsyncMock(return_value=None)
            
            response = client.get(f"/api/v1/input-storage/{storage_id}/history")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_delete_stored_input(self, client):
        """Test DELETE /input-storage/{storage_id} endpoint"""
        storage_id = "test-storage-123"
        
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.delete_input = AsyncMock(return_value=True)
            
            response = client.delete(f"/api/v1/input-storage/{storage_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        
        # Verify service was called
        mock_service.delete_input.assert_called_once_with(storage_id)
    
    def test_delete_stored_input_not_found(self, client):
        """Test DELETE /input-storage/{storage_id} endpoint when input not found"""
        storage_id = "nonexistent-storage-id"
        
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.delete_input = AsyncMock(return_value=False)
            
            response = client.delete(f"/api/v1/input-storage/{storage_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_get_storage_statistics(self, client):
        """Test GET /input-storage/stats/overview endpoint"""
        stats_data = {
            "total_inputs": 10,
            "content_type_distribution": {"text": 6, "file": 3, "url": 1},
            "total_content_size_bytes": 50000,
            "total_content_size_mb": 0.05,
            "vector_db_stats": {"content_count": 10, "scripts_count": 5},
            "file_storage_stats": {"total_files": 3, "total_size_bytes": 15000},
            "storage_directory": "/tmp/input_storage"
        }
        
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.get_storage_stats = AsyncMock(return_value=stats_data)
            
            response = client.get("/api/v1/input-storage/stats/overview")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_inputs"] == 10
        assert data["content_type_distribution"]["text"] == 6
        assert data["total_content_size_mb"] == 0.05
        assert "vector_db_stats" in data
        assert "file_storage_stats" in data
        
        # Verify service was called
        mock_service.get_storage_stats.assert_called_once()
    
    def test_search_validation_errors(self, client):
        """Test search endpoint with validation errors"""
        # Test missing query parameter
        response = client.get("/api/v1/input-storage/search")
        assert response.status_code == 422
        
        # Test invalid limit
        response = client.get(
            "/api/v1/input-storage/search",
            params={"query": "test", "limit": 0}
        )
        assert response.status_code == 422
        
        # Test invalid content type
        response = client.get(
            "/api/v1/input-storage/search",
            params={"query": "test", "content_type": "invalid"}
        )
        assert response.status_code == 422
    
    def test_list_validation_errors(self, client):
        """Test list endpoint with validation errors"""
        # Test invalid limit
        response = client.get(
            "/api/v1/input-storage/list",
            params={"limit": 0}
        )
        assert response.status_code == 422
        
        # Test invalid offset
        response = client.get(
            "/api/v1/input-storage/list",
            params={"offset": -1}
        )
        assert response.status_code == 422
    
    def test_search_service_error(self, client):
        """Test search endpoint when service raises an error"""
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.search_inputs = AsyncMock(side_effect=Exception("Service error"))
            
            response = client.get(
                "/api/v1/input-storage/search",
                params={"query": "test"}
            )
        
        assert response.status_code == 500
        data = response.json()
        assert "Search failed" in data["detail"]
    
    def test_retrieve_service_error(self, client):
        """Test retrieve endpoint when service raises an error"""
        storage_id = "test-storage-123"
        
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.retrieve_input = AsyncMock(side_effect=Exception("Service error"))
            
            response = client.get(f"/api/v1/input-storage/{storage_id}")
        
        assert response.status_code == 500
        data = response.json()
        assert "Retrieval failed" in data["detail"]
    
    def test_delete_service_error(self, client):
        """Test delete endpoint when service raises an error"""
        storage_id = "test-storage-123"
        
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.delete_input = AsyncMock(side_effect=Exception("Service error"))
            
            response = client.delete(f"/api/v1/input-storage/{storage_id}")
        
        assert response.status_code == 500
        data = response.json()
        assert "Deletion failed" in data["detail"]
    
    def test_stats_service_error(self, client):
        """Test stats endpoint when service raises an error"""
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.get_storage_stats = AsyncMock(side_effect=Exception("Service error"))
            
            response = client.get("/api/v1/input-storage/stats/overview")
        
        assert response.status_code == 500
        data = response.json()
        assert "Statistics retrieval failed" in data["detail"]


class TestInputStorageEndpointsIntegration:
    """Integration tests for input storage endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_api_documentation_includes_input_storage(self, client):
        """Test that API documentation includes input storage endpoints"""
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Check that OpenAPI spec includes input storage endpoints
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        paths = openapi_spec.get("paths", {})
        
        # Verify input storage endpoints are included
        assert "/api/v1/input-storage/search" in paths
        assert "/api/v1/input-storage/list" in paths
        assert "/api/v1/input-storage/{storage_id}" in paths
        assert "/api/v1/input-storage/{storage_id}/history" in paths
        assert "/api/v1/input-storage/stats/overview" in paths
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses"""
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.search_inputs = AsyncMock(return_value=[])
            
            response = client.get(
                "/api/v1/input-storage/search",
                params={"query": "test"},
                headers={"Origin": "http://localhost:3000"}
            )
        
        assert response.status_code == 200
        # CORS headers should be present (handled by FastAPI middleware)
        assert "access-control-allow-origin" in response.headers or "Access-Control-Allow-Origin" in response.headers
    
    def test_request_logging_middleware(self, client):
        """Test that request logging middleware works with input storage endpoints"""
        with patch('app.api.endpoints.input_storage.input_storage_service') as mock_service:
            mock_service.get_storage_stats = AsyncMock(return_value={
                "total_inputs": 0,
                "content_type_distribution": {},
                "total_content_size_bytes": 0,
                "total_content_size_mb": 0,
                "vector_db_stats": {},
                "file_storage_stats": {},
                "storage_directory": "/tmp"
            })
            
            response = client.get("/api/v1/input-storage/stats/overview")
        
        assert response.status_code == 200
        # Process time header should be added by middleware
        assert "X-Process-Time" in response.headers