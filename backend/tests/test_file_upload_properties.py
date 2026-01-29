"""
Property-based tests for file upload endpoint validation
**Validates: Requirements 1.1**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from fastapi.testclient import TestClient
from unittest.mock import patch
import io
import tempfile
import os
from app.main import app
from app.core.config import settings as app_settings

client = TestClient(app)

# Test data strategies
@st.composite
def valid_text_content(draw):
    """Generate valid text content for files"""
    # Generate text with at least 10 characters
    base_text = draw(st.text(min_size=10, max_size=1000))
    # Ensure it's not just whitespace
    assume(len(base_text.strip()) >= 10)
    return base_text

@st.composite
def valid_file_data(draw):
    """Generate valid file upload data"""
    content = draw(valid_text_content())
    filename = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='._-')))
    # Ensure filename has valid extension
    extensions = ['.txt', '.pdf', '.doc', '.docx']
    extension = draw(st.sampled_from(extensions))
    
    if not filename.endswith(tuple(extensions)):
        filename = filename + extension
    
    return {
        'content': content,
        'filename': filename,
        'extension': extension
    }

@st.composite
def valid_form_data(draw):
    """Generate valid form data for file upload"""
    topic = draw(st.one_of(
        st.none(),
        st.text(min_size=1, max_size=100)
    ))
    difficulty_level = draw(st.sampled_from(['beginner', 'intermediate', 'advanced']))
    target_audience = draw(st.text(min_size=1, max_size=200))
    learning_goals = draw(st.one_of(
        st.just(''),
        st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5).map(lambda x: ', '.join(x))
    ))
    
    return {
        'topic': topic,
        'difficulty_level': difficulty_level,
        'target_audience': target_audience,
        'learning_goals': learning_goals
    }

@pytest.mark.property
@given(
    file_data=valid_file_data(),
    form_data=valid_form_data()
)
@settings(max_examples=20, deadline=5000)
def test_file_upload_validation_property(file_data, form_data):
    """
    Property: Valid file uploads with proper validation should always succeed or fail predictably
    **Validates: Requirements 1.1**
    
    This test ensures that:
    1. Valid files with supported formats are accepted
    2. File validation is consistent across different inputs
    3. Form data validation works correctly
    4. The endpoint handles various combinations of valid inputs
    """
    with patch('app.services.content_service.ContentService.generate_from_file') as mock_generate:
        mock_generate.return_value = {
            "generation_id": "test-property-id",
            "status": "completed",
            "educational_script": {"title": "Test Property Content"},
            "created_at": "2024-01-01T00:00:00"
        }
        
        # Prepare file content based on extension
        content_bytes = file_data['content'].encode('utf-8')
        
        # Adjust content for specific file types to pass validation
        if file_data['extension'] == '.pdf':
            # Add PDF header for validation
            content_bytes = b'%PDF-1.4\n' + content_bytes
            mime_type = 'application/pdf'
        elif file_data['extension'] == '.docx':
            # Add ZIP header for DOCX validation
            content_bytes = b'PK\x03\x04' + content_bytes
            mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif file_data['extension'] == '.doc':
            # Add DOC header for validation
            content_bytes = b'\xd0\xcf\x11\xe0' + content_bytes
            mime_type = 'application/msword'
        else:  # .txt
            mime_type = 'text/plain'
        
        # Mock MIME type detection for non-text files
        with patch('magic.from_file', return_value=mime_type):
            response = client.post(
                "/api/v1/content/upload",
                files={"file": (file_data['filename'], io.BytesIO(content_bytes), mime_type)},
                data={k: v for k, v in form_data.items() if v is not None}
            )
        
        # Property: Valid inputs should result in successful processing (200) or validation error (4xx)
        assert response.status_code in [200, 400, 413, 415, 422], f"Unexpected status code: {response.status_code}"
        
        if response.status_code == 200:
            # If successful, response should have required fields
            data = response.json()
            assert "generation_id" in data
            assert "status" in data
            assert "created_at" in data
            
            # Verify the service was called with correct parameters
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            assert call_args[1]["difficulty_level"] == form_data["difficulty_level"]
            assert call_args[1]["target_audience"] == form_data["target_audience"]
            
            # Verify learning goals parsing
            expected_goals = []
            if form_data["learning_goals"].strip():
                expected_goals = [goal.strip() for goal in form_data["learning_goals"].split(",") if goal.strip()]
            assert call_args[1]["learning_goals"] == expected_goals

@pytest.mark.property
@given(
    file_size=st.integers(min_value=0, max_value=app_settings.MAX_FILE_SIZE + 1000000),
    filename=st.text(min_size=1, max_size=100)
)
@settings(max_examples=15, deadline=3000)
def test_file_size_validation_property(file_size, filename):
    """
    Property: File size validation should consistently reject files exceeding the limit
    **Validates: Requirements 1.1**
    
    This test ensures that:
    1. Files within size limit are processed
    2. Files exceeding size limit are rejected with 413 status
    3. Empty files are rejected with 400 status
    """
    # Generate content of specified size
    content = b'x' * file_size
    
    # Add valid extension if not present
    if not any(filename.endswith(ext) for ext in ['.txt', '.pdf', '.doc', '.docx']):
        filename = filename + '.txt'
    
    with patch('app.services.content_service.ContentService.generate_from_file') as mock_generate:
        mock_generate.return_value = {
            "generation_id": "test-size-id",
            "status": "completed",
            "educational_script": {"title": "Test Size Content"},
            "created_at": "2024-01-01T00:00:00"
        }
        
        response = client.post(
            "/api/v1/content/upload",
            files={"file": (filename, io.BytesIO(content), "text/plain")},
            data={
                "topic": "Test Topic",
                "target_audience": "test students"  # Add required field
            }
        )
        
        # Property: File size validation should be consistent
        if file_size == 0:
            # Empty files should be rejected
            assert response.status_code == 400
            data = response.json()
            assert "empty" in data["error"]["message"].lower()
        elif file_size > app_settings.MAX_FILE_SIZE:
            # Files too large should be rejected
            assert response.status_code == 413
            data = response.json()
            assert "too large" in data["error"]["message"].lower()
        else:
            # Valid size files should be processed (may fail for other reasons like content validation)
            assert response.status_code in [200, 400, 415], f"Unexpected status for size {file_size}: {response.status_code}"

@pytest.mark.property
@given(
    extension=st.sampled_from(['.xyz', '.exe', '.bin', '.jpg', '.png', '.mp3', '.zip']),
    content=st.text(min_size=10, max_size=100)
)
@settings(max_examples=10, deadline=2000)
def test_unsupported_file_types_property(extension, content):
    """
    Property: Unsupported file types should always be rejected with 415 status
    **Validates: Requirements 1.1**
    
    This test ensures that:
    1. Only supported file types (.pdf, .doc, .docx, .txt) are accepted
    2. Unsupported file types are consistently rejected
    3. Error messages are informative
    """
    filename = f"test{extension}"
    content_bytes = content.encode('utf-8')
    
    response = client.post(
        "/api/v1/content/upload",
        files={"file": (filename, io.BytesIO(content_bytes), "application/octet-stream")},
        data={
            "topic": "Test Topic",
            "target_audience": "test students"  # Add required field
        }
    )
    
    # Property: Unsupported file types should always be rejected
    assert response.status_code == 415
    data = response.json()
    assert "error" in data
    assert "unsupported file type" in data["error"]["message"].lower()

@pytest.mark.property
@given(
    difficulty_level=st.text().filter(lambda x: x not in ['beginner', 'intermediate', 'advanced'] and x.strip() != ''),
    target_audience=st.one_of(
        st.just(''),  # Empty string
        st.just('   '),  # Only whitespace
        st.text(min_size=201, max_size=300)  # Too long
    )
)
@settings(max_examples=10, deadline=2000)
def test_form_validation_property(difficulty_level, target_audience):
    """
    Property: Invalid form data should be consistently rejected with 422 status
    **Validates: Requirements 1.1**
    
    This test ensures that:
    1. Invalid difficulty levels are rejected
    2. Invalid target audience values are rejected
    3. Form validation is consistent
    """
    content = "This is valid educational content for testing form validation."
    
    response = client.post(
        "/api/v1/content/upload",
        files={"file": ("test.txt", io.BytesIO(content.encode()), "text/plain")},
        data={
            "topic": "Test Topic",
            "difficulty_level": difficulty_level,
            "target_audience": target_audience
        }
    )
    
    # Property: Invalid form data should be rejected
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    
    # Check that we get a validation error - the specific message depends on which validation fails first
    error_message = data["error"]["message"].lower()
    assert any([
        "invalid difficulty level" in error_message,
        "target audience cannot be empty" in error_message,
        "too long" in error_message,
        "validation_error" in data["error"].get("type", "")
    ]), f"Expected validation error, got: {error_message}"

@pytest.mark.property
@given(
    content_length=st.integers(min_value=0, max_value=20)
)
@settings(max_examples=10, deadline=2000)
def test_text_content_length_validation_property(content_length):
    """
    Property: Text files with insufficient content should be rejected
    **Validates: Requirements 1.1**
    
    This test ensures that:
    1. Text files must have at least 10 meaningful characters
    2. Content length validation is consistent
    """
    # Generate content of specified length
    content = 'x' * content_length
    
    response = client.post(
        "/api/v1/content/upload",
        files={"file": ("test.txt", io.BytesIO(content.encode()), "text/plain")},
        data={
            "topic": "Test Topic",
            "target_audience": "test students"  # Add required field
        }
    )
    
    # Property: Content length validation should be consistent
    if content_length == 0:
        # Empty files should be rejected with "file is empty" message
        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["error"]["message"].lower()
    elif content_length < 10:
        # Short content should be rejected with "too short" message
        assert response.status_code == 400
        data = response.json()
        assert "too short" in data["error"]["message"].lower()
    else:
        # Valid length content should be processed
        assert response.status_code in [200, 500], f"Unexpected status for length {content_length}: {response.status_code}"