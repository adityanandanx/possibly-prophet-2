"""
Unit tests for content validation and sanitization
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from pathlib import Path

from app.services.content_validator import (
    ContentValidator, 
    ValidationResult, 
    ContentSecurityConfig, 
    EducationalContentConfig
)

# Global fixtures
@pytest.fixture
def validator():
    """Create a ContentValidator instance for testing"""
    return ContentValidator()

@pytest.fixture
def sample_educational_text():
    """Sample educational text for testing"""
    return """
    Photosynthesis is the process by which plants convert sunlight into energy.
    This biological process involves several key concepts:
    
    1. Chloroplasts - the organelles where photosynthesis occurs
    2. Chlorophyll - the pigment that captures light energy
    3. Carbon dioxide - absorbed from the atmosphere
    4. Water - absorbed through the roots
    
    The overall equation for photosynthesis is:
    6CO2 + 6H2O + light energy → C6H12O6 + 6O2
    
    Students should understand that photosynthesis is essential for life on Earth
    as it produces oxygen and glucose. This process demonstrates the conversion
    of light energy into chemical energy.
    """

@pytest.fixture
def sample_low_quality_text():
    """Sample low-quality text for testing"""
    return "This is short. No details. Bad quality."

@pytest.fixture
def sample_malicious_text():
    """Sample text with potential security issues"""
    return """
    <script>alert('malicious')</script>
    This content contains javascript: void(0) and other suspicious elements.
    Visit this suspicious link: http://192.168.1.1/malware
    """

class TestContentValidator:
    """Test cases for ContentValidator"""

class TestTextContentValidation:
    """Test text content validation functionality"""
    
    @pytest.mark.asyncio
    async def test_valid_educational_content(self, validator, sample_educational_text):
        """Test validation of good educational content"""
        result = await validator.validate_text_content(sample_educational_text)
        
        assert result.is_valid
        assert result.sanitized_content is not None
        assert len(result.sanitized_content) > 0
        assert result.content_hash is not None
        assert result.metadata.get("quality_score", 0) > 0.3
        assert result.metadata.get("educational_score", 0) > 0.1
        assert result.metadata.get("word_count", 0) > 50
    
    @pytest.mark.asyncio
    async def test_empty_content(self, validator):
        """Test validation of empty content"""
        result = await validator.validate_text_content("")
        
        assert not result.is_valid
        assert "empty" in result.errors[0].lower()
    
    @pytest.mark.asyncio
    async def test_short_content(self, validator):
        """Test validation of content that's too short"""
        result = await validator.validate_text_content("Short")
        
        assert not result.is_valid
        assert "too short" in result.errors[0].lower()
    
    @pytest.mark.asyncio
    async def test_long_content(self, validator):
        """Test validation of content that's too long"""
        long_content = "A" * 200000  # 200KB
        result = await validator.validate_text_content(long_content)
        
        assert not result.is_valid
        assert "too long" in result.errors[0].lower()
    
    @pytest.mark.asyncio
    async def test_malicious_content(self, validator, sample_malicious_text):
        """Test detection of malicious content"""
        result = await validator.validate_text_content(sample_malicious_text)
        
        assert not result.is_valid
        assert any("malicious" in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_low_quality_content(self, validator, sample_low_quality_text):
        """Test validation of low-quality content"""
        result = await validator.validate_text_content(sample_low_quality_text)
        
        # Should be valid but with warnings
        assert result.is_valid
        assert len(result.warnings) > 0
        assert result.metadata.get("quality_score", 1) < 0.5
    
    @pytest.mark.asyncio
    async def test_content_sanitization(self, validator):
        """Test content sanitization functionality"""
        dirty_content = """
        This has   excessive    whitespace.
        
        
        
        Multiple newlines above.
        HTML entities: &amp; &lt; &gt; &quot;
        Unicode: café naïve résumé
        """
        
        result = await validator.validate_text_content(dirty_content)
        
        assert result.is_valid
        assert result.sanitized_content is not None
        
        # Check sanitization
        sanitized = result.sanitized_content
        assert "   " not in sanitized  # No excessive whitespace
        assert "\n\n\n" not in sanitized  # No excessive newlines
        assert "&amp;" not in sanitized  # HTML entities decoded
        assert "café" in sanitized  # Unicode preserved
    
    @pytest.mark.asyncio
    async def test_educational_content_scoring(self, validator, sample_educational_text):
        """Test educational content scoring"""
        result = await validator.validate_text_content(sample_educational_text)
        
        assert result.is_valid
        metadata = result.metadata
        
        # Should have educational indicators
        assert metadata.get("educational_score", 0) > 0
        assert metadata.get("educational_indicators", 0) > 0
        
        # Should have reasonable quality metrics
        assert metadata.get("quality_score", 0) > 0.3
        assert metadata.get("vocabulary_diversity", 0) > 0.2
        assert metadata.get("word_count", 0) > 50

class TestURLValidation:
    """Test URL validation functionality"""
    
    @pytest.mark.asyncio
    async def test_valid_url(self, validator):
        """Test validation of valid URL"""
        result = await validator.validate_url_content("https://example.com/article")
        
        assert result.is_valid
        assert result.metadata.get("domain") == "example.com"
        assert result.metadata.get("protocol") == "https"
    
    @pytest.mark.asyncio
    async def test_invalid_url_format(self, validator):
        """Test validation of invalid URL format"""
        result = await validator.validate_url_content("not-a-url")
        
        assert not result.is_valid
        assert any("protocol" in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_unsupported_protocol(self, validator):
        """Test validation of unsupported protocol"""
        result = await validator.validate_url_content("ftp://example.com/file")
        
        assert not result.is_valid
        assert any("protocol" in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_url_too_long(self, validator):
        """Test validation of excessively long URL"""
        long_url = "https://example.com/" + "a" * 3000
        result = await validator.validate_url_content(long_url)
        
        assert not result.is_valid
        assert any("too long" in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_suspicious_url(self, validator):
        """Test detection of suspicious URLs"""
        suspicious_urls = [
            "https://192.168.1.1/malware",
            "https://bit.ly/suspicious",
            "https://example.com/phishing"
        ]
        
        for url in suspicious_urls:
            result = await validator.validate_url_content(url)
            # Should be valid but with warnings
            assert result.is_valid
            if result.warnings:
                assert any("suspicious" in warning.lower() for warning in result.warnings)
    
    @pytest.mark.asyncio
    async def test_url_with_content_validation(self, validator, sample_educational_text):
        """Test URL validation with content"""
        result = await validator.validate_url_content(
            "https://example.com/article", 
            sample_educational_text
        )
        
        assert result.is_valid
        assert result.sanitized_content is not None
        assert result.content_hash is not None
        assert result.metadata.get("quality_score", 0) > 0

class TestFileValidation:
    """Test file validation functionality"""
    
    @pytest.mark.asyncio
    async def test_valid_text_file(self, validator):
        """Test validation of valid text file"""
        content = "This is a valid educational text file with sufficient content for testing."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = await validator.validate_file_content(
                temp_path, len(content.encode()), "text/plain", "test.txt"
            )
            
            assert result.is_valid
            assert result.metadata.get("file_size") == len(content.encode())
            assert result.metadata.get("mime_type") == "text/plain"
            assert result.metadata.get("file_extension") == ".txt"
            
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_empty_file(self, validator):
        """Test validation of empty file"""
        result = await validator.validate_file_content(
            "/tmp/empty", 0, "text/plain", "empty.txt"
        )
        
        assert not result.is_valid
        assert any("empty" in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_file_too_large(self, validator):
        """Test validation of file that's too large"""
        large_size = 20 * 1024 * 1024  # 20MB
        result = await validator.validate_file_content(
            "/tmp/large", large_size, "text/plain", "large.txt"
        )
        
        assert not result.is_valid
        assert any("too large" in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_unsupported_file_type(self, validator):
        """Test validation of unsupported file type"""
        result = await validator.validate_file_content(
            "/tmp/test", 1000, "application/exe", "malware.exe"
        )
        
        assert not result.is_valid
        assert any("unsupported" in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_suspicious_filename(self, validator):
        """Test validation of suspicious filenames"""
        suspicious_names = [
            "../../../etc/passwd",
            "file<script>.txt",
            "test\x00.txt",
            "malware.exe"
        ]
        
        for filename in suspicious_names:
            result = await validator.validate_file_content(
                "/tmp/test", 1000, "text/plain", filename
            )
            
            assert not result.is_valid
            assert len(result.errors) > 0

class TestBatchValidation:
    """Test batch validation functionality"""
    
    @pytest.mark.asyncio
    async def test_batch_validation_mixed_content(self, validator, sample_educational_text):
        """Test batch validation with mixed content quality"""
        content_items = [
            {
                "content_type": "text",
                "content": sample_educational_text,
                "metadata": {"source": "good_content"}
            },
            {
                "content_type": "text", 
                "content": "Too short",
                "metadata": {"source": "bad_content"}
            },
            {
                "content_type": "url",
                "content": "https://example.com/article",
                "metadata": {"source": "url_content"}
            }
        ]
        
        results = await validator.validate_batch_content(content_items)
        
        assert len(results) == 3
        assert results[0].is_valid  # Good educational content
        assert not results[1].is_valid  # Too short
        assert results[2].is_valid  # Valid URL
    
    @pytest.mark.asyncio
    async def test_batch_validation_all_valid(self, validator, sample_educational_text):
        """Test batch validation with all valid content"""
        content_items = [
            {
                "content_type": "text",
                "content": sample_educational_text,
                "metadata": {"source": "content1"}
            },
            {
                "content_type": "text",
                "content": sample_educational_text + " Additional educational content.",
                "metadata": {"source": "content2"}
            }
        ]
        
        results = await validator.validate_batch_content(content_items)
        
        assert len(results) == 2
        assert all(result.is_valid for result in results)
        assert all(result.content_hash for result in results)
        assert results[0].content_hash != results[1].content_hash  # Different hashes

class TestSecurityValidation:
    """Test security validation functionality"""
    
    def test_malicious_pattern_detection(self, validator):
        """Test detection of malicious patterns"""
        malicious_content = [
            "<script>alert('xss')</script>",
            "javascript:void(0)",
            "vbscript:msgbox('test')",
            "data:text/html,<script>alert(1)</script>",
            "onclick='malicious()'"
        ]
        
        for content in malicious_content:
            result = validator._validate_content_security(content)
            assert not result["is_safe"]
            assert len(result["errors"]) > 0
    
    def test_suspicious_url_detection(self, validator):
        """Test detection of suspicious URLs"""
        suspicious_urls = [
            "http://192.168.1.1/malware",
            "https://bit.ly/abcdef123456",
            "https://example.com/abcdefghijklmnopqrstuvwxyz123456789",
            "https://phishing-site.com/login"
        ]
        
        for url in suspicious_urls:
            is_suspicious = validator._is_suspicious_url(url)
            assert is_suspicious
    
    def test_filename_security_validation(self, validator):
        """Test filename security validation"""
        dangerous_filenames = [
            "../../../etc/passwd",
            "file\\with\\backslashes.txt",
            "file<script>.txt",
            "file|pipe.txt",
            "file?.txt",
            "file*.txt",
            "file\x00null.txt",
            "malware.exe"
        ]
        
        for filename in dangerous_filenames:
            result = validator._validate_filename(filename)
            assert not result["is_safe"]
            assert len(result["errors"]) > 0

class TestQualityAssessment:
    """Test content quality assessment functionality"""
    
    def test_quality_metrics_calculation(self, validator, sample_educational_text):
        """Test calculation of quality metrics"""
        result = validator._assess_content_quality(sample_educational_text)
        
        assert "quality_score" in result
        assert "word_count" in result
        assert "sentence_count" in result
        assert "vocabulary_diversity" in result
        assert "average_word_length" in result
        assert "complexity_ratio" in result
        
        # Quality score should be reasonable for educational content
        assert 0 <= result["quality_score"] <= 1
        assert result["word_count"] > 50
        assert result["vocabulary_diversity"] > 0.2
    
    def test_quality_metrics_empty_content(self, validator):
        """Test quality metrics for empty content"""
        result = validator._assess_content_quality("")
        
        assert result["quality_score"] == 0.0
    
    def test_quality_metrics_low_quality(self, validator):
        """Test quality metrics for low-quality content"""
        low_quality = "Bad bad bad bad bad bad bad bad bad bad."
        result = validator._assess_content_quality(low_quality)
        
        assert result["quality_score"] < 0.5
        assert result["vocabulary_diversity"] < 0.3

class TestContentHashing:
    """Test content hashing functionality"""
    
    def test_content_hash_generation(self, validator):
        """Test generation of content hashes"""
        content1 = "This is test content for hashing."
        content2 = "This is test content for hashing."
        content3 = "This is different content for hashing."
        
        hash1 = validator._generate_content_hash(content1)
        hash2 = validator._generate_content_hash(content2)
        hash3 = validator._generate_content_hash(content3)
        
        assert hash1 == hash2  # Same content should have same hash
        assert hash1 != hash3  # Different content should have different hash
        assert len(hash1) == 16  # Hash should be 16 characters
    
    def test_content_hash_normalization(self, validator):
        """Test content hash normalization"""
        content1 = "This   is   test   content."
        content2 = "This is test content."
        content3 = "THIS IS TEST CONTENT."
        
        hash1 = validator._generate_content_hash(content1)
        hash2 = validator._generate_content_hash(content2)
        hash3 = validator._generate_content_hash(content3)
        
        # All should have same hash after normalization
        assert hash1 == hash2 == hash3

class TestConfigurationCustomization:
    """Test configuration customization"""
    
    def test_custom_security_config(self):
        """Test custom security configuration"""
        custom_config = ContentSecurityConfig(
            max_text_length=50000,
            min_text_length=20,
            blocked_domains=["blocked.com"]
        )
        
        validator = ContentValidator()
        validator.security_config = custom_config
        
        assert validator.security_config.max_text_length == 50000
        assert validator.security_config.min_text_length == 20
        assert "blocked.com" in validator.security_config.blocked_domains
    
    def test_custom_educational_config(self):
        """Test custom educational configuration"""
        custom_config = EducationalContentConfig(
            min_educational_score=0.5,
            educational_indicators=["custom", "indicator", "test"]
        )
        
        validator = ContentValidator()
        validator.educational_config = custom_config
        
        assert validator.educational_config.min_educational_score == 0.5
        assert "custom" in validator.educational_config.educational_indicators

if __name__ == "__main__":
    pytest.main([__file__])