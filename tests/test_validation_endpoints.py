"""
Tests for content validation API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.services.content_validator import ValidationResult

client = TestClient(app)

class TestValidationEndpoints:
    """Test validation API endpoints"""
    
    @pytest.fixture
    def sample_educational_text(self):
        """Sample educational text for testing"""
        return """
        Artificial Intelligence is a branch of computer science that aims to create
        intelligent machines capable of performing tasks that typically require human
        intelligence. Key concepts include:
        
        1. Machine Learning - algorithms that improve through experience
        2. Neural Networks - computational models inspired by biological neurons
        3. Natural Language Processing - enabling computers to understand human language
        4. Computer Vision - teaching machines to interpret visual information
        
        Students should understand that AI has applications in healthcare, finance,
        transportation, and many other fields. The field continues to evolve rapidly
        with new breakthroughs in deep learning and reinforcement learning.
        """

class TestTextValidationEndpoint:
    """Test /validate/text endpoint"""
    
    def test_validate_text_success(self, sample_educational_text):
        """Test successful text validation"""
        response = client.post(
            "/content/validate/text",
            data={
                "content": sample_educational_text,
                "content_type": "text"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is True
        assert data["content_length"] > 0
        assert data["sanitized_content_length"] > 0
        assert "quality_metrics" in data
        assert "content_hash" in data
        assert "recommendations" in data
        
        # Should have quality metrics
        metrics = data["quality_metrics"]
        assert "quality_score" in metrics
        assert "educational_score" in metrics
        assert "word_count" in metrics
    
    def test_validate_text_short_content(self):
        """Test validation of short content"""
        response = client.post(
            "/content/validate/text",
            data={
                "content": "Short",
                "content_type": "text"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0
        assert any("too short" in error.lower() for error in data["errors"])
    
    def test_validate_text_malicious_content(self):
        """Test validation of malicious content"""
        malicious_content = "<script>alert('xss')</script>This is malicious content with javascript."
        
        response = client.post(
            "/content/validate/text",
            data={
                "content": malicious_content,
                "content_type": "text"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0
        assert any("malicious" in error.lower() for error in data["errors"])
    
    def test_validate_text_low_quality_with_recommendations(self):
        """Test validation of low-quality content with recommendations"""
        low_quality_content = """
        This is some basic content that lacks educational value.
        It doesn't have much structure or detailed explanations.
        No clear learning objectives or comprehensive information.
        """ * 5  # Make it long enough to pass length validation
        
        response = client.post(
            "/content/validate/text",
            data={
                "content": low_quality_content,
                "content_type": "text"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is True
        assert len(data["warnings"]) > 0
        assert len(data["recommendations"]) > 0
        
        # Should have recommendations for improvement
        recommendations = data["recommendations"]
        assert any("educational" in rec.lower() for rec in recommendations)
    
    def test_validate_text_empty_content(self):
        """Test validation of empty content"""
        response = client.post(
            "/content/validate/text",
            data={
                "content": "",
                "content_type": "text"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0
    
    def test_validate_text_missing_content(self):
        """Test validation endpoint with missing content parameter"""
        response = client.post(
            "/content/validate/text",
            data={
                "content_type": "text"
            }
        )
        
        assert response.status_code == 422  # Validation error

class TestURLValidationEndpoint:
    """Test /validate/url endpoint"""
    
    def test_validate_url_success(self):
        """Test successful URL validation"""
        response = client.post(
            "/content/validate/url",
            data={
                "url": "https://example.com/educational-article"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is True
        assert data["url"] == "https://example.com/educational-article"
        assert "url_metadata" in data
        assert "recommendations" in data
        
        # Should have URL metadata
        metadata = data["url_metadata"]
        assert "domain" in metadata
        assert "protocol" in metadata
        assert metadata["domain"] == "example.com"
        assert metadata["protocol"] == "https"
    
    def test_validate_url_invalid_format(self):
        """Test validation of invalid URL format"""
        response = client.post(
            "/content/validate/url",
            data={
                "url": "not-a-valid-url"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0
        assert any("protocol" in error.lower() for error in data["errors"])
    
    def test_validate_url_unsupported_protocol(self):
        """Test validation of unsupported protocol"""
        response = client.post(
            "/content/validate/url",
            data={
                "url": "ftp://example.com/file.txt"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0
        assert any("protocol" in error.lower() for error in data["errors"])
    
    def test_validate_url_too_long(self):
        """Test validation of excessively long URL"""
        long_url = "https://example.com/" + "a" * 3000
        
        response = client.post(
            "/content/validate/url",
            data={
                "url": long_url
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0
        assert any("too long" in error.lower() for error in data["errors"])
    
    def test_validate_url_with_recommendations(self):
        """Test URL validation with domain-based recommendations"""
        educational_url = "https://university.edu/course/machine-learning"
        
        response = client.post(
            "/content/validate/url",
            data={
                "url": educational_url
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is True
        assert len(data["recommendations"]) > 0
        
        # Should have positive recommendation for educational domain
        recommendations = data["recommendations"]
        assert any("educational" in rec.lower() for rec in recommendations)
    
    def test_validate_url_missing_parameter(self):
        """Test URL validation endpoint with missing URL parameter"""
        response = client.post(
            "/content/validate/url",
            data={}
        )
        
        assert response.status_code == 422  # Validation error

class TestBatchValidationEndpoint:
    """Test /validate/batch endpoint"""
    
    def test_validate_batch_success(self, sample_educational_text):
        """Test successful batch validation"""
        request_data = {
            "inputs": [
                {
                    "content_type": "text",
                    "content": sample_educational_text,
                    "metadata": {"source": "textbook"}
                },
                {
                    "content_type": "text",
                    "content": "Additional educational content about algorithms and data structures for computer science students.",
                    "metadata": {"source": "lecture_notes"}
                }
            ],
            "topic": "Computer Science Fundamentals",
            "difficulty_level": "intermediate",
            "target_audience": "university students"
        }
        
        response = client.post(
            "/content/validate/batch",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_inputs"] == 2
        assert data["valid_inputs"] == 2
        assert data["invalid_inputs"] == 0
        assert len(data["results"]) == 2
        assert "overall_recommendations" in data
        
        # Check individual results
        for result in data["results"]:
            assert result["is_valid"] is True
            assert "quality_metrics" in result
            assert "content_hash" in result
    
    def test_validate_batch_mixed_validity(self, sample_educational_text):
        """Test batch validation with mixed content validity"""
        request_data = {
            "inputs": [
                {
                    "content_type": "text",
                    "content": sample_educational_text,
                    "metadata": {"source": "good_content"}
                },
                {
                    "content_type": "text",
                    "content": "Short",  # Too short
                    "metadata": {"source": "bad_content"}
                },
                {
                    "content_type": "url",
                    "content": "https://example.com/article",
                    "metadata": {"source": "url_content"}
                }
            ],
            "topic": "Mixed Content Test"
        }
        
        response = client.post(
            "/content/validate/batch",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_inputs"] == 3
        assert data["valid_inputs"] == 2  # First and third should be valid
        assert data["invalid_inputs"] == 1  # Second should be invalid
        assert len(data["results"]) == 3
        
        # Check specific results
        assert data["results"][0]["is_valid"] is True   # Good educational content
        assert data["results"][1]["is_valid"] is False  # Too short
        assert data["results"][2]["is_valid"] is True   # Valid URL
        
        # Should have recommendations about invalid inputs
        recommendations = data["overall_recommendations"]
        assert any("failed validation" in rec.lower() for rec in recommendations)
    
    def test_validate_batch_all_invalid(self):
        """Test batch validation with all invalid content"""
        request_data = {
            "inputs": [
                {
                    "content_type": "text",
                    "content": "",  # Empty
                    "metadata": {"source": "empty"}
                },
                {
                    "content_type": "text",
                    "content": "Short",  # Too short
                    "metadata": {"source": "short"}
                }
            ],
            "topic": "Invalid Content Test"
        }
        
        response = client.post(
            "/content/validate/batch",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_inputs"] == 2
        assert data["valid_inputs"] == 0
        assert data["invalid_inputs"] == 2
        
        # All results should be invalid
        for result in data["results"]:
            assert result["is_valid"] is False
            assert len(result["errors"]) > 0
    
    def test_validate_batch_empty_inputs(self):
        """Test batch validation with empty inputs list"""
        request_data = {
            "inputs": [],
            "topic": "Empty Test"
        }
        
        response = client.post(
            "/content/validate/batch",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_inputs"] == 0
        assert data["valid_inputs"] == 0
        assert data["invalid_inputs"] == 0
        assert len(data["results"]) == 0
    
    def test_validate_batch_invalid_request_format(self):
        """Test batch validation with invalid request format"""
        response = client.post(
            "/content/validate/batch",
            json={
                "invalid_field": "invalid_value"
            }
        )
        
        assert response.status_code == 422  # Validation error

class TestValidationEndpointErrorHandling:
    """Test error handling in validation endpoints"""
    
    @patch('app.api.endpoints.content.content_validator.validate_text_content')
    def test_text_validation_internal_error(self, mock_validate):
        """Test handling of internal validation errors"""
        mock_validate.side_effect = Exception("Internal validation error")
        
        response = client.post(
            "/content/validate/text",
            data={
                "content": "Some test content",
                "content_type": "text"
            }
        )
        
        assert response.status_code == 500
        assert "validation failed" in response.json()["detail"].lower()
    
    @patch('app.api.endpoints.content.content_validator.validate_url_content')
    def test_url_validation_internal_error(self, mock_validate):
        """Test handling of internal URL validation errors"""
        mock_validate.side_effect = Exception("Internal URL validation error")
        
        response = client.post(
            "/content/validate/url",
            data={
                "url": "https://example.com"
            }
        )
        
        assert response.status_code == 500
        assert "validation failed" in response.json()["detail"].lower()
    
    @patch('app.api.endpoints.content.content_validator.validate_batch_content')
    def test_batch_validation_internal_error(self, mock_validate):
        """Test handling of internal batch validation errors"""
        mock_validate.side_effect = Exception("Internal batch validation error")
        
        request_data = {
            "inputs": [
                {
                    "content_type": "text",
                    "content": "Test content",
                    "metadata": {}
                }
            ],
            "topic": "Test"
        }
        
        response = client.post(
            "/content/validate/batch",
            json=request_data
        )
        
        assert response.status_code == 500
        assert "validation failed" in response.json()["detail"].lower()

class TestValidationEndpointIntegration:
    """Test integration between validation endpoints and content generation"""
    
    def test_validation_before_generation_workflow(self, sample_educational_text):
        """Test the workflow of validating content before generation"""
        # First, validate the content
        validation_response = client.post(
            "/content/validate/text",
            data={
                "content": sample_educational_text,
                "content_type": "text"
            }
        )
        
        assert validation_response.status_code == 200
        validation_data = validation_response.json()
        assert validation_data["is_valid"] is True
        
        # Then, use the same content for generation
        generation_response = client.post(
            "/content/text",
            data={
                "content": sample_educational_text,
                "topic": "AI Fundamentals",
                "difficulty_level": "intermediate",
                "target_audience": "computer science students"
            }
        )
        
        assert generation_response.status_code == 200
        generation_data = generation_response.json()
        assert generation_data["status"] == "completed"
        
        # The content hash should be consistent
        if "content_metadata" in generation_data:
            # Note: Hashes might differ due to sanitization, but both should exist
            assert validation_data["content_hash"] is not None
    
    def test_validation_recommendations_usage(self):
        """Test using validation recommendations to improve content"""
        # Start with low-quality content
        low_quality_content = "Basic content without much detail or structure."
        
        validation_response = client.post(
            "/content/validate/text",
            data={
                "content": low_quality_content,
                "content_type": "text"
            }
        )
        
        assert validation_response.status_code == 200
        validation_data = validation_response.json()
        
        # Should have recommendations for improvement
        assert len(validation_data["recommendations"]) > 0
        
        # Improved content based on recommendations
        improved_content = """
        Machine Learning Fundamentals
        
        Machine learning is a subset of artificial intelligence that enables computers
        to learn and improve from experience without being explicitly programmed.
        
        Key Concepts:
        1. Supervised Learning - learning from labeled training data
        2. Unsupervised Learning - finding hidden patterns in data
        3. Reinforcement Learning - learning through interaction and feedback
        
        Students will understand how algorithms can automatically improve their
        performance on a specific task through experience and data analysis.
        
        Example: Email spam detection systems learn to identify spam by analyzing
        thousands of emails labeled as spam or not spam.
        """
        
        improved_validation_response = client.post(
            "/content/validate/text",
            data={
                "content": improved_content,
                "content_type": "text"
            }
        )
        
        assert improved_validation_response.status_code == 200
        improved_validation_data = improved_validation_response.json()
        
        # Improved content should have better quality metrics
        original_quality = validation_data["quality_metrics"].get("quality_score", 0)
        improved_quality = improved_validation_data["quality_metrics"].get("quality_score", 0)
        
        assert improved_quality > original_quality

if __name__ == "__main__":
    pytest.main([__file__])