"""
Tests for file storage service
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from app.services.file_storage import FileStorageService
from app.core.config import settings

@pytest.fixture
def temp_file_storage():
    """Create a temporary file storage service for testing"""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Create FileStorageService with temporary directory
    service = FileStorageService()
    service.upload_dir = Path(temp_dir)
    service.upload_dir.mkdir(parents=True, exist_ok=True)
    
    yield service
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile for testing"""
    mock_file = Mock()
    mock_file.filename = "test_document.txt"
    mock_file.content_type = "text/plain"
    mock_file.size = 1024
    mock_file.read = AsyncMock(return_value=b"Test file content")
    mock_file.seek = AsyncMock()
    return mock_file

@pytest.mark.unit
def test_file_storage_initialization(temp_file_storage):
    """Test file storage service initialization"""
    service = temp_file_storage
    assert service.upload_dir.exists()
    assert service.max_file_size == settings.MAX_FILE_SIZE
    assert service.allowed_extensions == settings.ALLOWED_FILE_TYPES

@pytest.mark.asyncio
@pytest.mark.unit
async def test_validate_file_success(temp_file_storage, mock_upload_file):
    """Test successful file validation"""
    service = temp_file_storage
    
    result = await service._validate_file(mock_upload_file)
    assert result["valid"] is True

@pytest.mark.asyncio
@pytest.mark.unit
async def test_validate_file_size_exceeded(temp_file_storage):
    """Test file validation with size exceeded"""
    service = temp_file_storage
    
    mock_file = Mock()
    mock_file.filename = "large_file.txt"
    mock_file.size = service.max_file_size + 1
    
    result = await service._validate_file(mock_file)
    assert result["valid"] is False
    assert "exceeds maximum" in result["error"]

@pytest.mark.asyncio
@pytest.mark.unit
async def test_validate_file_invalid_extension(temp_file_storage):
    """Test file validation with invalid extension"""
    service = temp_file_storage
    
    mock_file = Mock()
    mock_file.filename = "test_file.exe"
    mock_file.size = 1024
    
    result = await service._validate_file(mock_file)
    assert result["valid"] is False
    assert "not allowed" in result["error"]

@pytest.mark.unit
def test_generate_file_id(temp_file_storage):
    """Test file ID generation"""
    service = temp_file_storage
    
    file_id1 = service._generate_file_id("test.txt")
    file_id2 = service._generate_file_id("test.txt")
    
    # IDs should be different (due to timestamp)
    assert file_id1 != file_id2
    assert len(file_id1) == 16  # SHA256 hash truncated to 16 chars
    assert len(file_id2) == 16

@pytest.mark.unit
def test_get_storage_stats_empty(temp_file_storage):
    """Test storage statistics for empty storage"""
    service = temp_file_storage
    
    stats = service.get_storage_stats()
    assert stats["total_files"] == 0
    assert stats["total_size_bytes"] == 0
    assert stats["total_size_mb"] == 0
    assert "upload_dir" in stats

@pytest.mark.unit
def test_list_files_empty(temp_file_storage):
    """Test listing files in empty storage"""
    service = temp_file_storage
    
    files = service.list_files()
    assert files == []

@pytest.mark.unit
def test_get_file_info_nonexistent(temp_file_storage):
    """Test getting info for non-existent file"""
    service = temp_file_storage
    
    info = service.get_file_info("nonexistent_id")
    assert info is None

@pytest.mark.unit
def test_delete_nonexistent_file(temp_file_storage):
    """Test deleting non-existent file"""
    service = temp_file_storage
    
    result = service.delete_file("nonexistent_id")
    assert result is False

@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_file_content_nonexistent(temp_file_storage):
    """Test getting content of non-existent file"""
    service = temp_file_storage
    
    content = await service.get_file_content("nonexistent_id")
    assert content is None

@pytest.mark.unit
def test_get_mime_type_fallback(temp_file_storage):
    """Test MIME type detection fallback"""
    service = temp_file_storage
    
    # Create a temporary file
    test_file = service.upload_dir / "test.pdf"
    test_file.write_text("fake pdf content")
    
    mime_type = service._get_mime_type(test_file)
    # Should fallback to extension-based detection
    assert mime_type in ["application/pdf", "text/plain"]  # Depending on magic library availability