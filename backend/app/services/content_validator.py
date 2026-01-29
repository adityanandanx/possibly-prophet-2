"""
Content validation and sanitization service

This service provides comprehensive validation and sanitization for all input types
(text, files, URLs) to ensure content quality, security, and educational suitability.
"""

import re
import html
import logging
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse
from pathlib import Path
import hashlib
import unicodedata
from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ValidationResult(BaseModel):
    """Result of content validation"""
    is_valid: bool
    sanitized_content: Optional[str] = None
    warnings: List[str] = []
    errors: List[str] = []
    metadata: Dict[str, Any] = {}
    content_hash: Optional[str] = None

class ContentSecurityConfig(BaseModel):
    """Configuration for content security validation"""
    max_text_length: int = 100000  # 100KB
    min_text_length: int = 10
    max_url_length: int = 2048
    allowed_protocols: List[str] = ["http", "https"]
    blocked_domains: List[str] = []
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_extensions: List[str] = [".pdf", ".doc", ".docx", ".txt"]
    
class EducationalContentConfig(BaseModel):
    """Configuration for educational content validation"""
    min_educational_score: float = 0.3
    required_content_types: List[str] = ["text", "concepts"]
    blocked_content_patterns: List[str] = [
        r"(?i)(adult|explicit|nsfw|inappropriate)",
        r"(?i)(violence|harmful|dangerous)",
        r"(?i)(spam|advertisement|promotion)"
    ]
    educational_indicators: List[str] = [
        "learn", "understand", "concept", "theory", "principle",
        "example", "definition", "explanation", "analysis",
        "study", "research", "academic", "educational"
    ]

class ContentValidator:
    """Comprehensive content validation and sanitization service"""
    
    def __init__(self):
        """Initialize the content validator"""
        self.security_config = ContentSecurityConfig()
        self.educational_config = EducationalContentConfig()
        
        # Compile regex patterns for performance
        self._compile_patterns()
        
        logger.info("Content validator initialized")
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        self.blocked_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.educational_config.blocked_content_patterns
        ]
        
        # Common malicious patterns
        self.malicious_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'on\w+\s*=', re.IGNORECASE),  # Event handlers
            re.compile(r'data:text/html', re.IGNORECASE),
            re.compile(r'vbscript:', re.IGNORECASE),
        ]
        
        # Educational content indicators
        self.educational_pattern = re.compile(
            r'\b(' + '|'.join(self.educational_config.educational_indicators) + r')\b',
            re.IGNORECASE
        )
    
    async def validate_text_content(
        self, 
        content: str, 
        content_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate and sanitize text content
        
        Args:
            content: Raw text content
            content_type: Type of content (text, extracted_text, etc.)
            metadata: Additional metadata for validation context
            
        Returns:
            ValidationResult with validation status and sanitized content
        """
        result = ValidationResult(is_valid=True, warnings=[], errors=[], metadata={})
        metadata = metadata or {}
        
        try:
            logger.debug(f"Validating text content: {len(content)} characters")
            
            # Basic validation
            if not content or not isinstance(content, str):
                result.is_valid = False
                result.errors.append("Content is empty or not a string")
                return result
            
            # Length validation
            content_length = len(content.strip())
            if content_length < self.security_config.min_text_length:
                result.is_valid = False
                result.errors.append(
                    f"Content too short ({content_length} chars). "
                    f"Minimum required: {self.security_config.min_text_length} characters"
                )
                return result
            
            if content_length > self.security_config.max_text_length:
                result.is_valid = False
                result.errors.append(
                    f"Content too long ({content_length} chars). "
                    f"Maximum allowed: {self.security_config.max_text_length} characters"
                )
                return result
            
            # Security validation
            security_result = self._validate_content_security(content)
            if not security_result["is_safe"]:
                result.is_valid = False
                result.errors.extend(security_result["errors"])
                return result
            
            result.warnings.extend(security_result["warnings"])
            
            # Educational content validation
            educational_result = self._validate_educational_content(content)
            result.warnings.extend(educational_result["warnings"])
            result.metadata.update(educational_result["metadata"])
            
            # Content sanitization
            sanitized_content = self._sanitize_text_content(content)
            result.sanitized_content = sanitized_content
            
            # Generate content hash for deduplication
            result.content_hash = self._generate_content_hash(sanitized_content)
            
            # Quality assessment
            quality_result = self._assess_content_quality(sanitized_content)
            result.metadata.update(quality_result)
            
            # Final validation
            if quality_result.get("quality_score", 0) < 0.2:
                result.warnings.append("Content quality is low - may not be suitable for educational use")
            
            logger.info(f"Text content validation completed: {len(sanitized_content)} chars, "
                       f"quality_score: {quality_result.get('quality_score', 0):.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating text content: {str(e)}")
            result.is_valid = False
            result.errors.append(f"Validation error: {str(e)}")
            return result
    
    async def validate_file_content(
        self,
        file_path: str,
        file_size: int,
        mime_type: str,
        filename: str
    ) -> ValidationResult:
        """
        Validate uploaded file content
        
        Args:
            file_path: Path to the uploaded file
            file_size: File size in bytes
            mime_type: MIME type of the file
            filename: Original filename
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, warnings=[], errors=[], metadata={})
        
        try:
            logger.debug(f"Validating file: {filename} ({file_size} bytes, {mime_type})")
            
            # File size validation
            if file_size == 0:
                result.is_valid = False
                result.errors.append("File is empty")
                return result
            
            if file_size > self.security_config.max_file_size:
                result.is_valid = False
                result.errors.append(
                    f"File too large ({file_size / (1024*1024):.1f}MB). "
                    f"Maximum allowed: {self.security_config.max_file_size / (1024*1024):.1f}MB"
                )
                return result
            
            # File extension validation
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.security_config.allowed_file_extensions:
                result.is_valid = False
                result.errors.append(
                    f"Unsupported file type '{file_ext}'. "
                    f"Allowed types: {', '.join(self.security_config.allowed_file_extensions)}"
                )
                return result
            
            # MIME type validation
            expected_mime_types = {
                ".pdf": ["application/pdf"],
                ".doc": ["application/msword"],
                ".docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
                ".txt": ["text/plain", "text/x-plain"]
            }
            
            expected_mimes = expected_mime_types.get(file_ext, [])
            if expected_mimes and mime_type not in expected_mimes:
                result.warnings.append(
                    f"MIME type '{mime_type}' doesn't match expected type for '{file_ext}' files"
                )
            
            # Filename validation
            filename_result = self._validate_filename(filename)
            if not filename_result["is_safe"]:
                result.is_valid = False
                result.errors.extend(filename_result["errors"])
                return result
            
            result.warnings.extend(filename_result["warnings"])
            
            # File content security scan (basic)
            if file_ext == ".txt":
                # For text files, we can do content validation
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    
                    text_result = await self.validate_text_content(content, "file_text")
                    if not text_result.is_valid:
                        result.is_valid = False
                        result.errors.extend(text_result.errors)
                        return result
                    
                    result.warnings.extend(text_result.warnings)
                    result.metadata.update(text_result.metadata)
                    
                except Exception as e:
                    result.warnings.append(f"Could not validate text file content: {str(e)}")
            
            # Add file metadata
            result.metadata.update({
                "file_size": file_size,
                "mime_type": mime_type,
                "file_extension": file_ext,
                "filename": filename,
                "validated_at": datetime.now().isoformat()
            })
            
            logger.info(f"File validation completed: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error validating file {filename}: {str(e)}")
            result.is_valid = False
            result.errors.append(f"File validation error: {str(e)}")
            return result
    
    async def validate_url_content(
        self,
        url: str,
        extracted_content: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate URL and its content
        
        Args:
            url: URL to validate
            extracted_content: Content extracted from the URL (optional)
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, warnings=[], errors=[], metadata={})
        
        try:
            logger.debug(f"Validating URL: {url}")
            
            # URL format validation
            url_result = self._validate_url_format(url)
            if not url_result["is_valid"]:
                result.is_valid = False
                result.errors.extend(url_result["errors"])
                return result
            
            result.warnings.extend(url_result["warnings"])
            result.metadata.update(url_result["metadata"])
            
            # Content validation if provided
            if extracted_content:
                content_result = await self.validate_text_content(
                    extracted_content, 
                    "url_content",
                    {"source_url": url}
                )
                
                if not content_result.is_valid:
                    result.is_valid = False
                    result.errors.extend(content_result.errors)
                    return result
                
                result.warnings.extend(content_result.warnings)
                result.metadata.update(content_result.metadata)
                result.sanitized_content = content_result.sanitized_content
                result.content_hash = content_result.content_hash
            
            logger.info(f"URL validation completed: {url}")
            return result
            
        except Exception as e:
            logger.error(f"Error validating URL {url}: {str(e)}")
            result.is_valid = False
            result.errors.append(f"URL validation error: {str(e)}")
            return result
    
    def _validate_content_security(self, content: str) -> Dict[str, Any]:
        """Validate content for security issues"""
        result = {"is_safe": True, "errors": [], "warnings": []}
        
        # Check for malicious patterns
        for pattern in self.malicious_patterns:
            if pattern.search(content):
                result["is_safe"] = False
                result["errors"].append(f"Potentially malicious content detected: {pattern.pattern}")
        
        # Check for blocked content patterns
        for pattern in self.blocked_patterns:
            if pattern.search(content):
                result["warnings"].append(f"Content may contain inappropriate material")
                break
        
        # Check for excessive special characters (potential obfuscation)
        special_char_ratio = len(re.findall(r'[^\w\s]', content)) / len(content) if content else 0
        if special_char_ratio > 0.3:
            result["warnings"].append("Content contains high ratio of special characters")
        
        # Check for suspicious URLs in content
        url_pattern = re.compile(r'https?://[^\s<>"]+', re.IGNORECASE)
        urls = url_pattern.findall(content)
        for url in urls:
            if self._is_suspicious_url(url):
                result["warnings"].append(f"Content contains potentially suspicious URL: {url}")
        
        return result
    
    def _validate_educational_content(self, content: str) -> Dict[str, Any]:
        """Validate content for educational suitability"""
        result = {"warnings": [], "metadata": {}}
        
        # Calculate educational content score
        educational_matches = len(self.educational_pattern.findall(content))
        total_words = len(content.split())
        educational_score = educational_matches / total_words if total_words > 0 else 0
        
        result["metadata"]["educational_score"] = educational_score
        result["metadata"]["educational_indicators"] = educational_matches
        result["metadata"]["total_words"] = total_words
        
        if educational_score < self.educational_config.min_educational_score:
            result["warnings"].append(
                f"Content may not be educational (score: {educational_score:.2f}). "
                f"Consider adding more educational context."
            )
        
        # Check for academic language patterns
        academic_patterns = [
            r'\b(research|study|analysis|methodology|hypothesis|conclusion)\b',
            r'\b(according to|studies show|research indicates|evidence suggests)\b',
            r'\b(definition|explanation|example|illustration|demonstration)\b'
        ]
        
        academic_score = 0
        for pattern in academic_patterns:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            academic_score += matches
        
        result["metadata"]["academic_score"] = academic_score / total_words if total_words > 0 else 0
        
        return result
    
    def _sanitize_text_content(self, content: str) -> str:
        """Sanitize text content for safe processing"""
        # HTML entity decoding
        content = html.unescape(content)
        
        # Unicode normalization
        content = unicodedata.normalize('NFKC', content)
        
        # Remove null bytes and control characters (except newlines and tabs)
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Max 2 consecutive newlines
        
        # Remove excessive punctuation
        content = re.sub(r'[.]{4,}', '...', content)
        content = re.sub(r'[!]{3,}', '!!', content)
        content = re.sub(r'[?]{3,}', '??', content)
        
        # Clean up quotes
        content = re.sub(r'["""]', '"', content)
        content = re.sub(r"[''']", "'", content)
        
        # Remove potential script injections (basic)
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)
        
        return content.strip()
    
    def _assess_content_quality(self, content: str) -> Dict[str, Any]:
        """Assess the quality of content for educational use"""
        result = {}
        
        if not content:
            return {"quality_score": 0.0}
        
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        
        # Basic metrics
        word_count = len(words)
        sentence_count = len([s for s in sentences if s.strip()])
        char_count = len(content)
        
        # Calculate various quality indicators
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Vocabulary diversity (unique words / total words)
        unique_words = set(word.lower() for word in words if word.isalpha())
        vocabulary_diversity = len(unique_words) / word_count if word_count > 0 else 0
        
        # Readability indicators
        complex_words = len([word for word in words if len(word) > 6])
        complexity_ratio = complex_words / word_count if word_count > 0 else 0
        
        # Educational structure indicators
        has_headings = bool(re.search(r'^[A-Z][^.!?]*:?\s*$', content, re.MULTILINE))
        has_lists = bool(re.search(r'^\s*[-•*]\s+', content, re.MULTILINE))
        has_numbers = bool(re.search(r'\b\d+\b', content))
        
        # Calculate overall quality score (0-1)
        quality_factors = [
            min(vocabulary_diversity * 2, 1.0),  # Vocabulary diversity (max 1.0)
            min(avg_word_length / 6, 1.0),       # Average word length (max 1.0)
            min(complexity_ratio * 3, 1.0),      # Complexity ratio (max 1.0)
            0.2 if has_headings else 0.0,        # Structure bonus
            0.1 if has_lists else 0.0,           # List bonus
            0.1 if has_numbers else 0.0,         # Numbers bonus
        ]
        
        quality_score = sum(quality_factors) / len(quality_factors)
        
        result.update({
            "quality_score": round(quality_score, 3),
            "word_count": word_count,
            "sentence_count": sentence_count,
            "character_count": char_count,
            "vocabulary_diversity": round(vocabulary_diversity, 3),
            "average_word_length": round(avg_word_length, 2),
            "average_sentence_length": round(avg_sentence_length, 2),
            "complexity_ratio": round(complexity_ratio, 3),
            "has_structure": has_headings or has_lists,
            "has_numerical_data": has_numbers
        })
        
        return result
    
    def _validate_url_format(self, url: str) -> Dict[str, Any]:
        """Validate URL format and security"""
        result = {"is_valid": True, "errors": [], "warnings": [], "metadata": {}}
        
        # Basic format validation
        if not url or not isinstance(url, str):
            result["is_valid"] = False
            result["errors"].append("URL is empty or not a string")
            return result
        
        url = url.strip()
        
        # Length validation
        if len(url) > self.security_config.max_url_length:
            result["is_valid"] = False
            result["errors"].append(f"URL too long ({len(url)} chars). Maximum: {self.security_config.max_url_length}")
            return result
        
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            result["is_valid"] = False
            result["errors"].append(f"Invalid URL format: {str(e)}")
            return result
        
        # Protocol validation
        if parsed.scheme not in self.security_config.allowed_protocols:
            result["is_valid"] = False
            result["errors"].append(f"Unsupported protocol '{parsed.scheme}'. Allowed: {', '.join(self.security_config.allowed_protocols)}")
            return result
        
        # Domain validation
        if not parsed.netloc:
            result["is_valid"] = False
            result["errors"].append("URL missing domain name")
            return result
        
        # Check blocked domains
        domain = parsed.netloc.lower()
        for blocked_domain in self.security_config.blocked_domains:
            if blocked_domain in domain:
                result["is_valid"] = False
                result["errors"].append(f"Domain '{domain}' is blocked")
                return result
        
        # Security checks
        if self._is_suspicious_url(url):
            result["warnings"].append("URL appears suspicious - proceed with caution")
        
        # Add metadata
        result["metadata"].update({
            "domain": parsed.netloc,
            "protocol": parsed.scheme,
            "path": parsed.path,
            "has_query": bool(parsed.query),
            "has_fragment": bool(parsed.fragment)
        })
        
        return result
    
    def _validate_filename(self, filename: str) -> Dict[str, Any]:
        """Validate filename for security"""
        result = {"is_safe": True, "errors": [], "warnings": []}
        
        if not filename:
            result["is_safe"] = False
            result["errors"].append("Filename is empty")
            return result
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            result["is_safe"] = False
            result["errors"].append("Filename contains invalid path characters")
            return result
        
        # Check for suspicious characters
        suspicious_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
        for char in suspicious_chars:
            if char in filename:
                result["is_safe"] = False
                result["errors"].append(f"Filename contains invalid character: '{char}'")
                return result
        
        # Check filename length
        if len(filename) > 255:
            result["warnings"].append("Filename is very long")
        
        # Check for executable extensions
        executable_extensions = ['.exe', '.bat', '.cmd', '.com', '.scr', '.vbs', '.js']
        file_ext = Path(filename).suffix.lower()
        if file_ext in executable_extensions:
            result["is_safe"] = False
            result["errors"].append(f"Executable file type not allowed: {file_ext}")
            return result
        
        return result
    
    def _is_suspicious_url(self, url: str) -> bool:
        """Check if URL appears suspicious"""
        suspicious_indicators = [
            r'bit\.ly|tinyurl|t\.co',  # URL shorteners
            r'\d+\.\d+\.\d+\.\d+',     # IP addresses instead of domains
            r'[a-z0-9]{20,}',          # Very long random strings
            r'(phishing|malware|spam)', # Suspicious keywords
        ]
        
        for indicator in suspicious_indicators:
            if re.search(indicator, url, re.IGNORECASE):
                return True
        
        return False
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash for content deduplication"""
        # Normalize content for hashing
        normalized = re.sub(r'\s+', ' ', content.lower().strip())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
    
    async def validate_batch_content(
        self,
        content_items: List[Dict[str, Any]]
    ) -> List[ValidationResult]:
        """
        Validate multiple content items in batch
        
        Args:
            content_items: List of content items to validate
            
        Returns:
            List of ValidationResult objects
        """
        results = []
        
        for i, item in enumerate(content_items):
            try:
                content_type = item.get("content_type", "text")
                content = item.get("content", "")
                metadata = item.get("metadata", {})
                
                if content_type == "text":
                    result = await self.validate_text_content(content, content_type, metadata)
                elif content_type == "url":
                    result = await self.validate_url_content(content)
                else:
                    result = ValidationResult(
                        is_valid=False,
                        errors=[f"Unsupported content type: {content_type}"]
                    )
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error validating content item {i}: {str(e)}")
                results.append(ValidationResult(
                    is_valid=False,
                    errors=[f"Validation error: {str(e)}"]
                ))
        
        return results