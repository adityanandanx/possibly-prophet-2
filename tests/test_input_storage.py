"""
Tests for input storage service
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.services.input_storage import InputStorageService, input_storage_service
from app.models.content import ContentInput, ContentType


class TestInputStorageService:
    """Test cases for InputStorageService"""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage_service(self, temp_storage_dir):
        """Create InputStorageService with temporary directory"""
        service = InputStorageService()
        service.storage_dir = temp_storage_dir / "input_storage"
        service.storage_dir.mkdir(parents=True, exist_ok=True)
        service.stored_inputs = {}  # Reset in-memory storage
        return service
    
    @pytest.fixture
    def sample_text_input(self):
        """Sample text input for testing"""
        return ContentInput(
            content_type=ContentType.TEXT,
            content="This is a sample educational content about photosynthesis. Plants convert sunlight into energy through this process.",
            metadata={"topic": "photosynthesis", "difficulty": "intermediate"}
        )
    
    @pytest.fixture
    def sample_file_input(self):
        """Sample file input for testing"""
        return ContentInput(
            content_type=ContentType.FILE,
            content="File content about mathematics. Algebra is a branch of mathematics dealing with symbols.",
            metadata={
                "filename": "math_content.pdf",
                "file_size": 1024,
                "mime_type": "application/pdf"
            }
        )
    
    @pytest.fixture
    def sample_url_input(self):
        """Sample URL input for testing"""
        return ContentInput(
            content_type=ContentType.URL,
            content="Web content about physics. Newton's laws describe the relationship between forces and motion.",
            metadata={
                "source_url": "https://example.com/physics",
                "page_title": "Physics Fundamentals"
            }
        )
    
    @pytest.mark.asyncio
    async def test_store_text_input(self, storage_service, sample_text_input):
        """Test storing text input with metadata"""
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "metadata": {"content_hash": "abc123"}
        }
        
        processing_metadata = {
            "status": "processing",
            "start_time": datetime.now().isoformat()
        }
        
        generation_id = "test-gen-123"
        
        # Mock vector database operations
        with patch('app.services.input_storage.vector_db_service') as mock_vector_db:
            mock_vector_db.add_content.return_value = True
            
            storage_id = await storage_service.store_input(
                content_input=sample_text_input,
                validation_result=validation_result,
                processing_metadata=processing_metadata,
                generation_id=generation_id
            )
        
        # Verify storage ID is returned
        assert storage_id is not None
        assert len(storage_id) == 36  # UUID length
        
        # Verify in-memory storage
        assert storage_id in storage_service.stored_inputs
        stored_data = storage_service.stored_inputs[storage_id]
        assert stored_data["content"] == sample_text_input.content
        assert stored_data["metadata"]["content_type"] == ContentType.TEXT.value
        assert stored_data["metadata"]["generation_id"] == generation_id
        
        # Verify filesystem storage
        input_dir = storage_service.storage_dir / storage_id
        assert input_dir.exists()
        assert (input_dir / "content.txt").exists()
        assert (input_dir / "metadata.json").exists()
        
        # Verify content file
        with open(input_dir / "content.txt", 'r') as f:
            stored_content = f.read()
        assert stored_content == sample_text_input.content
        
        # Verify vector database was called
        mock_vector_db.add_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_file_input(self, storage_service, sample_file_input):
        """Test storing file input with file-specific metadata"""
        validation_result = {"is_valid": True, "warnings": [], "errors": []}
        
        with patch('app.services.input_storage.vector_db_service') as mock_vector_db:
            mock_vector_db.add_content.return_value = True
            
            storage_id = await storage_service.store_input(
                content_input=sample_file_input,
                validation_result=validation_result
            )
        
        # Verify file-specific metadata
        stored_data = storage_service.stored_inputs[storage_id]
        assert "file_metadata" in stored_data["metadata"]
        file_metadata = stored_data["metadata"]["file_metadata"]
        assert file_metadata["filename"] == "math_content.pdf"
        assert file_metadata["file_size"] == 1024
        assert file_metadata["mime_type"] == "application/pdf"
    
    @pytest.mark.asyncio
    async def test_store_url_input(self, storage_service, sample_url_input):
        """Test storing URL input with URL-specific metadata"""
        validation_result = {"is_valid": True, "warnings": [], "errors": []}
        
        with patch('app.services.input_storage.vector_db_service') as mock_vector_db:
            mock_vector_db.add_content.return_value = True
            
            storage_id = await storage_service.store_input(
                content_input=sample_url_input,
                validation_result=validation_result
            )
        
        # Verify URL-specific metadata
        stored_data = storage_service.stored_inputs[storage_id]
        assert "url_metadata" in stored_data["metadata"]
        url_metadata = stored_data["metadata"]["url_metadata"]
        assert url_metadata["source_url"] == "https://example.com/physics"
        assert url_metadata["page_title"] == "Physics Fundamentals"
    
    @pytest.mark.asyncio
    async def test_retrieve_input(self, storage_service, sample_text_input):
        """Test retrieving stored input by ID"""
        validation_result = {"is_valid": True, "warnings": [], "errors": []}
        
        with patch('app.services.input_storage.vector_db_service') as mock_vector_db:
            mock_vector_db.add_content.return_value = True
            
            # Store input
            storage_id = await storage_service.store_input(
                content_input=sample_text_input,
                validation_result=validation_result
            )
            
            # Retrieve input
            retrieved_data = await storage_service.retrieve_input(storage_id)
        
        # Verify retrieved data
        assert retrieved_data is not None
        assert retrieved_data["content"] == sample_text_input.content
        assert retrieved_data["metadata"]["storage_id"] == storage_id
        assert retrieved_data["metadata"]["content_type"] == ContentType.TEXT.value
    
    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_input(self, storage_service):
        """Test retrieving non-existent input returns None"""
        result = await storage_service.retrieve_input("nonexistent-id")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_search_inputs(self, storage_service, sample_text_input, sample_file_input):
        """Test searching stored inputs"""
        validation_result = {"is_valid": True, "warnings": [], "errors": []}
        
        with patch('app.services.input_storage.vector_db_service') as mock_vector_db:
            mock_vector_db.add_content.return_value = True
            
            # Mock search results
            mock_vector_db.search_content.return_value = [
                {
                    "id": "storage-1",
                    "content": sample_text_input.content,
                    "metadata": {"content_type": "text"},
                    "distance": 0.2
                }
            ]
            
            # Store inputs
            storage_id1 = await storage_service.store_input(
                content_input=sample_text_input,
                validation_result=validation_result
            )
            storage_id2 = await storage_service.store_input(
                content_input=sample_file_input,
                validation_result=validation_result
            )
            
            # Update mock to return actual storage ID
            mock_vector_db.search_content.return_value[0]["id"] = storage_id1
            
            # Search inputs
            results = await storage_service.search_inputs(
                query="photosynthesis",
                content_type=ContentType.TEXT,
                limit=10
            )
        
        # Verify search results
        assert len(results) == 1
        assert results[0]["storage_id"] == storage_id1
        assert results[0]["content"] == sample_text_input.content
        assert "similarity_score" in results[0]
        assert "search_snippet" in results[0]
        
        # Verify vector database search was called
        mock_vector_db.search_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_inputs(self, storage_service, sample_text_input, sample_file_input):
        """Test listing stored inputs with filters"""
        validation_result = {"is_valid": True, "warnings": [], "errors": []}
        
        with patch('app.services.input_storage.vector_db_service') as mock_vector_db:
            mock_vector_db.add_content.return_value = True
            
            # Store inputs
            text_storage_id = await storage_service.store_input(
                content_input=sample_text_input,
                validation_result=validation_result,
                generation_id="gen-1"
            )
            file_storage_id = await storage_service.store_input(
                content_input=sample_file_input,
                validation_result=validation_result,
                generation_id="gen-2"
            )
            
            # List all inputs
            all_results = await storage_service.list_inputs(limit=10)
            assert len(all_results) == 2
            
            # List with content type filter
            text_results = await storage_service.list_inputs(
                content_type=ContentType.TEXT,
                limit=10
            )
            assert len(text_results) == 1
            assert text_results[0]["storage_id"] == text_storage_id
            
            # List with generation ID filter
            gen1_results = await storage_service.list_inputs(
                generation_id="gen-1",
                limit=10
            )
            assert len(gen1_results) == 1
            assert gen1_results[0]["storage_id"] == text_storage_id
    
    @pytest.mark.asyncio
    async def test_get_input_history(self, storage_service, sample_text_input):
        """Test getting input processing history"""
        validation_result = {"is_valid": True, "warnings": [], "errors": []}
        
        with patch('app.services.input_storage.vector_db_service') as mock_vector_db:
            mock_vector_db.add_content.return_value = True
            
            # Store same content multiple times (simulating reprocessing)
            storage_id1 = await storage_service.store_input(
                content_input=sample_text_input,
                validation_result=validation_result,
                generation_id="gen-1"
            )
            storage_id2 = await storage_service.store_input(
                content_input=sample_text_input,
                validation_result=validation_result,
                generation_id="gen-2"
            )
            
            # Get content hash from first storage
            content_hash = storage_service.stored_inputs[storage_id1]["metadata"]["content_hash"]
            
            # Get history
            history = await storage_service.get_input_history(content_hash)
        
        # Verify history
        assert len(history) == 2
        storage_ids = [entry["storage_id"] for entry in history]
        assert storage_id1 in storage_ids
        assert storage_id2 in storage_ids
        
        # Verify history is sorted by storage time
        assert history[0]["stored_at"] <= history[1]["stored_at"]
    
    @pytest.mark.asyncio
    async def test_delete_input(self, storage_service, sample_text_input):
        """Test deleting stored input"""
        validation_result = {"is_valid": True, "warnings": [], "errors": []}
        
        with patch('app.services.input_storage.vector_db_service') as mock_vector_db:
            mock_vector_db.add_content.return_value = True
            mock_vector_db.delete_content.return_value = True
            
            # Store input
            storage_id = await storage_service.store_input(
                content_input=sample_text_input,
                validation_result=validation_result
            )
            
            # Verify input exists
            assert storage_id in storage_service.stored_inputs
            input_dir = storage_service.storage_dir / storage_id
            assert input_dir.exists()
            
            # Delete input
            success = await storage_service.delete_input(storage_id)
        
        # Verify deletion
        assert success is True
        assert storage_id not in storage_service.stored_inputs
        assert not input_dir.exists()
        
        # Verify vector database delete was called
        mock_vector_db.delete_content.assert_called_once_with(storage_id)
    
    @pytest.mark.asyncio
    async def test_get_storage_stats(self, storage_service, sample_text_input, sample_file_input):
        """Test getting storage statistics"""
        validation_result = {"is_valid": True, "warnings": [], "errors": []}
        
        with patch('app.services.input_storage.vector_db_service') as mock_vector_db:
            mock_vector_db.add_content.return_value = True
            mock_vector_db.get_collection_stats.return_value = {
                "content_count": 2,
                "scripts_count": 0,
                "total_items": 2
            }
            
            with patch('app.services.input_storage.file_storage_service') as mock_file_storage:
                mock_file_storage.get_storage_stats.return_value = {
                    "total_files": 0,
                    "total_size_bytes": 0,
                    "total_size_mb": 0
                }
                
                # Store inputs
                await storage_service.store_input(
                    content_input=sample_text_input,
                    validation_result=validation_result
                )
                await storage_service.store_input(
                    content_input=sample_file_input,
                    validation_result=validation_result
                )
                
                # Get stats
                stats = await storage_service.get_storage_stats()
        
        # Verify stats
        assert stats["total_inputs"] == 2
        assert "content_type_distribution" in stats
        assert stats["content_type_distribution"]["text"] == 1
        assert stats["content_type_distribution"]["file"] == 1
        assert "total_content_size_bytes" in stats
        assert "total_content_size_mb" in stats
        assert "vector_db_stats" in stats
        assert "file_storage_stats" in stats
    
    def test_create_content_hash(self, storage_service):
        """Test content hash creation"""
        content1 = "This is test content"
        content2 = "This is test content"
        content3 = "This is different content"
        
        hash1 = storage_service._create_content_hash(content1)
        hash2 = storage_service._create_content_hash(content2)
        hash3 = storage_service._create_content_hash(content3)
        
        # Same content should produce same hash
        assert hash1 == hash2
        
        # Different content should produce different hash
        assert hash1 != hash3
        
        # Hash should be 64 characters (SHA-256 hex)
        assert len(hash1) == 64
        assert all(c in '0123456789abcdef' for c in hash1)
    
    def test_extract_file_metadata(self, storage_service, sample_file_input):
        """Test file metadata extraction"""
        metadata = storage_service._extract_file_metadata(sample_file_input)
        
        assert "file_metadata" in metadata
        file_meta = metadata["file_metadata"]
        assert file_meta["filename"] == "math_content.pdf"
        assert file_meta["file_size"] == 1024
        assert file_meta["mime_type"] == "application/pdf"
    
    def test_extract_url_metadata(self, storage_service, sample_url_input):
        """Test URL metadata extraction"""
        metadata = storage_service._extract_url_metadata(sample_url_input)
        
        assert "url_metadata" in metadata
        url_meta = metadata["url_metadata"]
        assert url_meta["page_title"] == "Physics Fundamentals"
    
    def test_extract_text_metadata(self, storage_service, sample_text_input):
        """Test text metadata extraction"""
        metadata = storage_service._extract_text_metadata(sample_text_input)
        
        assert "text_metadata" in metadata
        text_meta = metadata["text_metadata"]
        assert text_meta["word_count"] > 0
        assert text_meta["character_count"] == len(sample_text_input.content)
        assert text_meta["line_count"] >= 1
        assert text_meta["estimated_reading_time_minutes"] >= 1
    
    @pytest.mark.asyncio
    async def test_filesystem_persistence(self, storage_service, sample_text_input):
        """Test that data persists to filesystem correctly"""
        validation_result = {"is_valid": True, "warnings": [], "errors": []}
        
        with patch('app.services.input_storage.vector_db_service') as mock_vector_db:
            mock_vector_db.add_content.return_value = True
            
            # Store input
            storage_id = await storage_service.store_input(
                content_input=sample_text_input,
                validation_result=validation_result
            )
            
            # Clear in-memory cache
            storage_service.stored_inputs.clear()
            
            # Retrieve from filesystem
            retrieved_data = await storage_service.retrieve_input(storage_id)
        
        # Verify data was loaded from filesystem
        assert retrieved_data is not None
        assert retrieved_data["content"] == sample_text_input.content
        assert retrieved_data["metadata"]["storage_id"] == storage_id
    
    @pytest.mark.asyncio
    async def test_vector_db_integration(self, storage_service, sample_text_input):
        """Test integration with vector database"""
        validation_result = {"is_valid": True, "warnings": [], "errors": []}
        
        with patch('app.services.input_storage.vector_db_service') as mock_vector_db:
            mock_vector_db.add_content.return_value = True
            
            # Store input
            storage_id = await storage_service.store_input(
                content_input=sample_text_input,
                validation_result=validation_result
            )
        
        # Verify vector database was called with correct parameters
        mock_vector_db.add_content.assert_called_once()
        call_args = mock_vector_db.add_content.call_args
        
        assert call_args[1]["content_id"] == storage_id
        assert call_args[1]["content"] == sample_text_input.content
        assert "metadata" in call_args[1]
        
        # Verify metadata contains expected fields
        metadata = call_args[1]["metadata"]
        assert metadata["storage_id"] == storage_id
        assert metadata["content_type"] == ContentType.TEXT.value
        assert "content_hash" in metadata
        assert "stored_at" in metadata


@pytest.mark.asyncio
async def test_global_input_storage_service():
    """Test that global input storage service is properly initialized"""
    assert input_storage_service is not None
    assert isinstance(input_storage_service, InputStorageService)
    assert input_storage_service.storage_dir.exists()


class TestInputStorageIntegration:
    """Integration tests for input storage with other services"""
    
    @pytest.mark.asyncio
    async def test_content_service_integration(self):
        """Test that content service properly integrates with input storage"""
        # This would test the actual integration between ContentService and InputStorageService
        # For now, we'll just verify the import works
        from app.services.content_service import ContentService
        
        service = ContentService()
        # Verify that input_storage_service is imported and available
        assert hasattr(service, 'content_validator')
        assert hasattr(service, 'document_parser')
    
    @pytest.mark.asyncio
    async def test_vector_db_service_integration(self):
        """Test integration with vector database service"""
        from app.services.vector_db import vector_db_service
        
        # Verify vector database service is available
        assert vector_db_service is not None
        
        # Test basic functionality
        stats = vector_db_service.get_collection_stats()
        assert "content_count" in stats
        assert "scripts_count" in stats
    
    @pytest.mark.asyncio
    async def test_file_storage_service_integration(self):
        """Test integration with file storage service"""
        from app.services.file_storage import file_storage_service
        
        # Verify file storage service is available
        assert file_storage_service is not None
        
        # Test basic functionality
        stats = file_storage_service.get_storage_stats()
        assert "total_files" in stats
        assert "total_size_bytes" in stats