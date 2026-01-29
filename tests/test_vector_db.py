"""
Tests for vector database service
"""

import pytest
from unittest.mock import Mock, patch
from app.services.vector_db import VectorDBService
from app.models.content import EducationalScript, LearningObjective, ContentSection, BloomLevel

@pytest.mark.unit
def test_vector_db_service_initialization():
    """Test that VectorDBService can be initialized"""
    # This test just verifies the service can be created
    # without actually connecting to ChromaDB
    with patch('chromadb.PersistentClient') as mock_client:
        mock_collection = Mock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection
        
        service = VectorDBService()
        assert service is not None

@pytest.mark.unit
def test_create_searchable_text():
    """Test creating searchable text from educational script"""
    with patch('chromadb.PersistentClient'):
        service = VectorDBService()
        
        script = EducationalScript(
            title="Photosynthesis Basics",
            description="Introduction to photosynthesis process",
            learning_objectives=[
                LearningObjective(
                    objective="Understand photosynthesis process",
                    bloom_level=BloomLevel.UNDERSTAND
                )
            ],
            sections=[
                ContentSection(
                    title="What is Photosynthesis?",
                    content="Photosynthesis converts sunlight to energy",
                    duration_minutes=10
                )
            ],
            tags=["biology", "plants", "energy"],
            prerequisites=["basic chemistry"]
        )
        
        searchable_text = service._create_searchable_text(script)
        
        # Verify all important content is included
        assert "Photosynthesis Basics" in searchable_text
        assert "Introduction to photosynthesis process" in searchable_text
        assert "Understand photosynthesis process" in searchable_text
        assert "What is Photosynthesis?" in searchable_text
        assert "Photosynthesis converts sunlight to energy" in searchable_text
        assert "biology" in searchable_text
        assert "plants" in searchable_text
        assert "energy" in searchable_text
        assert "basic chemistry" in searchable_text

@pytest.mark.unit
def test_add_content_success():
    """Test successful content addition"""
    with patch('chromadb.PersistentClient') as mock_client:
        mock_collection = Mock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection
        
        service = VectorDBService()
        service.content_collection = mock_collection
        
        # Mock successful add
        mock_collection.add.return_value = None
        
        result = service.add_content(
            "test_id",
            "test content",
            {"topic": "test"}
        )
        
        assert result is True
        mock_collection.add.assert_called_once()

@pytest.mark.unit
def test_add_content_failure():
    """Test content addition failure handling"""
    with patch('chromadb.PersistentClient') as mock_client:
        mock_collection = Mock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection
        
        service = VectorDBService()
        service.content_collection = mock_collection
        
        # Mock add failure
        mock_collection.add.side_effect = Exception("Database error")
        
        result = service.add_content(
            "test_id",
            "test content",
            {"topic": "test"}
        )
        
        assert result is False

@pytest.mark.unit
def test_search_content():
    """Test content search functionality"""
    with patch('chromadb.PersistentClient') as mock_client:
        mock_collection = Mock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection
        
        service = VectorDBService()
        service.content_collection = mock_collection
        
        # Mock search results
        mock_collection.query.return_value = {
            'documents': [['test document']],
            'ids': [['test_id']],
            'metadatas': [[{'topic': 'test'}]],
            'distances': [[0.5]]
        }
        
        results = service.search_content("test query")
        
        assert len(results) == 1
        assert results[0]['id'] == 'test_id'
        assert results[0]['content'] == 'test document'
        assert results[0]['metadata']['topic'] == 'test'
        assert results[0]['distance'] == 0.5