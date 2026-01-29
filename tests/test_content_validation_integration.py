"""
Integration tests for content validation in the content service
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi import UploadFile
from io import BytesIO

from app.services.content_service import ContentService
from app.models.content import ContentInput

class TestContentServiceValidation:
    """Integration tests for content validation in ContentService"""
    
    @pytest.fixture
    def content_service(self):
        """Create a ContentService instance for testing"""
        return ContentService()
    
    @pytest.fixture
    def sample_educational_text(self):
        """Sample educational text for testing"""
        return """
        Machine Learning is a subset of artificial intelligence that enables computers
        to learn and make decisions without being explicitly programmed. Key concepts include:
        
        1. Supervised Learning - learning from labeled examples
        2. Unsupervised Learning - finding patterns in unlabeled data
        3. Neural Networks - computational models inspired by the brain
        4. Training Data - the dataset used to teach the algorithm
        
        Students should understand that machine learning algorithms improve their
        performance through experience and data analysis. This field has applications
        in image recognition, natural language processing, and predictive analytics.
        """
    
    @pytest.fixture
    def sample_invalid_text(self):
        """Sample invalid text for testing"""
        return "<script>alert('malicious')</script>Short bad content."

class TestTextContentValidation:
    """Test text content validation integration"""
    
    @pytest.mark.asyncio
    async def test_generate_from_text_valid_content(self, content_service, sample_educational_text):
        """Test text generation with valid educational content"""
        result = await content_service.generate_from_text(
            content=sample_educational_text,
            topic="Machine Learning Basics",
            difficulty_level="intermediate",
            target_audience="computer science students"
        )
        
        assert result["status"] == "completed"
        assert "generation_id" in result
        assert "educational_script" in result
        assert "validation_warnings" in result
        assert "content_metadata" in result
        
        # Check that content metadata includes quality metrics
        metadata = result["content_metadata"]
        assert "quality_score" in metadata
        assert "educational_score" in metadata
        assert "word_count" in metadata
        assert metadata["quality_score"] > 0.3
    
    @pytest.mark.asyncio
    async def test_generate_from_text_invalid_content(self, content_service, sample_invalid_text):
        """Test text generation with invalid content"""
        result = await content_service.generate_from_text(
            content=sample_invalid_text,
            topic="Test Topic"
        )
        
        assert result["status"] == "failed"
        assert "validation_errors" in result
        assert len(result["validation_errors"]) > 0
        assert any("malicious" in error.lower() for error in result["validation_errors"])
    
    @pytest.mark.asyncio
    async def test_generate_from_text_short_content(self, content_service):
        """Test text generation with content that's too short"""
        result = await content_service.generate_from_text(
            content="Short",
            topic="Test Topic"
        )
        
        assert result["status"] == "failed"
        assert "validation_errors" in result
        assert any("too short" in error.lower() for error in result["validation_errors"])
    
    @pytest.mark.asyncio
    async def test_generate_from_text_with_warnings(self, content_service):
        """Test text generation with content that has warnings"""
        low_quality_content = """
        This is some content that might have quality issues.
        It's not very educational and lacks structure.
        No clear learning objectives or detailed explanations.
        """ * 5  # Make it long enough to pass length validation
        
        result = await content_service.generate_from_text(
            content=low_quality_content,
            topic="Test Topic"
        )
        
        assert result["status"] == "completed"
        assert "validation_warnings" in result
        assert len(result["validation_warnings"]) > 0

class TestMultiInputValidation:
    """Test multi-input content validation integration"""
    
    @pytest.mark.asyncio
    async def test_generate_from_inputs_valid_content(self, content_service, sample_educational_text):
        """Test multi-input generation with valid content"""
        inputs = [
            ContentInput(
                content_type="text",
                content=sample_educational_text,
                metadata={"source": "textbook"}
            ),
            ContentInput(
                content_type="text", 
                content="Additional educational content about algorithms and data structures.",
                metadata={"source": "lecture_notes"}
            )
        ]
        
        result = await content_service.generate_from_inputs(
            inputs=inputs,
            topic="Computer Science Fundamentals",
            difficulty_level="intermediate"
        )
        
        assert result["status"] == "completed"
        assert "validation_warnings" in result
        assert "content_metadata" in result
        
        # Should have combined metadata from all inputs
        metadata = result["content_metadata"]
        assert "quality_score" in metadata
        assert "educational_score" in metadata
    
    @pytest.mark.asyncio
    async def test_generate_from_inputs_mixed_validity(self, content_service, sample_educational_text, sample_invalid_text):
        """Test multi-input generation with mixed content validity"""
        inputs = [
            ContentInput(
                content_type="text",
                content=sample_educational_text,
                metadata={"source": "good_content"}
            ),
            ContentInput(
                content_type="text",
                content=sample_invalid_text,
                metadata={"source": "bad_content"}
            )
        ]
        
        result = await content_service.generate_from_inputs(
            inputs=inputs,
            topic="Test Topic"
        )
        
        assert result["status"] == "failed"
        assert "validation_errors" in result
        assert "failed_input_index" in result
        assert result["failed_input_index"] == 1  # Second input failed
    
    @pytest.mark.asyncio
    async def test_generate_from_inputs_empty_after_validation(self, content_service):
        """Test multi-input generation with no valid content after validation"""
        inputs = [
            ContentInput(
                content_type="text",
                content="",  # Empty content
                metadata={"source": "empty"}
            ),
            ContentInput(
                content_type="text",
                content="   ",  # Whitespace only
                metadata={"source": "whitespace"}
            )
        ]
        
        result = await content_service.generate_from_inputs(
            inputs=inputs,
            topic="Test Topic"
        )
        
        assert result["status"] == "failed"
        assert "validation_errors" in result

class TestURLValidation:
    """Test URL content validation integration"""
    
    @pytest.mark.asyncio
    async def test_generate_from_url_valid_url(self, content_service, sample_educational_text):
        """Test URL generation with valid URL and content"""
        with patch.object(content_service, '_scrape_url_content', return_value=sample_educational_text):
            result = await content_service.generate_from_url(
                url="https://example.com/educational-article",
                topic="Educational Content",
                difficulty_level="intermediate"
            )
            
            assert result["status"] == "completed"
            assert "validation_warnings" in result
            assert "content_metadata" in result
            
            # Should have URL-specific metadata
            script = result.get("educational_script", {})
            metadata = script.get("metadata", {})
            assert "source_url" in metadata
            assert metadata["source_url"] == "https://example.com/educational-article"
    
    @pytest.mark.asyncio
    async def test_generate_from_url_invalid_url_format(self, content_service):
        """Test URL generation with invalid URL format"""
        result = await content_service.generate_from_url(
            url="not-a-valid-url",
            topic="Test Topic"
        )
        
        assert result["status"] == "failed"
        assert "validation_errors" in result
        assert any("protocol" in error.lower() or "format" in error.lower() 
                  for error in result["validation_errors"])
    
    @pytest.mark.asyncio
    async def test_generate_from_url_invalid_scraped_content(self, content_service, sample_invalid_text):
        """Test URL generation with invalid scraped content"""
        with patch.object(content_service, '_scrape_url_content', return_value=sample_invalid_text):
            result = await content_service.generate_from_url(
                url="https://example.com/malicious-content",
                topic="Test Topic"
            )
            
            assert result["status"] == "failed"
            assert "validation_errors" in result
    
    @pytest.mark.asyncio
    async def test_generate_from_url_empty_scraped_content(self, content_service):
        """Test URL generation with empty scraped content"""
        with patch.object(content_service, '_scrape_url_content', return_value=""):
            result = await content_service.generate_from_url(
                url="https://example.com/empty-page",
                topic="Test Topic"
            )
            
            assert result["status"] == "failed"
            assert "No content could be extracted" in result["error_message"]

class TestFileValidation:
    """Test file content validation integration"""
    
    @pytest.mark.asyncio
    async def test_generate_from_file_valid_text_file(self, content_service, sample_educational_text):
        """Test file generation with valid text file"""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_educational_text)
            temp_path = f.name
        
        try:
            # Create UploadFile mock
            file_content = sample_educational_text.encode('utf-8')
            upload_file = UploadFile(
                filename="educational_content.txt",
                file=BytesIO(file_content),
                size=len(file_content)
            )
            
            # Mock the document parser to return our content
            with patch.object(content_service.document_parser, 'extract_text_from_file') as mock_extract:
                mock_extract.return_value = {
                    "text": sample_educational_text,
                    "metadata": {
                        "filename": "educational_content.txt",
                        "file_type": "text",
                        "page_count": 1
                    }
                }
                
                result = await content_service.generate_from_file(
                    file=upload_file,
                    topic="Educational File Content",
                    difficulty_level="intermediate"
                )
                
                assert result["status"] == "completed"
                assert "validation_warnings" in result
                assert "content_metadata" in result
                
                # Should have file-specific metadata
                script = result.get("educational_script", {})
                metadata = script.get("metadata", {})
                assert "source_file" in metadata
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_generate_from_file_invalid_content(self, content_service, sample_invalid_text):
        """Test file generation with invalid extracted content"""
        file_content = sample_invalid_text.encode('utf-8')
        upload_file = UploadFile(
            filename="malicious_content.txt",
            file=BytesIO(file_content),
            size=len(file_content)
        )
        
        # Mock the document parser to return malicious content
        with patch.object(content_service.document_parser, 'extract_text_from_file') as mock_extract:
            mock_extract.return_value = {
                "text": sample_invalid_text,
                "metadata": {
                    "filename": "malicious_content.txt",
                    "file_type": "text"
                }
            }
            
            result = await content_service.generate_from_file(
                file=upload_file,
                topic="Test File"
            )
            
            assert result["status"] == "failed"
            assert "validation_errors" in result
    
    @pytest.mark.asyncio
    async def test_generate_from_file_empty_content(self, content_service):
        """Test file generation with empty extracted content"""
        file_content = b"Some binary content"
        upload_file = UploadFile(
            filename="empty_content.txt",
            file=BytesIO(file_content),
            size=len(file_content)
        )
        
        # Mock the document parser to return empty content
        with patch.object(content_service.document_parser, 'extract_text_from_file') as mock_extract:
            mock_extract.return_value = {
                "text": "",
                "metadata": {
                    "filename": "empty_content.txt",
                    "file_type": "text"
                }
            }
            
            result = await content_service.generate_from_file(
                file=upload_file,
                topic="Test File"
            )
            
            assert result["status"] == "failed"
            assert "validation_errors" in result

class TestValidationMetadataPropagation:
    """Test that validation metadata is properly propagated through the system"""
    
    @pytest.mark.asyncio
    async def test_validation_metadata_in_response(self, content_service, sample_educational_text):
        """Test that validation metadata is included in responses"""
        result = await content_service.generate_from_text(
            content=sample_educational_text,
            topic="Test Topic"
        )
        
        assert result["status"] == "completed"
        assert "content_metadata" in result
        
        metadata = result["content_metadata"]
        
        # Should include quality metrics
        assert "quality_score" in metadata
        assert "educational_score" in metadata
        assert "word_count" in metadata
        assert "vocabulary_diversity" in metadata
        
        # Should include content analysis
        assert "has_structure" in metadata
        assert "has_numerical_data" in metadata
    
    @pytest.mark.asyncio
    async def test_validation_warnings_propagation(self, content_service):
        """Test that validation warnings are properly propagated"""
        # Content that will generate warnings but is still valid
        warning_content = """
        This content might generate some warnings.
        It's not very educational in nature.
        No clear structure or learning objectives.
        But it's long enough to pass basic validation.
        """ * 10
        
        result = await content_service.generate_from_text(
            content=warning_content,
            topic="Test Topic"
        )
        
        assert result["status"] == "completed"
        assert "validation_warnings" in result
        
        # Should have warnings about educational quality
        warnings = result["validation_warnings"]
        assert len(warnings) > 0
        assert any("educational" in warning.lower() for warning in warnings)

class TestValidationErrorHandling:
    """Test error handling in validation scenarios"""
    
    @pytest.mark.asyncio
    async def test_validation_exception_handling(self, content_service):
        """Test handling of validation exceptions"""
        # Mock the validator to raise an exception
        with patch.object(content_service.content_validator, 'validate_text_content') as mock_validate:
            mock_validate.side_effect = Exception("Validation error")
            
            result = await content_service.generate_from_text(
                content="Some test content for validation error testing.",
                topic="Test Topic"
            )
            
            assert result["status"] == "failed"
            assert "error_message" in result
            assert "Validation error" in result["error_message"]
    
    @pytest.mark.asyncio
    async def test_partial_validation_failure_recovery(self, content_service, sample_educational_text):
        """Test recovery from partial validation failures"""
        # Test with content that might have some validation issues but should still work
        mixed_content = sample_educational_text + "\n\nSome potentially problematic content here."
        
        result = await content_service.generate_from_text(
            content=mixed_content,
            topic="Test Topic"
        )
        
        # Should complete successfully even with warnings
        assert result["status"] == "completed"
        assert "validation_warnings" in result

if __name__ == "__main__":
    pytest.main([__file__])