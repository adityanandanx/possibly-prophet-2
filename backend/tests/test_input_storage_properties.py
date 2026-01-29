"""
Property-based tests for input storage service
**Validates: Requirements 1.7**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

def create_mock_kb_service():
    """Create a properly configured mock for the AWS Knowledge Base service"""
    mock_kb = MagicMock()
    mock_kb.add_document = AsyncMock(return_value={"success": True})
    mock_kb.delete_document = AsyncMock(return_value={"success": True})
    mock_kb.retrieve = AsyncMock(return_value={"success": True, "results": []})
    mock_kb.get_knowledge_base_info = AsyncMock(return_value={"knowledge_base_id": "test-kb"})
    return mock_kb


from datetime import datetime

from app.services.input_storage import InputStorageService
from app.models.content import ContentInput, ContentType


# Strategies for generating test data
content_types = st.sampled_from([ContentType.TEXT, ContentType.FILE, ContentType.URL])

text_content = st.text(min_size=10, max_size=1000).filter(lambda x: x.strip())

file_metadata = st.fixed_dictionaries({
    "filename": st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    "file_size": st.integers(min_value=1, max_value=10000000),
    "mime_type": st.sampled_from(["application/pdf", "text/plain", "application/msword"])
})

url_metadata = st.fixed_dictionaries({
    "source_url": st.text(min_size=10, max_size=100).filter(lambda x: x.startswith("http")),
    "page_title": st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
})

generation_ids = st.one_of(st.none(), st.text(min_size=5, max_size=50))

validation_results = st.fixed_dictionaries({
    "is_valid": st.booleans(),
    "warnings": st.lists(st.text(min_size=1, max_size=100), max_size=5),
    "errors": st.lists(st.text(min_size=1, max_size=100), max_size=5),
    "metadata": st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=50), max_size=5)
})

processing_metadata = st.fixed_dictionaries({
    "status": st.sampled_from(["processing", "completed", "failed"]),
    "start_time": st.text(min_size=10, max_size=30),
    "processing_notes": st.text(min_size=0, max_size=200)
})


@st.composite
def content_inputs(draw):
    """Generate ContentInput objects with appropriate metadata"""
    content_type = draw(content_types)
    content = draw(text_content)
    
    if content_type == ContentType.FILE:
        metadata = draw(file_metadata)
    elif content_type == ContentType.URL:
        metadata = draw(url_metadata)
    else:
        metadata = draw(st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=50), max_size=3))
    
    return ContentInput(
        content_type=content_type,
        content=content,
        metadata=metadata
    )


class TestInputStorageProperties:
    """Property-based tests for input storage service"""
    
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
        service.stored_inputs = {}
        return service
    
    @given(
        content_input=content_inputs(),
        validation_result=validation_results,
        processing_meta=processing_metadata,
        generation_id=generation_ids
    )
    @settings(max_examples=50, deadline=5000)
    @pytest.mark.asyncio
    async def test_storage_persistence_property(
        self, storage_service, content_input, validation_result, processing_meta, generation_id
    ):
        """
        Property: All stored inputs must be retrievable with identical content
        **Validates: Requirements 1.7 - Storage and Retrieval**
        """
        mock_kb = create_mock_kb_service()
        storage_service._knowledge_base = mock_kb
            
            
            # Store input
            storage_id = await storage_service.store_input(
                content_input=content_input,
                validation_result=validation_result,
                processing_metadata=processing_meta,
                generation_id=generation_id
            )
            
            # Retrieve input
            retrieved_data = await storage_service.retrieve_input(storage_id)
        
        # Property assertions
        assert retrieved_data is not None, "Stored input must be retrievable"
        assert retrieved_data["content"] == content_input.content, "Retrieved content must match stored content"
        assert retrieved_data["metadata"]["storage_id"] == storage_id, "Storage ID must be preserved"
        assert retrieved_data["metadata"]["content_type"] == content_input.content_type.value, "Content type must be preserved"
        assert retrieved_data["metadata"]["generation_id"] == generation_id, "Generation ID must be preserved"
    
    @given(
        content_input=content_inputs(),
        validation_result=validation_results
    )
    @settings(max_examples=30, deadline=5000)
    @pytest.mark.asyncio
    async def test_content_hash_consistency_property(self, storage_service, content_input, validation_result):
        """
        Property: Identical content must produce identical content hashes
        **Validates: Requirements 1.7 - Content versioning tracks modifications**
        """
        mock_kb = create_mock_kb_service()
        storage_service._knowledge_base = mock_kb
            
            
            # Store same content twice
            storage_id1 = await storage_service.store_input(
                content_input=content_input,
                validation_result=validation_result
            )
            storage_id2 = await storage_service.store_input(
                content_input=content_input,
                validation_result=validation_result
            )
            
            # Retrieve both
            data1 = await storage_service.retrieve_input(storage_id1)
            data2 = await storage_service.retrieve_input(storage_id2)
        
        # Property assertions
        assert data1["metadata"]["content_hash"] == data2["metadata"]["content_hash"], \
            "Identical content must produce identical hashes"
        
        # Verify history tracking works
        content_hash = data1["metadata"]["content_hash"]
        history = await storage_service.get_input_history(content_hash)
        assert len(history) == 2, "History must track all instances of same content"
        
        storage_ids_in_history = {entry["storage_id"] for entry in history}
        assert storage_id1 in storage_ids_in_history, "First storage must be in history"
        assert storage_id2 in storage_ids_in_history, "Second storage must be in history"
    
    @given(
        content_inputs_list=st.lists(content_inputs(), min_size=1, max_size=10),
        search_query=st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
    )
    @settings(max_examples=20, deadline=10000)
    @pytest.mark.asyncio
    async def test_search_completeness_property(self, storage_service, content_inputs_list, search_query):
        """
        Property: Search must return all relevant stored inputs
        **Validates: Requirements 1.7 - Search functionality allows finding relevant past content**
        """
        stored_ids = []
        
        mock_kb = create_mock_kb_service()
        storage_service._knowledge_base = mock_kb
            
            
            # Store all inputs
            for content_input in content_inputs_list:
                storage_id = await storage_service.store_input(
                    content_input=content_input,
                    validation_result={"is_valid": True, "warnings": [], "errors": [], "metadata": {}}
                )
                stored_ids.append(storage_id)
            
            # Mock search to return all stored inputs (simulating perfect match)
            mock_search_results = []
            for i, storage_id in enumerate(stored_ids):
                mock_search_results.append({
                    "id": storage_id,
                    "content": content_inputs_list[i].content,
                    "metadata": {"content_type": content_inputs_list[i].content_type.value},
                    "distance": 0.1
                })
            
            storage_service._knowledge_base.retrieve = AsyncMock(return_value={"success": True, "results": mock_search_results})
            
            # Perform search
            search_results = await storage_service.search_inputs(
                query=search_query,
                limit=len(stored_ids)
            )
        
        # Property assertions
        assert len(search_results) == len(stored_ids), "Search must return all stored inputs when limit allows"
        
        returned_storage_ids = {result["storage_id"] for result in search_results}
        for storage_id in stored_ids:
            assert storage_id in returned_storage_ids, f"Search must include stored input {storage_id}"
        
        # Verify each result has required fields
        for result in search_results:
            assert "storage_id" in result, "Search results must include storage_id"
            assert "content" in result, "Search results must include content"
            assert "metadata" in result, "Search results must include metadata"
            assert "similarity_score" in result, "Search results must include similarity_score"
    
    @given(
        content_input=content_inputs(),
        content_type_filter=st.one_of(st.none(), content_types),
        generation_id_filter=st.one_of(st.none(), st.text(min_size=5, max_size=50))
    )
    @settings(max_examples=30, deadline=5000)
    @pytest.mark.asyncio
    async def test_filtering_correctness_property(
        self, storage_service, content_input, content_type_filter, generation_id_filter
    ):
        """
        Property: Filtering must only return inputs matching the specified criteria
        **Validates: Requirements 1.7 - Search functionality with filters**
        """
        mock_kb = create_mock_kb_service()
        storage_service._knowledge_base = mock_kb
            
            
            # Store input
            storage_id = await storage_service.store_input(
                content_input=content_input,
                validation_result={"is_valid": True, "warnings": [], "errors": [], "metadata": {}},
                generation_id=generation_id_filter  # Use filter value as actual generation_id
            )
            
            # List with filters
            results = await storage_service.list_inputs(
                content_type=content_type_filter,
                generation_id=generation_id_filter,
                limit=100
            )
        
        # Property assertions
        if content_type_filter is not None and content_type_filter != content_input.content_type:
            # If filter doesn't match, should return empty
            assert len(results) == 0, "Filter must exclude non-matching content types"
        elif generation_id_filter is not None:
            # If generation_id filter matches, should return the input
            assert len(results) == 1, "Filter must include matching generation IDs"
            assert results[0]["storage_id"] == storage_id, "Returned input must be the stored one"
            assert results[0]["content_type"] == content_input.content_type.value, "Content type must match"
            assert results[0]["generation_id"] == generation_id_filter, "Generation ID must match filter"
        else:
            # No filters, should return the input
            assert len(results) >= 1, "No filters should return all inputs"
            storage_ids = [r["storage_id"] for r in results]
            assert storage_id in storage_ids, "Stored input must be in unfiltered results"
    
    @given(
        content_input=content_inputs(),
        validation_result=validation_results
    )
    @settings(max_examples=30, deadline=5000)
    @pytest.mark.asyncio
    async def test_deletion_completeness_property(self, storage_service, content_input, validation_result):
        """
        Property: Deleted inputs must be completely removed from all storage systems
        **Validates: Requirements 1.7 - Content management and cleanup**
        """
        mock_kb = create_mock_kb_service()
        storage_service._knowledge_base = mock_kb
            
            
            
            # Store input
            storage_id = await storage_service.store_input(
                content_input=content_input,
                validation_result=validation_result
            )
            
            # Verify input exists
            retrieved_before = await storage_service.retrieve_input(storage_id)
            assert retrieved_before is not None, "Input must exist before deletion"
            
            # Delete input
            deletion_success = await storage_service.delete_input(storage_id)
            assert deletion_success, "Deletion must succeed"
            
            # Verify complete removal
            retrieved_after = await storage_service.retrieve_input(storage_id)
            assert retrieved_after is None, "Input must not exist after deletion"
            
            # Verify removal from in-memory storage
            assert storage_id not in storage_service.stored_inputs, "Input must be removed from memory"
            
            # Verify filesystem cleanup
            input_dir = storage_service.storage_dir / storage_id
            assert not input_dir.exists(), "Input directory must be removed from filesystem"
            
            # Verify vector database cleanup was called
            storage_service._knowledge_base.delete_document.assert_called_once()
    
    @given(
        content_inputs_list=st.lists(content_inputs(), min_size=2, max_size=5)
    )
    @settings(max_examples=20, deadline=10000)
    @pytest.mark.asyncio
    async def test_statistics_accuracy_property(self, storage_service, content_inputs_list):
        """
        Property: Storage statistics must accurately reflect stored data
        **Validates: Requirements 1.7 - Storage monitoring and management**
        """
        mock_kb = create_mock_kb_service()
        storage_service._knowledge_base = mock_kb
            
            mock_kb_service.get_collection_stats.return_value = {
                "content_count": len(content_inputs_list),
                "scripts_count": 0,
                "total_items": len(content_inputs_list)
            }
            
            with patch('app.services.input_storage.file_storage_service') as mock_file_storage:
                mock_file_storage.get_storage_stats.return_value = {
                    "total_files": 0,
                    "total_size_bytes": 0,
                    "total_size_mb": 0
                }
                
                # Store all inputs
                stored_ids = []
                expected_type_counts = {}
                expected_total_size = 0
                
                for content_input in content_inputs_list:
                    storage_id = await storage_service.store_input(
                        content_input=content_input,
                        validation_result={"is_valid": True, "warnings": [], "errors": [], "metadata": {}}
                    )
                    stored_ids.append(storage_id)
                    
                    # Track expected statistics
                    content_type = content_input.content_type.value
                    expected_type_counts[content_type] = expected_type_counts.get(content_type, 0) + 1
                    expected_total_size += len(content_input.content)
                
                # Get statistics
                stats = await storage_service.get_storage_stats()
        
        # Property assertions
        assert stats["total_inputs"] == len(content_inputs_list), \
            "Total inputs count must match number of stored inputs"
        
        assert stats["content_type_distribution"] == expected_type_counts, \
            "Content type distribution must accurately reflect stored inputs"
        
        assert stats["total_content_size_bytes"] == expected_total_size, \
            "Total content size must match sum of all content lengths"
        
        assert stats["total_content_size_mb"] == round(expected_total_size / (1024 * 1024), 2), \
            "Content size in MB must be correctly calculated"
        
        assert "vector_db_stats" in stats, "Statistics must include vector database stats"
        assert "file_storage_stats" in stats, "Statistics must include file storage stats"
    
    @given(content_input=content_inputs())
    @settings(max_examples=50, deadline=3000)
    @pytest.mark.asyncio
    async def test_metadata_preservation_property(self, storage_service, content_input):
        """
        Property: All metadata must be preserved during storage and retrieval
        **Validates: Requirements 1.7 - Metadata storage and retrieval**
        """
        validation_result = {
            "is_valid": True,
            "warnings": ["test warning"],
            "errors": [],
            "metadata": {"test_key": "test_value"}
        }
        
        processing_metadata = {
            "status": "completed",
            "processing_time": 1.5,
            "notes": "test processing"
        }
        
        generation_id = "test-gen-123"
        
        mock_kb = create_mock_kb_service()
        storage_service._knowledge_base = mock_kb
            
            
            # Store input
            storage_id = await storage_service.store_input(
                content_input=content_input,
                validation_result=validation_result,
                processing_metadata=processing_metadata,
                generation_id=generation_id
            )
            
            # Retrieve input
            retrieved_data = await storage_service.retrieve_input(storage_id)
        
        # Property assertions - verify all metadata is preserved
        metadata = retrieved_data["metadata"]
        
        assert metadata["storage_id"] == storage_id, "Storage ID must be preserved"
        assert metadata["content_type"] == content_input.content_type.value, "Content type must be preserved"
        assert metadata["generation_id"] == generation_id, "Generation ID must be preserved"
        assert metadata["content_length"] == len(content_input.content), "Content length must be accurate"
        assert "content_hash" in metadata, "Content hash must be generated and stored"
        assert "stored_at" in metadata, "Storage timestamp must be recorded"
        assert "storage_version" in metadata, "Storage version must be recorded"
        
        # Verify original metadata is preserved
        assert metadata["original_metadata"] == content_input.metadata, "Original metadata must be preserved"
        
        # Verify validation result is preserved
        assert metadata["validation_result"] == validation_result, "Validation result must be preserved"
        
        # Verify processing metadata is preserved
        assert metadata["processing_metadata"] == processing_metadata, "Processing metadata must be preserved"
        
        # Verify type-specific metadata is extracted
        if content_input.content_type == ContentType.FILE:
            assert "file_metadata" in metadata, "File metadata must be extracted for file inputs"
        elif content_input.content_type == ContentType.URL:
            assert "url_metadata" in metadata, "URL metadata must be extracted for URL inputs"
        elif content_input.content_type == ContentType.TEXT:
            assert "text_metadata" in metadata, "Text metadata must be extracted for text inputs"


class InputStorageStateMachine(RuleBasedStateMachine):
    """
    Stateful property-based testing for input storage service
    **Validates: Requirements 1.7 - Complex storage operations and state consistency**
    """
    
    def __init__(self):
        super().__init__()
        self.temp_dir = None
        self.storage_service = None
        self.stored_inputs = {}  # Track what we've stored
        self.deleted_inputs = set()  # Track what we've deleted
    
    @initialize()
    def setup(self):
        """Initialize the storage service for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_service = InputStorageService()
        self.storage_service.storage_dir = Path(self.temp_dir) / "input_storage"
        self.storage_service.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_service.stored_inputs = {}
    
    def teardown(self):
        """Clean up after testing"""
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
    
    @rule(
        content_input=content_inputs(),
        generation_id=st.one_of(st.none(), st.text(min_size=5, max_size=20))
    )
    def store_input(self, content_input, generation_id):
        """Store an input and track it"""
        mock_kb = create_mock_kb_service()
        storage_service._knowledge_base = mock_kb
            
            
            # Run the async operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                storage_id = loop.run_until_complete(
                    self.storage_service.store_input(
                        content_input=content_input,
                        validation_result={"is_valid": True, "warnings": [], "errors": [], "metadata": {}},
                        generation_id=generation_id
                    )
                )
                
                # Track the stored input
                self.stored_inputs[storage_id] = {
                    "content": content_input.content,
                    "content_type": content_input.content_type,
                    "generation_id": generation_id
                }
            finally:
                loop.close()
    
    @rule(storage_id=st.sampled_from([]))  # Will be populated by stored inputs
    def retrieve_input(self, storage_id):
        """Retrieve a stored input and verify it matches expectations"""
        assume(storage_id in self.stored_inputs)
        assume(storage_id not in self.deleted_inputs)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            retrieved_data = loop.run_until_complete(
                self.storage_service.retrieve_input(storage_id)
            )
            
            # Verify the retrieved data matches what we stored
            expected = self.stored_inputs[storage_id]
            assert retrieved_data is not None
            assert retrieved_data["content"] == expected["content"]
            assert retrieved_data["metadata"]["content_type"] == expected["content_type"].value
            assert retrieved_data["metadata"]["generation_id"] == expected["generation_id"]
        finally:
            loop.close()
    
    @rule(storage_id=st.sampled_from([]))  # Will be populated by stored inputs
    def delete_input(self, storage_id):
        """Delete a stored input and track the deletion"""
        assume(storage_id in self.stored_inputs)
        assume(storage_id not in self.deleted_inputs)
        
        mock_kb = create_mock_kb_service()
        storage_service._knowledge_base = mock_kb
            
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(
                    self.storage_service.delete_input(storage_id)
                )
                
                assert success, "Deletion should succeed for existing inputs"
                self.deleted_inputs.add(storage_id)
            finally:
                loop.close()
    
    @invariant()
    def storage_consistency(self):
        """Verify storage consistency invariants"""
        # All stored inputs (not deleted) should be retrievable
        for storage_id in self.stored_inputs:
            if storage_id not in self.deleted_inputs:
                assert storage_id in self.storage_service.stored_inputs, \
                    f"Stored input {storage_id} should be in service memory"
        
        # Deleted inputs should not be in service memory
        for storage_id in self.deleted_inputs:
            assert storage_id not in self.storage_service.stored_inputs, \
                f"Deleted input {storage_id} should not be in service memory"
    
    @invariant()
    def filesystem_consistency(self):
        """Verify filesystem consistency invariants"""
        # Check that filesystem matches in-memory state
        for storage_id in self.storage_service.stored_inputs:
            input_dir = self.storage_service.storage_dir / storage_id
            assert input_dir.exists(), f"Directory for {storage_id} should exist"
            assert (input_dir / "content.txt").exists(), f"Content file for {storage_id} should exist"
            assert (input_dir / "metadata.json").exists(), f"Metadata file for {storage_id} should exist"


# Run the stateful test
TestInputStorageStateMachine = InputStorageStateMachine.TestCase