"""
Tests for content generation endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app
from app.models.content import ContentResponse, GenerationStatus
import io
import tempfile
import os

@pytest.mark.unit
def test_text_prompt_endpoint_success(client: TestClient, sample_text_content: str):
    """Test successful text prompt processing."""
    response = client.post(
        "/api/v1/content/text",
        data={
            "content": sample_text_content,
            "topic": "Photosynthesis",
            "difficulty_level": "intermediate",
            "target_audience": "high school students",
            "learning_goals": "understand photosynthesis, identify stages"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate response structure
    assert "generation_id" in data
    assert "status" in data
    assert data["status"] in ["completed", "processing"]
    assert "created_at" in data
    
    # If completed, validate educational script structure
    if data["status"] == "completed":
        assert "educational_script" in data
        script = data["educational_script"]
        assert "title" in script
        assert "learning_objectives" in script
        assert "sections" in script

@pytest.mark.unit
def test_text_prompt_endpoint_minimal_input(client: TestClient):
    """Test text prompt endpoint with minimal valid input."""
    minimal_content = "This is a test educational content about basic math concepts."
    
    response = client.post(
        "/api/v1/content/text",
        data={"content": minimal_content}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "generation_id" in data
    assert "status" in data

@pytest.mark.unit
def test_text_prompt_endpoint_content_too_short(client: TestClient):
    """Test validation error for content that is too short."""
    response = client.post(
        "/api/v1/content/text",
        data={"content": "short"}  # Less than 10 characters
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "too short" in data["error"]["message"].lower()

@pytest.mark.unit
def test_text_prompt_endpoint_content_too_long(client: TestClient):
    """Test validation error for content that is too long."""
    long_content = "x" * 100001  # Exceeds 100KB limit
    
    response = client.post(
        "/api/v1/content/text",
        data={"content": long_content}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "too long" in data["error"]["message"].lower()

@pytest.mark.unit
def test_text_prompt_endpoint_empty_content(client: TestClient):
    """Test validation error for empty content."""
    response = client.post(
        "/api/v1/content/text",
        data={"content": "   "}  # Only whitespace
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "too short" in data["error"]["message"].lower()

@pytest.mark.unit
def test_text_prompt_endpoint_missing_content(client: TestClient):
    """Test validation error for missing content field."""
    response = client.post(
        "/api/v1/content/text",
        data={"topic": "Test Topic"}  # Missing required content field
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "validation_error"

@pytest.mark.unit
def test_text_prompt_endpoint_difficulty_levels(client: TestClient, sample_text_content: str):
    """Test different difficulty levels are accepted."""
    difficulty_levels = ["beginner", "intermediate", "advanced"]
    
    for level in difficulty_levels:
        response = client.post(
            "/api/v1/content/text",
            data={
                "content": sample_text_content,
                "difficulty_level": level
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "generation_id" in data

@pytest.mark.unit
def test_text_prompt_endpoint_learning_goals_parsing(client: TestClient, sample_text_content: str):
    """Test that learning goals are properly parsed from comma-separated string."""
    learning_goals = "goal1, goal2, goal3"
    
    with patch('app.services.content_service.ContentService.generate_from_inputs') as mock_generate:
        mock_generate.return_value = {
            "generation_id": "test-id",
            "status": "completed",
            "educational_script": {"title": "Test"},
            "created_at": "2024-01-01T00:00:00"
        }
        
        response = client.post(
            "/api/v1/content/text",
            data={
                "content": sample_text_content,
                "learning_goals": learning_goals
            }
        )
        
        assert response.status_code == 200
        
        # Verify that the service was called with parsed learning goals
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        assert call_args[1]["learning_goals"] == ["goal1", "goal2", "goal3"]

@pytest.mark.unit
def test_text_prompt_endpoint_empty_learning_goals(client: TestClient, sample_text_content: str):
    """Test that empty learning goals are handled correctly."""
    with patch('app.services.content_service.ContentService.generate_from_inputs') as mock_generate:
        mock_generate.return_value = {
            "generation_id": "test-id",
            "status": "completed",
            "educational_script": {"title": "Test"},
            "created_at": "2024-01-01T00:00:00"
        }
        
        response = client.post(
            "/api/v1/content/text",
            data={
                "content": sample_text_content,
                "learning_goals": ""
            }
        )
        
        assert response.status_code == 200
        
        # Verify that the service was called with empty learning goals list
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        assert call_args[1]["learning_goals"] == []

@pytest.mark.unit
def test_text_prompt_endpoint_unicode_content(client: TestClient):
    """Test that unicode content is handled correctly."""
    unicode_content = "This content has unicode characters: 你好, café, naïve, résumé. Mathematical symbols: ∑, ∫, π, α, β."
    
    response = client.post(
        "/api/v1/content/text",
        data={"content": unicode_content}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "generation_id" in data

@pytest.mark.unit
def test_text_prompt_endpoint_special_characters(client: TestClient):
    """Test that special characters in content are handled correctly."""
    special_content = """
    Content with special characters:
    - Quotes: "Hello" and 'World'
    - Symbols: @#$%^&*()
    - HTML-like: <tag>content</tag>
    - Code: function() { return true; }
    """
    
    response = client.post(
        "/api/v1/content/text",
        data={"content": special_content}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "generation_id" in data

@pytest.mark.unit
def test_text_prompt_endpoint_service_error_handling(client: TestClient, sample_text_content: str):
    """Test error handling when content service fails."""
    with patch('app.services.content_service.ContentService.generate_from_inputs') as mock_generate:
        mock_generate.side_effect = Exception("Service error")
        
        response = client.post(
            "/api/v1/content/text",
            data={"content": sample_text_content}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "Content generation failed" in data["error"]["message"]

@pytest.mark.unit
def test_text_prompt_endpoint_content_request_creation(client: TestClient, sample_text_content: str):
    """Test that ContentRequest is properly created from form data."""
    with patch('app.services.content_service.ContentService.generate_from_inputs') as mock_generate:
        mock_generate.return_value = {
            "generation_id": "test-id",
            "status": "completed",
            "educational_script": {"title": "Test"},
            "created_at": "2024-01-01T00:00:00"
        }
        
        response = client.post(
            "/api/v1/content/text",
            data={
                "content": sample_text_content,
                "topic": "Test Topic",
                "difficulty_level": "advanced",
                "target_audience": "college students",
                "learning_goals": "goal1, goal2"
            }
        )
        
        assert response.status_code == 200
        
        # Verify the service was called with correct parameters
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        
        # Check inputs structure
        inputs = call_args[1]["inputs"]
        assert len(inputs) == 1
        assert inputs[0].content_type == "text"
        assert inputs[0].content == sample_text_content
        assert inputs[0].metadata["source"] == "text_prompt"
        
        # Check other parameters
        assert call_args[1]["topic"] == "Test Topic"
        assert call_args[1]["difficulty_level"] == "advanced"
        assert call_args[1]["target_audience"] == "college students"
        assert call_args[1]["learning_goals"] == ["goal1", "goal2"]
        assert call_args[1]["preferences"] == {}

# File Upload Tests

@pytest.mark.unit
def test_file_upload_endpoint_success_txt(client: TestClient):
    """Test successful text file upload."""
    file_content = "This is a sample educational content about photosynthesis. It explains how plants convert sunlight into energy."
    
    with patch('app.services.content_service.ContentService.generate_from_file') as mock_generate:
        mock_generate.return_value = {
            "generation_id": "test-file-id",
            "status": "completed",
            "educational_script": {"title": "Test File Content"},
            "created_at": "2024-01-01T00:00:00"
        }
        
        response = client.post(
            "/api/v1/content/upload",
            files={"file": ("test.txt", io.BytesIO(file_content.encode()), "text/plain")},
            data={
                "topic": "Photosynthesis",
                "difficulty_level": "intermediate",
                "target_audience": "high school students",
                "learning_goals": "understand photosynthesis, identify stages"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "generation_id" in data
        assert data["generation_id"] == "test-file-id"
        assert "status" in data

@pytest.mark.unit
def test_file_upload_endpoint_success_pdf(client: TestClient):
    """Test successful PDF file upload."""
    # Create a minimal PDF content (PDF header)
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    
    with patch('app.services.content_service.ContentService.generate_from_file') as mock_generate:
        mock_generate.return_value = {
            "generation_id": "test-pdf-id",
            "status": "completed",
            "educational_script": {"title": "Test PDF Content"},
            "created_at": "2024-01-01T00:00:00"
        }
        
        with patch('magic.from_file', return_value='application/pdf'):
            response = client.post(
                "/api/v1/content/upload",
                files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")},
                data={
                    "topic": "Test PDF",
                    "target_audience": "test students"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "generation_id" in data

@pytest.mark.unit
def test_file_upload_endpoint_no_file(client: TestClient):
    """Test error when no file is provided."""
    response = client.post(
        "/api/v1/content/upload",
        data={"topic": "Test Topic"}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "error" in data

@pytest.mark.unit
def test_file_upload_endpoint_empty_file(client: TestClient):
    """Test error when empty file is uploaded."""
    response = client.post(
        "/api/v1/content/upload",
        files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
        data={
            "topic": "Test Topic",
            "target_audience": "test students"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "empty" in data["error"]["message"].lower()

@pytest.mark.unit
def test_file_upload_endpoint_file_too_large(client: TestClient):
    """Test error when file is too large."""
    # Create a file larger than the 10MB limit
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    
    response = client.post(
        "/api/v1/content/upload",
        files={"file": ("large.txt", io.BytesIO(large_content), "text/plain")},
        data={
            "topic": "Test Topic",
            "target_audience": "test students"
        }
    )
    
    assert response.status_code == 413
    data = response.json()
    assert "error" in data
    assert "too large" in data["error"]["message"].lower()

@pytest.mark.unit
def test_file_upload_endpoint_unsupported_extension(client: TestClient):
    """Test error when file has unsupported extension."""
    file_content = b"This is an unsupported file type"
    
    response = client.post(
        "/api/v1/content/upload",
        files={"file": ("test.xyz", io.BytesIO(file_content), "application/octet-stream")},
        data={
            "topic": "Test Topic",
            "target_audience": "test students"
        }
    )
    
    assert response.status_code == 415
    data = response.json()
    assert "error" in data
    assert "unsupported file type" in data["error"]["message"].lower()

@pytest.mark.unit
def test_file_upload_endpoint_invalid_pdf(client: TestClient):
    """Test error when file claims to be PDF but isn't."""
    fake_pdf_content = b"This is not a PDF file"
    
    response = client.post(
        "/api/v1/content/upload",
        files={"file": ("fake.pdf", io.BytesIO(fake_pdf_content), "application/pdf")},
        data={
            "topic": "Test Topic",
            "target_audience": "test students"
        }
    )
    
    assert response.status_code == 415
    data = response.json()
    assert "error" in data
    assert "valid PDF" in data["error"]["message"]

@pytest.mark.unit
def test_file_upload_endpoint_invalid_difficulty_level(client: TestClient):
    """Test error when invalid difficulty level is provided."""
    file_content = "Valid educational content about science topics."
    
    response = client.post(
        "/api/v1/content/upload",
        files={"file": ("test.txt", io.BytesIO(file_content.encode()), "text/plain")},
        data={
            "topic": "Test Topic",
            "difficulty_level": "invalid_level"
        }
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "invalid difficulty level" in data["error"]["message"].lower()

@pytest.mark.unit
def test_file_upload_endpoint_empty_target_audience(client: TestClient):
    """Test error when target audience is empty."""
    file_content = "Valid educational content about science topics."
    
    response = client.post(
        "/api/v1/content/upload",
        files={"file": ("test.txt", io.BytesIO(file_content.encode()), "text/plain")},
        data={
            "topic": "Test Topic",
            "target_audience": "   "  # Only whitespace
        }
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "target audience cannot be empty" in data["error"]["message"].lower()

@pytest.mark.unit
def test_file_upload_endpoint_target_audience_too_long(client: TestClient):
    """Test error when target audience is too long."""
    file_content = "Valid educational content about science topics."
    long_audience = "x" * 201  # Exceeds 200 character limit
    
    response = client.post(
        "/api/v1/content/upload",
        files={"file": ("test.txt", io.BytesIO(file_content.encode()), "text/plain")},
        data={
            "topic": "Test Topic",
            "target_audience": long_audience
        }
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "too long" in data["error"]["message"].lower()

@pytest.mark.unit
def test_file_upload_endpoint_learning_goals_parsing(client: TestClient):
    """Test that learning goals are properly parsed from comma-separated string."""
    file_content = "Valid educational content about science topics."
    
    with patch('app.services.content_service.ContentService.generate_from_file') as mock_generate:
        mock_generate.return_value = {
            "generation_id": "test-id",
            "status": "completed",
            "educational_script": {"title": "Test"},
            "created_at": "2024-01-01T00:00:00"
        }
        
        response = client.post(
            "/api/v1/content/upload",
            files={"file": ("test.txt", io.BytesIO(file_content.encode()), "text/plain")},
            data={
                "topic": "Test Topic",
                "learning_goals": "goal1, goal2, goal3"
            }
        )
        
        assert response.status_code == 200
        
        # Verify that the service was called with parsed learning goals
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        assert call_args[1]["learning_goals"] == ["goal1", "goal2", "goal3"]

@pytest.mark.unit
def test_file_upload_endpoint_text_file_too_short(client: TestClient):
    """Test error when text file content is too short."""
    short_content = "short"  # Less than 10 characters
    
    response = client.post(
        "/api/v1/content/upload",
        files={"file": ("test.txt", io.BytesIO(short_content.encode()), "text/plain")},
        data={"topic": "Test Topic"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "too short" in data["error"]["message"].lower()

@pytest.mark.unit
def test_file_upload_endpoint_invalid_text_encoding(client: TestClient):
    """Test error when text file has invalid encoding."""
    # Create invalid UTF-8 bytes
    invalid_content = b'\xff\xfe\x00\x00invalid'
    
    response = client.post(
        "/api/v1/content/upload",
        files={"file": ("test.txt", io.BytesIO(invalid_content), "text/plain")},
        data={"topic": "Test Topic"}
    )
    
    assert response.status_code == 415
    data = response.json()
    assert "error" in data
    assert "invalid characters" in data["error"]["message"].lower()

@pytest.mark.unit
def test_file_upload_endpoint_service_error_handling(client: TestClient):
    """Test error handling when content service fails."""
    file_content = "Valid educational content about science topics."
    
    with patch('app.services.content_service.ContentService.generate_from_file') as mock_generate:
        mock_generate.side_effect = Exception("Service error")
        
        response = client.post(
            "/api/v1/content/upload",
            files={"file": ("test.txt", io.BytesIO(file_content.encode()), "text/plain")},
            data={"topic": "Test Topic"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "File processing failed" in data["error"]["message"]

@pytest.mark.unit
def test_file_upload_endpoint_docx_validation(client: TestClient):
    """Test DOCX file validation."""
    # DOCX files are ZIP archives, so they start with PK
    docx_content = b"PK\x03\x04" + b"fake docx content"
    
    with patch('app.services.content_service.ContentService.generate_from_file') as mock_generate:
        mock_generate.return_value = {
            "generation_id": "test-docx-id",
            "status": "completed",
            "educational_script": {"title": "Test DOCX Content"},
            "created_at": "2024-01-01T00:00:00"
        }
        
        with patch('magic.from_file', return_value='application/vnd.openxmlformats-officedocument.wordprocessingml.document'):
            response = client.post(
                "/api/v1/content/upload",
                files={"file": ("test.docx", io.BytesIO(docx_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"topic": "Test DOCX"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "generation_id" in data

@pytest.mark.unit
def test_file_upload_endpoint_invalid_docx(client: TestClient):
    """Test error when file claims to be DOCX but isn't."""
    fake_docx_content = b"This is not a DOCX file"
    
    response = client.post(
        "/api/v1/content/upload",
        files={"file": ("fake.docx", io.BytesIO(fake_docx_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"topic": "Test Topic"}
    )
    
    assert response.status_code == 415
    data = response.json()
    assert "error" in data
    assert "valid DOCX" in data["error"]["message"]

@pytest.mark.integration
def test_file_upload_endpoint_integration(client: TestClient):
    """Integration test for file upload endpoint with real service."""
    educational_content = """
    The Water Cycle
    
    The water cycle is the continuous movement of water on, above, and below the surface of the Earth.
    It involves several key processes:
    
    1. Evaporation: Water changes from liquid to vapor
    2. Condensation: Water vapor changes back to liquid
    3. Precipitation: Water falls as rain, snow, or hail
    4. Collection: Water gathers in bodies of water
    
    This cycle is powered by the sun's energy and is essential for all life on Earth.
    """
    
    response = client.post(
        "/api/v1/content/upload",
        files={"file": ("water_cycle.txt", io.BytesIO(educational_content.encode()), "text/plain")},
        data={
            "topic": "The Water Cycle",
            "difficulty_level": "intermediate",
            "target_audience": "middle school students",
            "learning_goals": "understand water cycle, identify processes"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate response structure
    assert "generation_id" in data
    assert "status" in data
    assert "created_at" in data
    
    # The response should have either completed content or be in processing state
    assert data["status"] in ["completed", "processing", "failed"]
    
    if data["status"] == "completed":
        assert "educational_script" in data
        script = data["educational_script"]
        assert script["title"] is not None
        assert len(script.get("learning_objectives", [])) >= 0
        assert len(script.get("sections", [])) >= 0

@pytest.mark.integration
def test_text_prompt_endpoint_integration(client: TestClient):
    """Integration test for text prompt endpoint with real service."""
    educational_content = """
    The Water Cycle
    
    The water cycle is the continuous movement of water on, above, and below the surface of the Earth.
    It involves several key processes:
    
    1. Evaporation: Water changes from liquid to vapor
    2. Condensation: Water vapor changes back to liquid
    3. Precipitation: Water falls as rain, snow, or hail
    4. Collection: Water gathers in bodies of water
    
    This cycle is powered by the sun's energy and is essential for all life on Earth.
    """
    
    response = client.post(
        "/api/v1/content/text",
        data={
            "content": educational_content,
            "topic": "The Water Cycle",
            "difficulty_level": "intermediate",
            "target_audience": "middle school students",
            "learning_goals": "understand water cycle, identify processes"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate response structure
    assert "generation_id" in data
    assert "status" in data
    assert "created_at" in data
    
    # The response should have either completed content or be in processing state
    assert data["status"] in ["completed", "processing", "failed"]
    
    if data["status"] == "completed":
        assert "educational_script" in data
        script = data["educational_script"]
        assert script["title"] is not None
        assert len(script.get("learning_objectives", [])) >= 0
        assert len(script.get("sections", [])) >= 0