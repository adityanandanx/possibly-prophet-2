"""
Content generation service
"""

from typing import Dict, Any, Optional, List
from fastapi import UploadFile, HTTPException
import uuid
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import time

# Import document parser and content validator
from .document_parser import DocumentParser, DocumentParsingError
from .content_validator import ContentValidator, ValidationResult
from .input_storage import input_storage_service
from .manim_generator import ManimCodeGenerator

# Import agents (will be available after agents setup is complete)
try:
    from agents import PedagogyWorkflow
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    logging.warning("Agents not available - using mock responses")

logger = logging.getLogger(__name__)

class ContentService:
    """Service for handling educational content generation"""
    
    def __init__(self):
        """Initialize content service"""
        if AGENTS_AVAILABLE:
            self.workflow = PedagogyWorkflow()
            logger.info("Content service initialized with agents")
        else:
            self.workflow = None
            logger.info("Content service initialized without agents (mock mode)")
        
        # Initialize document parser and content validator
        self.document_parser = DocumentParser()
        self.content_validator = ContentValidator()
        self.manim_generator = ManimCodeGenerator()
        
        # In-memory storage for generation status (replace with database later)
        self.generations = {}
    
    async def generate_from_inputs(
        self,
        inputs: List[Dict[str, Any]],
        topic: Optional[str] = None,
        difficulty_level: str = "intermediate",
        target_audience: str = "general",
        learning_goals: List[str] = None,
        preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate educational content from multiple inputs
        
        Args:
            inputs: List of content inputs to process
            topic: Optional topic override
            difficulty_level: Content difficulty level
            target_audience: Target audience
            learning_goals: Specific learning goals
            preferences: Generation preferences
            
        Returns:
            Generation result dictionary
        """
        generation_id = str(uuid.uuid4())
        learning_goals = learning_goals or []
        preferences = preferences or {}
        
        try:
            logger.info(f"Starting multi-input content generation: {generation_id}")
            
            # Store initial generation status
            self.generations[generation_id] = {
                "status": "processing",
                "created_at": datetime.now(),
                "input_type": "multi_input",
                "input_count": len(inputs)
            }
            
            # Validate all inputs
            validation_results = []
            validated_content = []
            
            for i, input_item in enumerate(inputs):
                # Handle both dict and ContentInput object formats
                if hasattr(input_item, 'content_type'):
                    # Pydantic model object
                    content_type = input_item.content_type
                    content = input_item.content
                    metadata = input_item.metadata or {}
                else:
                    # Dictionary format
                    content_type = input_item.get("content_type", "text")
                    content = input_item.get("content", "")
                    metadata = input_item.get("metadata", {})
                
                if content_type == "text" and content.strip():
                    # Validate text content
                    validation_result = await self.content_validator.validate_text_content(
                        content, f"multi_input_{i}", 
                        {**metadata, "generation_id": generation_id, "input_index": i}
                    )
                    
                    validation_results.append(validation_result)
                    
                    if not validation_result.is_valid:
                        error_message = f"Input {i+1} validation failed: {'; '.join(validation_result.errors)}"
                        logger.error(f"Multi-input validation failed for {generation_id}: {error_message}")
                        error_result = {
                            "generation_id": generation_id,
                            "status": "failed",
                            "error_message": error_message,
                            "validation_errors": validation_result.errors,
                            "failed_input_index": i,
                            "created_at": datetime.now()
                        }
                        self.generations[generation_id].update(error_result)
                        return error_result
                    
                    # Use sanitized content
                    sanitized_content = validation_result.sanitized_content or content
                    validated_content.append(sanitized_content)
            
            # Combine all validated content
            full_content = "\n\n".join(validated_content)
            
            if not full_content.strip():
                raise ValueError("No valid text content found in inputs after validation")
            
            # Collect all validation warnings and metadata
            all_warnings = []
            combined_metadata = {}
            
            for result in validation_results:
                all_warnings.extend(result.warnings)
                combined_metadata.update(result.metadata)
            
            if all_warnings:
                logger.warning(f"Content validation warnings for {generation_id}: {all_warnings}")
            
            # Store combined input with metadata
            from app.models.content import ContentInput, ContentType
            content_input = ContentInput(
                content_type=ContentType.TEXT,  # Combined content is treated as text
                content=full_content,
                metadata={
                    "topic": topic,
                    "difficulty_level": difficulty_level,
                    "target_audience": target_audience,
                    "learning_goals": learning_goals,
                    "input_count": len(validated_content),
                    "original_inputs": [
                        {
                            "content_type": inp.get("content_type") if isinstance(inp, dict) else inp.content_type,
                            "content_length": len(inp.get("content", "") if isinstance(inp, dict) else inp.content),
                            "metadata": inp.get("metadata", {}) if isinstance(inp, dict) else inp.metadata
                        }
                        for inp in inputs
                    ],
                    "combined_content_length": len(full_content)
                }
            )
            
            processing_metadata = {
                "status": "processing",
                "generation_id": generation_id,
                "processing_start": datetime.now().isoformat(),
                "multi_input": True,
                "input_count": len(validated_content),
                "content_combined": True
            }
            
            try:
                storage_id = await input_storage_service.store_input(
                    content_input=content_input,
                    validation_result={
                        "combined_validation": True,
                        "individual_results": [result.__dict__ if hasattr(result, '__dict__') else result for result in validation_results],
                        "all_warnings": all_warnings,
                        "combined_metadata": combined_metadata
                    },
                    processing_metadata=processing_metadata,
                    generation_id=generation_id
                )
                logger.info(f"Stored multi-input with storage ID: {storage_id}")
            except Exception as storage_error:
                logger.warning(f"Failed to store multi-input for {generation_id}: {str(storage_error)}")
                storage_id = None
            
            if AGENTS_AVAILABLE and self.workflow:
                # Use real agents workflow
                context = {
                    "topic": topic,
                    "difficulty_level": difficulty_level,
                    "target_audience": target_audience,
                    "learning_goals": learning_goals,
                    "preferences": preferences,
                    "inputs": inputs,
                    "validation_metadata": combined_metadata,
                    "input_count": len(validated_content)
                }
                
                educational_script = self.workflow.execute(full_content, context)
                
                result = {
                    "generation_id": generation_id,
                    "status": "completed",
                    "educational_script": educational_script,
                    "created_at": datetime.now(),
                    "completed_at": datetime.now(),
                    "validation_warnings": all_warnings,
                    "content_metadata": combined_metadata,
                    "storage_id": storage_id
                }
            else:
                # Mock response for testing
                result = self._create_mock_response(generation_id, topic or "Generated Content")
                result["validation_warnings"] = all_warnings
                result["content_metadata"] = combined_metadata
                result["storage_id"] = storage_id
            
            # Update generation status
            self.generations[generation_id].update(result)
            
            logger.info(f"Completed multi-input content generation: {generation_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in multi-input content generation: {str(e)}")
            error_result = {
                "generation_id": generation_id,
                "status": "failed",
                "error_message": str(e),
                "created_at": datetime.now()
            }
            self.generations[generation_id].update(error_result)
            return error_result

    async def generate_from_text(
        self,
        content: str,
        topic: Optional[str] = None,
        difficulty_level: str = "intermediate",
        target_audience: str = "general",
        learning_goals: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate educational content from text input
        
        Args:
            content: Raw text content
            topic: Optional topic override
            difficulty_level: Content difficulty level
            target_audience: Target audience
            learning_goals: Specific learning goals
            
        Returns:
            Generation result dictionary
        """
        generation_id = str(uuid.uuid4())
        learning_goals = learning_goals or []
        
        try:
            logger.info(f"Starting text content generation: {generation_id}")
            
            # Store initial generation status
            self.generations[generation_id] = {
                "status": "processing",
                "created_at": datetime.now(),
                "input_type": "text"
            }
            
            # Validate and sanitize content
            validation_result = await self.content_validator.validate_text_content(
                content, "text", {"generation_id": generation_id}
            )
            
            if not validation_result.is_valid:
                error_message = f"Content validation failed: {'; '.join(validation_result.errors)}"
                logger.error(f"Text validation failed for {generation_id}: {error_message}")
                error_result = {
                    "generation_id": generation_id,
                    "status": "failed",
                    "error_message": error_message,
                    "validation_errors": validation_result.errors,
                    "created_at": datetime.now()
                }
                self.generations[generation_id].update(error_result)
                return error_result
            
            # Log validation warnings
            if validation_result.warnings:
                logger.warning(f"Content validation warnings for {generation_id}: {validation_result.warnings}")
            
            # Use sanitized content for processing
            processed_content = validation_result.sanitized_content or content
            
            # Store input with metadata
            from app.models.content import ContentInput, ContentType
            content_input = ContentInput(
                content_type=ContentType.TEXT,
                content=processed_content,
                metadata={
                    "topic": topic,
                    "difficulty_level": difficulty_level,
                    "target_audience": target_audience,
                    "learning_goals": learning_goals,
                    "original_content_length": len(content),
                    "processed_content_length": len(processed_content)
                }
            )
            
            processing_metadata = {
                "status": "processing",
                "generation_id": generation_id,
                "processing_start": datetime.now().isoformat(),
                "content_sanitized": processed_content != content
            }
            
            try:
                storage_id = await input_storage_service.store_input(
                    content_input=content_input,
                    validation_result=validation_result.__dict__ if hasattr(validation_result, '__dict__') else validation_result,
                    processing_metadata=processing_metadata,
                    generation_id=generation_id
                )
                logger.info(f"Stored input with storage ID: {storage_id}")
            except Exception as storage_error:
                logger.warning(f"Failed to store input for {generation_id}: {str(storage_error)}")
                storage_id = None
            
            if AGENTS_AVAILABLE and self.workflow:
                # Use real agents workflow
                context = {
                    "topic": topic,
                    "difficulty_level": difficulty_level,
                    "target_audience": target_audience,
                    "validation_metadata": validation_result.metadata,
                    "content_hash": validation_result.content_hash,
                    "storage_id": storage_id
                }
                
                educational_script = self.workflow.execute(processed_content, context)
                
                result = {
                    "generation_id": generation_id,
                    "status": "completed",
                    "educational_script": educational_script,
                    "created_at": datetime.now(),
                    "completed_at": datetime.now(),
                    "validation_warnings": validation_result.warnings,
                    "content_metadata": validation_result.metadata,
                    "storage_id": storage_id
                }
            else:
                # Mock response for testing
                result = self._create_mock_response(generation_id, topic or "Generated Content")
                result["validation_warnings"] = validation_result.warnings
                result["content_metadata"] = validation_result.metadata
                result["storage_id"] = storage_id
            
            # Update processing metadata
            if storage_id:
                try:
                    processing_metadata.update({
                        "status": "completed",
                        "processing_end": datetime.now().isoformat(),
                        "generation_result": "success"
                    })
                    # Note: In a full implementation, we might update the stored processing metadata
                except Exception as update_error:
                    logger.warning(f"Failed to update processing metadata: {str(update_error)}")
            
            # Update generation status
            self.generations[generation_id].update(result)
            
            logger.info(f"Completed text content generation: {generation_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in text content generation: {str(e)}")
            error_result = {
                "generation_id": generation_id,
                "status": "failed",
                "error_message": str(e),
                "created_at": datetime.now()
            }
            self.generations[generation_id].update(error_result)
            return error_result
    
    async def generate_from_file(
        self,
        file: UploadFile,
        topic: Optional[str] = None,
        difficulty_level: str = "intermediate",
        target_audience: str = "general",
        learning_goals: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate educational content from uploaded file
        
        Args:
            file: Uploaded file
            topic: Optional topic override
            difficulty_level: Content difficulty level
            target_audience: Target audience
            learning_goals: Specific learning goals
            
        Returns:
            Generation result dictionary
        """
        generation_id = str(uuid.uuid4())
        learning_goals = learning_goals or []
        
        try:
            logger.info(f"Starting file content generation: {generation_id}")
            
            # Store initial generation status
            self.generations[generation_id] = {
                "status": "processing",
                "created_at": datetime.now(),
                "input_type": "file",
                "filename": file.filename
            }
            
            # Get file information for validation
            file_content = await file.read()
            file_size = len(file_content)
            await file.seek(0)  # Reset file pointer
            
            # Validate file before processing
            import tempfile
            import os
            
            # Create temporary file for validation
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Get MIME type
                import magic
                mime_type = magic.from_file(temp_file_path, mime=True)
                
                # Validate file
                file_validation = await self.content_validator.validate_file_content(
                    temp_file_path, file_size, mime_type, file.filename
                )
                
                if not file_validation.is_valid:
                    error_message = f"File validation failed: {'; '.join(file_validation.errors)}"
                    logger.error(f"File validation failed for {generation_id}: {error_message}")
                    error_result = {
                        "generation_id": generation_id,
                        "status": "failed",
                        "error_message": error_message,
                        "validation_errors": file_validation.errors,
                        "created_at": datetime.now()
                    }
                    self.generations[generation_id].update(error_result)
                    return error_result
                
                if file_validation.warnings:
                    logger.warning(f"File validation warnings for {generation_id}: {file_validation.warnings}")
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                await file.seek(0)  # Reset file pointer again
            
            # Extract text content using document parser
            try:
                extraction_result = await self.document_parser.extract_text_from_file(file)
                text_content = extraction_result["text"]
                file_metadata = extraction_result["metadata"]
                
                logger.info(f"Successfully extracted {len(text_content)} characters from {file.filename}")
                
            except DocumentParsingError as e:
                logger.error(f"Document parsing error for {file.filename}: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Unexpected error parsing {file.filename}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")
            
            # Validate extracted text content
            content_validation = await self.content_validator.validate_text_content(
                text_content, "file_content", 
                {"filename": file.filename, "generation_id": generation_id, **file_metadata}
            )
            
            if not content_validation.is_valid:
                error_message = f"Extracted content validation failed: {'; '.join(content_validation.errors)}"
                logger.error(f"Content validation failed for {generation_id}: {error_message}")
                error_result = {
                    "generation_id": generation_id,
                    "status": "failed",
                    "error_message": error_message,
                    "validation_errors": content_validation.errors,
                    "created_at": datetime.now()
                }
                self.generations[generation_id].update(error_result)
                return error_result
            
            # Combine validation warnings
            all_warnings = file_validation.warnings + content_validation.warnings
            if all_warnings:
                logger.warning(f"File content validation warnings for {generation_id}: {all_warnings}")
            
            # Use sanitized content
            processed_content = content_validation.sanitized_content or text_content
            
            # Store input with metadata
            from app.models.content import ContentInput, ContentType
            content_input = ContentInput(
                content_type=ContentType.FILE,
                content=processed_content,
                metadata={
                    "filename": file.filename,
                    "topic": topic,
                    "difficulty_level": difficulty_level,
                    "target_audience": target_audience,
                    "learning_goals": learning_goals,
                    "original_text_length": len(text_content),
                    "processed_text_length": len(processed_content),
                    **file_metadata
                }
            )
            
            processing_metadata = {
                "status": "processing",
                "generation_id": generation_id,
                "processing_start": datetime.now().isoformat(),
                "file_processed": True,
                "text_extracted": True,
                "content_sanitized": processed_content != text_content
            }
            
            try:
                storage_id = await input_storage_service.store_input(
                    content_input=content_input,
                    validation_result={
                        "file_validation": file_validation.__dict__ if hasattr(file_validation, '__dict__') else file_validation,
                        "content_validation": content_validation.__dict__ if hasattr(content_validation, '__dict__') else content_validation
                    },
                    processing_metadata=processing_metadata,
                    generation_id=generation_id
                )
                logger.info(f"Stored file input with storage ID: {storage_id}")
            except Exception as storage_error:
                logger.warning(f"Failed to store file input for {generation_id}: {str(storage_error)}")
                storage_id = None
            
            # Generate content from extracted and validated text
            result = await self.generate_from_text(
                content=processed_content,
                topic=topic or file.filename,
                difficulty_level=difficulty_level,
                target_audience=target_audience,
                learning_goals=learning_goals
            )
            
            # Add file-specific metadata to the result
            if "educational_script" in result and result["educational_script"]:
                result["educational_script"]["metadata"] = result["educational_script"].get("metadata", {})
                result["educational_script"]["metadata"]["source_file"] = {
                    **file_metadata,
                    **file_validation.metadata
                }
            
            # Add file validation warnings to existing warnings
            existing_warnings = result.get("validation_warnings", [])
            result["validation_warnings"] = existing_warnings + all_warnings
            
            # Combine content metadata
            existing_metadata = result.get("content_metadata", {})
            combined_metadata = {
                **existing_metadata, 
                **content_validation.metadata, 
                **file_validation.metadata,
                "file_metadata": file_metadata
            }
            result["content_metadata"] = combined_metadata
            result["file_storage_id"] = storage_id
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in file content generation: {str(e)}")
            error_result = {
                "generation_id": generation_id,
                "status": "failed",
                "error_message": str(e),
                "created_at": datetime.now()
            }
            self.generations[generation_id].update(error_result)
            return error_result
    
    async def generate_from_url(
        self,
        url: str,
        topic: Optional[str] = None,
        difficulty_level: str = "intermediate",
        target_audience: str = "general",
        learning_goals: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate educational content from web URL
        
        Args:
            url: Web URL to process
            topic: Optional topic override
            difficulty_level: Content difficulty level
            target_audience: Target audience
            learning_goals: Specific learning goals
            
        Returns:
            Generation result dictionary
        """
        generation_id = str(uuid.uuid4())
        learning_goals = learning_goals or []
        
        try:
            logger.info(f"Starting URL content generation: {generation_id}")
            
            # Store initial generation status
            self.generations[generation_id] = {
                "status": "processing",
                "created_at": datetime.now(),
                "input_type": "url",
                "source_url": url
            }
            
            # Validate URL format first
            url_validation = await self.content_validator.validate_url_content(url)
            if not url_validation.is_valid:
                error_message = f"URL validation failed: {'; '.join(url_validation.errors)}"
                logger.error(f"URL validation failed for {generation_id}: {error_message}")
                error_result = {
                    "generation_id": generation_id,
                    "status": "failed",
                    "error_message": error_message,
                    "validation_errors": url_validation.errors,
                    "created_at": datetime.now()
                }
                self.generations[generation_id].update(error_result)
                return error_result
            
            # Scrape content from URL
            scraped_content = await self._scrape_url_content(url)
            
            if not scraped_content.strip():
                raise ValueError(f"No content could be extracted from URL: {url}")
            
            # Validate scraped content
            content_validation = await self.content_validator.validate_text_content(
                scraped_content, "url_content", 
                {"source_url": url, "generation_id": generation_id}
            )
            
            if not content_validation.is_valid:
                error_message = f"Scraped content validation failed: {'; '.join(content_validation.errors)}"
                logger.error(f"Content validation failed for {generation_id}: {error_message}")
                error_result = {
                    "generation_id": generation_id,
                    "status": "failed",
                    "error_message": error_message,
                    "validation_errors": content_validation.errors,
                    "created_at": datetime.now()
                }
                self.generations[generation_id].update(error_result)
                return error_result
            
            # Combine validation warnings
            all_warnings = url_validation.warnings + content_validation.warnings
            if all_warnings:
                logger.warning(f"URL content validation warnings for {generation_id}: {all_warnings}")
            
            # Use sanitized content
            processed_content = content_validation.sanitized_content or scraped_content
            
            # Store input with metadata
            from app.models.content import ContentInput, ContentType
            content_input = ContentInput(
                content_type=ContentType.URL,
                content=processed_content,
                metadata={
                    "source_url": url,
                    "topic": topic,
                    "difficulty_level": difficulty_level,
                    "target_audience": target_audience,
                    "learning_goals": learning_goals,
                    "original_scraped_length": len(scraped_content),
                    "processed_content_length": len(processed_content),
                    "scraping_timestamp": datetime.now().isoformat()
                }
            )
            
            processing_metadata = {
                "status": "processing",
                "generation_id": generation_id,
                "processing_start": datetime.now().isoformat(),
                "url_scraped": True,
                "content_sanitized": processed_content != scraped_content
            }
            
            try:
                storage_id = await input_storage_service.store_input(
                    content_input=content_input,
                    validation_result={
                        "url_validation": url_validation.__dict__ if hasattr(url_validation, '__dict__') else url_validation,
                        "content_validation": content_validation.__dict__ if hasattr(content_validation, '__dict__') else content_validation
                    },
                    processing_metadata=processing_metadata,
                    generation_id=generation_id
                )
                logger.info(f"Stored URL input with storage ID: {storage_id}")
            except Exception as storage_error:
                logger.warning(f"Failed to store URL input for {generation_id}: {str(storage_error)}")
                storage_id = None
            
            # Generate content from validated and sanitized text
            result = await self.generate_from_text(
                content=processed_content,
                topic=topic or self._extract_title_from_url(url),
                difficulty_level=difficulty_level,
                target_audience=target_audience,
                learning_goals=learning_goals
            )
            
            # Update the result with URL-specific metadata
            if "educational_script" in result and result["educational_script"]:
                result["educational_script"]["metadata"] = result["educational_script"].get("metadata", {})
                result["educational_script"]["metadata"]["source_url"] = url
                result["educational_script"]["metadata"]["content_length"] = len(processed_content)
                result["educational_script"]["metadata"]["url_validation"] = url_validation.metadata
            
            # Add URL validation warnings to existing warnings
            existing_warnings = result.get("validation_warnings", [])
            result["validation_warnings"] = existing_warnings + all_warnings
            
            # Combine content metadata
            existing_metadata = result.get("content_metadata", {})
            combined_metadata = {**existing_metadata, **content_validation.metadata, **url_validation.metadata}
            result["content_metadata"] = combined_metadata
            result["url_storage_id"] = storage_id
            
            logger.info(f"Completed URL content generation: {generation_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in URL content generation: {str(e)}")
            error_result = {
                "generation_id": generation_id,
                "status": "failed",
                "error_message": str(e),
                "created_at": datetime.now()
            }
            self.generations[generation_id].update(error_result)
            return error_result
    
    async def _scrape_url_content(self, url: str) -> str:
        """
        Enhanced web scraping with robust content extraction
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted text content
            
        Raises:
            HTTPException: If URL is invalid or scraping fails
        """
        try:
            # Validate URL format
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid URL format. Must include protocol (http:// or https://)"
                )
            
            # Enhanced headers with multiple User-Agent rotation capability
            headers = self._get_scraping_headers()
            
            # Make request with retry logic
            response = await self._make_request_with_retry(url, headers)
            
            # Validate and process response
            content_type = response.headers.get('content-type', '').lower()
            if not self._is_supported_content_type(content_type):
                raise HTTPException(
                    status_code=415,
                    detail=f"Unsupported content type: {content_type}. Only HTML pages are supported."
                )
            
            # Parse HTML with enhanced error handling
            soup = self._parse_html_content(response.content, response.encoding)
            
            # Extract page metadata for better context
            page_metadata = self._extract_page_metadata(soup)
            
            # Enhanced content extraction with multiple strategies
            text_content = self._extract_meaningful_text_enhanced(soup, url)
            
            # Advanced text cleaning and validation
            cleaned_content = self._clean_scraped_text_enhanced(text_content)
            
            # Quality validation with detailed feedback
            self._validate_content_quality(cleaned_content, url)
            
            logger.info(f"Successfully extracted {len(cleaned_content)} characters from URL: {url}")
            logger.debug(f"Page metadata: {page_metadata}")
            
            return cleaned_content
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except requests.exceptions.Timeout:
            raise HTTPException(
                status_code=408,
                detail="Request timeout. The URL took too long to respond (30s limit)."
            )
        except requests.exceptions.ConnectionError:
            raise HTTPException(
                status_code=503,
                detail="Connection error. Could not connect to the URL. Please check your internet connection."
            )
        except requests.exceptions.HTTPError as e:
            raise self._handle_http_error(e)
        except Exception as e:
            logger.error(f"Unexpected error scraping URL {url}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to scrape URL content: {str(e)}"
            )
    
    def _get_scraping_headers(self) -> Dict[str, str]:
        """Get enhanced headers for web scraping"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
    
    async def _make_request_with_retry(self, url: str, headers: Dict[str, str], max_retries: int = 2) -> requests.Response:
        """Make HTTP request with retry logic"""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Fetching content from URL (attempt {attempt + 1}): {url}")
                
                # Use session for better connection handling
                session = requests.Session()
                session.headers.update(headers)
                
                response = session.get(
                    url, 
                    timeout=30, 
                    allow_redirects=True,
                    stream=False,
                    verify=True  # SSL verification
                )
                response.raise_for_status()
                
                # Check response size
                if len(response.content) > 10 * 1024 * 1024:  # 10MB limit
                    raise HTTPException(
                        status_code=413,
                        detail="Response too large. Maximum supported page size is 10MB."
                    )
                
                return response
                
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
            except Exception as e:
                raise e
        
        # This should never be reached, but just in case
        raise last_exception or Exception("Request failed after all retries")
    
    def _is_supported_content_type(self, content_type: str) -> bool:
        """Check if content type is supported for scraping"""
        supported_types = [
            'text/html',
            'application/xhtml+xml',
            'application/xml',
            'text/xml'
        ]
        return any(supported_type in content_type for supported_type in supported_types)
    
    def _parse_html_content(self, content: bytes, encoding: Optional[str] = None) -> BeautifulSoup:
        """Parse HTML content with enhanced error handling"""
        try:
            # Try to detect encoding if not provided
            if encoding:
                try:
                    decoded_content = content.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    # Fall back to UTF-8 if specified encoding fails
                    decoded_content = content.decode('utf-8', errors='replace')
            else:
                # Try UTF-8 first, then fall back to other encodings
                try:
                    decoded_content = content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        decoded_content = content.decode('latin-1')
                    except UnicodeDecodeError:
                        decoded_content = content.decode('utf-8', errors='replace')
            
            # Parse with BeautifulSoup using lxml parser if available, otherwise html.parser
            try:
                soup = BeautifulSoup(decoded_content, 'lxml')
            except:
                soup = BeautifulSoup(decoded_content, 'html.parser')
            
            return soup
            
        except Exception as e:
            logger.error(f"Error parsing HTML content: {str(e)}")
            raise HTTPException(
                status_code=422,
                detail="Failed to parse HTML content. The page may be malformed."
            )
    
    def _extract_page_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract page metadata for better context"""
        metadata = {}
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            metadata['description'] = meta_desc['content'].strip()
        
        # Extract meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            metadata['keywords'] = meta_keywords['content'].strip()
        
        # Extract language
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            metadata['language'] = html_tag['lang']
        
        # Extract author
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author and meta_author.get('content'):
            metadata['author'] = meta_author['content'].strip()
        
        return metadata
    
    def _handle_http_error(self, error: requests.exceptions.HTTPError) -> HTTPException:
        """Handle HTTP errors with detailed messages"""
        status_code = error.response.status_code
        
        error_messages = {
            400: "Bad request. The URL may be malformed.",
            401: "Authentication required. The website requires login.",
            403: "Access forbidden. The website may be blocking automated requests.",
            404: "URL not found. Please check the URL and try again.",
            429: "Too many requests. The website is rate limiting. Please try again later.",
            500: "Internal server error on the target website.",
            502: "Bad gateway. The website server is having issues.",
            503: "Service unavailable. The website is temporarily down.",
            504: "Gateway timeout. The website took too long to respond."
        }
        
        detail = error_messages.get(status_code, f"HTTP error {status_code}: {error.response.reason}")
        
        return HTTPException(status_code=status_code, detail=detail)
    
    def _validate_content_quality(self, content: str, url: str) -> None:
        """Validate content quality with detailed feedback"""
        content_length = len(content.strip())
        
        if content_length < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient content extracted from URL ({content_length} characters). "
                       f"Please ensure the page contains substantial text content. "
                       f"The page may be JavaScript-heavy or have restricted access."
            )
        
        # Check for common indicators of failed scraping
        low_quality_indicators = [
            'javascript is disabled',
            'enable javascript',
            'please enable cookies',
            'access denied',
            'forbidden',
            'not authorized',
            'login required',
            'subscription required'
        ]
        
        content_lower = content.lower()
        for indicator in low_quality_indicators:
            if indicator in content_lower:
                logger.warning(f"Potential content quality issue detected for {url}: {indicator}")
                break
        
        # Check content diversity (not just repeated text)
        words = content.split()
        if len(words) > 50:
            unique_words = set(words)
            diversity_ratio = len(unique_words) / len(words)
            if diversity_ratio < 0.3:  # Less than 30% unique words
                logger.warning(f"Low content diversity detected for {url}: {diversity_ratio:.2f}")
        
        logger.info(f"Content quality validation passed for {url}: {content_length} characters")
    
    def _extract_meaningful_text_enhanced(self, soup: BeautifulSoup, url: str) -> str:
        """
        Enhanced text extraction with multiple strategies for different website types
        
        Args:
            soup: BeautifulSoup parsed HTML
            url: Source URL for context
            
        Returns:
            Extracted text content
        """
        # Remove unwanted elements first
        self._remove_unwanted_elements(soup)
        
        # Strategy 1: Try structured content selectors (most reliable)
        content = self._extract_with_structured_selectors(soup)
        if content and len(content.strip()) > 200:
            logger.debug(f"Used structured selectors for {url}")
            return content
        
        # Strategy 2: Try article/blog-specific selectors
        content = self._extract_with_article_selectors(soup)
        if content and len(content.strip()) > 200:
            logger.debug(f"Used article selectors for {url}")
            return content
        
        # Strategy 3: Try documentation/wiki-specific selectors
        content = self._extract_with_documentation_selectors(soup)
        if content and len(content.strip()) > 200:
            logger.debug(f"Used documentation selectors for {url}")
            return content
        
        # Strategy 4: Try news/media-specific selectors
        content = self._extract_with_news_selectors(soup)
        if content and len(content.strip()) > 200:
            logger.debug(f"Used news selectors for {url}")
            return content
        
        # Strategy 5: Fall back to general content extraction
        content = self._extract_with_general_strategy(soup)
        if content and len(content.strip()) > 100:
            logger.debug(f"Used general strategy for {url}")
            return content
        
        # Strategy 6: Last resort - extract all text with filtering
        logger.warning(f"Using last resort extraction for {url}")
        return self._extract_with_last_resort(soup)
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """Remove unwanted HTML elements"""
        unwanted_tags = [
            'script', 'style', 'noscript', 'iframe', 'embed', 'object',
            'form', 'input', 'button', 'select', 'textarea',
            'nav', 'header', 'footer', 'aside', 'menu',
            'advertisement', 'ads', 'social-share', 'comments'
        ]
        
        # Remove by tag name
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove by class/id patterns
        unwanted_patterns = [
            'nav', 'navigation', 'menu', 'sidebar', 'footer', 'header',
            'ad', 'ads', 'advertisement', 'banner', 'popup', 'modal',
            'social', 'share', 'comment', 'related', 'recommended',
            'newsletter', 'subscription', 'cookie', 'gdpr'
        ]
        
        for pattern in unwanted_patterns:
            # Remove by class
            for element in soup.find_all(class_=lambda x: x and any(pattern in cls.lower() for cls in x)):
                element.decompose()
            # Remove by id
            for element in soup.find_all(id=lambda x: x and pattern in x.lower()):
                element.decompose()
    
    def _extract_with_structured_selectors(self, soup: BeautifulSoup) -> str:
        """Extract using structured content selectors"""
        selectors = [
            'article',
            'main',
            '[role="main"]',
            '.content',
            '.post-content',
            '.entry-content',
            '.article-content',
            '#content',
            '.main-content',
            '.page-content'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                return self._extract_text_from_element(elements[0])
        
        return ""
    
    def _extract_with_article_selectors(self, soup: BeautifulSoup) -> str:
        """Extract using blog/article-specific selectors"""
        selectors = [
            '.post-body',
            '.article-body',
            '.entry-body',
            '.blog-content',
            '.post-text',
            '.article-text',
            '.content-body',
            '.story-body',
            '.article-wrapper'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                return self._extract_text_from_element(elements[0])
        
        return ""
    
    def _extract_with_documentation_selectors(self, soup: BeautifulSoup) -> str:
        """Extract using documentation/wiki-specific selectors"""
        selectors = [
            '.wiki-content',
            '.documentation',
            '.docs-content',
            '.readme',
            '.markdown-body',
            '.rst-content',
            '.doc-content',
            '.guide-content',
            '.tutorial-content'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                return self._extract_text_from_element(elements[0])
        
        return ""
    
    def _extract_with_news_selectors(self, soup: BeautifulSoup) -> str:
        """Extract using news/media-specific selectors"""
        selectors = [
            '.story-content',
            '.news-content',
            '.article-content',
            '.story-body',
            '.news-body',
            '.press-release',
            '.media-content'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                return self._extract_text_from_element(elements[0])
        
        return ""
    
    def _extract_with_general_strategy(self, soup: BeautifulSoup) -> str:
        """Extract using general content strategy"""
        # Try body content with filtering
        body = soup.find('body')
        if body:
            return self._extract_text_from_element(body)
        
        # Fall back to entire document
        return self._extract_text_from_element(soup)
    
    def _extract_with_last_resort(self, soup: BeautifulSoup) -> str:
        """Last resort extraction - get all text and filter heavily"""
        all_text = soup.get_text(separator=' ', strip=True)
        
        # Split into sentences and filter
        sentences = re.split(r'[.!?]+', all_text)
        meaningful_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and self._is_meaningful_sentence(sentence):
                meaningful_sentences.append(sentence)
        
        return '. '.join(meaningful_sentences[:50])  # Limit to 50 sentences
    
    def _extract_text_from_element(self, element) -> str:
        """Extract text from a specific element with smart formatting"""
        if not element:
            return ""
        
        # Get all text elements in order
        text_elements = element.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'div', 'span'])
        
        text_parts = []
        seen_texts = set()  # Avoid duplicates
        
        for elem in text_elements:
            text = elem.get_text(strip=True)
            
            # Skip if too short, duplicate, or unwanted
            if (len(text) < 5 or  # Reduced from 10 to 5 to capture more content
                text in seen_texts or 
                not self._is_meaningful_text(text)):
                continue
            
            seen_texts.add(text)
            
            # Add appropriate spacing based on element type
            if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                text_parts.append(f"\n\n{text}\n")
            elif elem.name in ['p', 'blockquote']:
                text_parts.append(f"{text}\n")
            elif elem.name == 'li':
                text_parts.append(f"• {text}\n")
            else:
                text_parts.append(text)
        
        # If no structured text found, fall back to all text
        if not text_parts:
            all_text = element.get_text(separator=' ', strip=True)
            if len(all_text) > 20:  # Reduced threshold
                text_parts = [all_text]
        
        return '\n'.join(text_parts)
    
    def _is_meaningful_text(self, text: str) -> bool:
        """Check if text is meaningful content"""
        if not text or len(text.strip()) < 3:
            return False
        
        # Skip common UI/navigation text - be more specific with patterns
        skip_patterns = [
            r'^(skip to|jump to|go to)',
            r'^(home|about|contact|privacy|terms)$',
            r'^(login|register|sign in|sign up)$',
            r'^(search|menu|navigation)$',
            r'^(cookie|gdpr|privacy policy)$',
            r'^(share|like|follow|subscribe)$',
            r'^(advertisement|sponsored|ad)$',
            r'follow us on',  # Added specific pattern for social media
            r'subscribe to',  # Added specific pattern for subscriptions
            r'^\d+$',  # Just numbers
            r'^[^\w\s]+$',  # Just punctuation
        ]
        
        text_lower = text.lower().strip()
        for pattern in skip_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # For very short text (3-10 chars), be more permissive if it looks like a heading
        if len(text) < 10:
            # Allow if it contains letters and looks like a title/heading
            if re.search(r'[a-zA-Z]', text) and not re.match(r'^[^\w]*$', text):
                return True
            return False
        
        # For longer text, check word count and character diversity
        words = text.split()
        if len(words) == 1:
            # Single word - accept if it's long enough and looks meaningful
            if len(text) >= 5 and re.search(r'[a-zA-Z]', text):
                # Check character diversity for single words
                unique_chars = len(set(text.lower()))
                if unique_chars < len(text) * 0.4:  # Higher threshold for single words
                    return False
                return True
            return False
        elif len(words) < 2:
            return False
        
        # Check character diversity (avoid repeated characters)
        unique_chars = len(set(text.lower()))
        if unique_chars < len(text) * 0.2:  # Less than 20% unique characters
            return False
        
        return True
    
    def _is_meaningful_sentence(self, sentence: str) -> bool:
        """Check if a sentence contains meaningful content"""
        if len(sentence.strip()) < 20:
            return False
        
        # Must contain some alphabetic characters
        if not re.search(r'[a-zA-Z]', sentence):
            return False
        
        # Skip sentences that are mostly navigation or UI text
        ui_indicators = [
            'click here', 'read more', 'learn more', 'sign up', 'log in',
            'subscribe', 'follow us', 'share this', 'cookie policy',
            'privacy policy', 'terms of service', 'advertisement'
        ]
        
        sentence_lower = sentence.lower()
        for indicator in ui_indicators:
            if indicator in sentence_lower:
                return False
        
        return True
    
    def _clean_scraped_text_enhanced(self, text: str) -> str:
        """
        Enhanced text cleaning and normalization
        
        Args:
            text: Raw scraped text
            
        Returns:
            Cleaned and normalized text content
        """
        if not text:
            return ""
        
        # Stage 1: Basic whitespace normalization
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Stage 2: Remove common UI/navigation patterns
        text = self._remove_ui_patterns(text)
        
        # Stage 3: Clean up formatting artifacts
        text = self._clean_formatting_artifacts(text)
        
        # Stage 4: Normalize punctuation and spacing
        text = self._normalize_punctuation(text)
        
        # Stage 5: Remove duplicate content
        text = self._remove_duplicate_content(text)
        
        # Stage 6: Final cleanup
        text = self._final_cleanup(text)
        
        return text.strip()
    
    def _remove_ui_patterns(self, text: str) -> str:
        """Remove common UI and navigation patterns"""
        # Comprehensive list of UI patterns to remove
        ui_patterns = [
            # Navigation and menu items
            r'Skip to (?:main )?content',
            r'Jump to (?:main )?content',
            r'Go to (?:main )?content',
            r'Main navigation',
            r'Primary navigation',
            r'Secondary navigation',
            r'Breadcrumb navigation',
            
            # Cookie and privacy notices
            r'Cookie (?:policy|notice|consent|banner)',
            r'Accept (?:all )?cookies',
            r'Manage cookies',
            r'Privacy (?:policy|notice|settings)',
            r'GDPR (?:notice|compliance)',
            r'Data protection',
            
            # Legal and terms
            r'Terms (?:of service|and conditions|of use)',
            r'Legal (?:notice|disclaimer)',
            r'Copyright notice',
            
            # Social and sharing
            r'Share (?:this|on):?',
            r'Follow us (?:on)?',
            r'Subscribe to (?:our )?newsletter',
            r'Join our (?:newsletter|mailing list)',
            r'Social media (?:links|sharing)',
            r'Like us on',
            r'Follow @\w+',
            
            # Comments and interaction
            r'Leave a comment',
            r'Post a comment',
            r'Comments? \(\d+\)',
            r'Reply to this',
            r'Rate this (?:article|post)',
            
            # Related content
            r'Related (?:articles|posts|stories)',
            r'You might also (?:like|enjoy)',
            r'More (?:from|like this)',
            r'Similar (?:articles|content)',
            r'Recommended (?:for you|reading)',
            
            # Advertisements
            r'Advertisement',
            r'Sponsored content',
            r'Promoted (?:content|post)',
            r'Ad(?:s)? by',
            
            # Search and filters
            r'Search (?:for|the site)',
            r'Filter (?:by|results)',
            r'Sort by',
            r'Show (?:more|less|all)',
            
            # User account
            r'(?:Log|Sign) (?:in|up|out)',
            r'Create (?:an )?account',
            r'Register (?:now|here)',
            r'My account',
            r'User (?:profile|settings)',
            
            # Pagination
            r'Page \d+ of \d+',
            r'Next page',
            r'Previous page',
            r'Go to page \d+',
            
            # Timestamps and metadata (when standalone)
            r'^\d{1,2}[:/]\d{1,2}[:/]\d{2,4}$',
            r'^\d{1,2} \w+ \d{4}$',
            r'^Updated:? \d',
            r'^Published:? \d',
            
            # Common form elements
            r'Enter your email',
            r'Email address',
            r'Password',
            r'Confirm password',
            r'Submit',
            r'Reset',
            r'Cancel',
        ]
        
        for pattern in ui_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        return text
    
    def _clean_formatting_artifacts(self, text: str) -> str:
        """Clean up formatting artifacts from HTML conversion"""
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[-]{3,}', '---', text)
        text = re.sub(r'[=]{3,}', '===', text)
        text = re.sub(r'[_]{3,}', '___', text)
        
        # Clean up bullet points and list markers
        text = re.sub(r'^[•·▪▫‣⁃]\s*', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^[\*\-\+]\s+', '• ', text, flags=re.MULTILINE)
        
        # Remove standalone numbers that are likely page numbers or counters
        text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)
        
        # Clean up quotation marks
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"[''']", "'", text)
        
        # Remove HTML entities that might have been missed
        html_entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&hellip;': '...',
            '&mdash;': '—',
            '&ndash;': '–',
        }
        
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)
        
        return text
    
    def _normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation and spacing"""
        # Ensure proper spacing after punctuation
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        text = re.sub(r'([,;:])([A-Za-z])', r'\1 \2', text)
        
        # Remove spaces before punctuation
        text = re.sub(r'\s+([.!?,:;])', r'\1', text)
        
        # Normalize multiple spaces
        text = re.sub(r' {2,}', ' ', text)
        
        # Clean up line breaks - max 2 consecutive newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove trailing spaces on lines
        text = re.sub(r' +\n', '\n', text)
        
        return text
    
    def _remove_duplicate_content(self, text: str) -> str:
        """Remove duplicate sentences and paragraphs"""
        lines = text.split('\n')
        unique_lines = []
        seen_lines = set()
        
        for line in lines:
            line = line.strip()
            if not line:
                unique_lines.append('')
                continue
            
            # Create a normalized version for comparison
            normalized = re.sub(r'\s+', ' ', line.lower())
            
            # Skip if we've seen this line before (or very similar)
            if normalized not in seen_lines:
                seen_lines.add(normalized)
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup pass"""
        # Remove very short lines that are likely artifacts
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Keep empty lines for paragraph separation
            if not line:
                cleaned_lines.append('')
                continue
            
            # Skip very short lines unless they look like headings or important content
            if len(line) < 5:
                continue
            
            # Skip lines that are mostly punctuation or numbers
            if re.match(r'^[^\w]*$', line) or re.match(r'^\d+[^\w]*$', line):
                continue
            
            cleaned_lines.append(line)
        
        # Join and do final whitespace cleanup
        text = '\n'.join(cleaned_lines)
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines
        
        return text.strip()
    
    def _extract_title_from_url(self, url: str) -> str:
        """
        Extract a meaningful title from URL for content generation
        
        Args:
            url: Source URL
            
        Returns:
            Extracted title
        """
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace('www.', '')
            path_parts = [part for part in parsed_url.path.split('/') if part and part != 'index.html']
            
            if path_parts:
                # Use the last meaningful path component
                title_part = path_parts[-1]
                
                # Remove file extensions
                title_part = re.sub(r'\.[a-zA-Z0-9]+$', '', title_part)
                
                # Convert URL-friendly format to readable title
                title_part = title_part.replace('-', ' ').replace('_', ' ')
                title_part = re.sub(r'[^\w\s]', ' ', title_part)  # Remove special chars
                title_part = re.sub(r'\s+', ' ', title_part).strip()  # Normalize spaces
                
                if title_part and len(title_part) > 2:
                    # Capitalize properly
                    title_part = ' '.join(word.capitalize() for word in title_part.split())
                    return f"Content from {domain}: {title_part}"
            
            # If no meaningful path, try to extract from domain
            domain_parts = domain.split('.')
            if len(domain_parts) > 2:
                # Use subdomain if it looks meaningful
                subdomain = domain_parts[0]
                if subdomain not in ['www', 'blog', 'news', 'docs', 'support']:
                    return f"Content from {subdomain.capitalize()} ({domain})"
            
            return f"Content from {domain}"
                
        except Exception as e:
            logger.warning(f"Error extracting title from URL {url}: {str(e)}")
            return f"Web Content from {url}"
    
    async def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """
        Get the status of a content generation request
        
        Args:
            generation_id: Unique identifier for the generation
            
        Returns:
            Generation status information
        """
        if generation_id not in self.generations:
            raise ValueError(f"Generation {generation_id} not found")
        
        return self.generations[generation_id]
    
    async def list_recent_generations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent content generations
        
        Args:
            limit: Maximum number of generations to return
            
        Returns:
            List of recent generation summaries
        """
        try:
            # Get recent generations (sorted by creation time)
            recent = sorted(
                self.generations.items(),
                key=lambda x: x[1].get('created_at', datetime.min),
                reverse=True
            )[:limit]
            
            # Return summary information
            return [
                {
                    "generation_id": gen_id,
                    "status": gen_data.get("status", "unknown"),
                    "input_type": gen_data.get("input_type", "unknown"),
                    "created_at": gen_data.get("created_at"),
                    "completed_at": gen_data.get("completed_at"),
                    "topic": gen_data.get("educational_script", {}).get("title") if gen_data.get("educational_script") else None
                }
                for gen_id, gen_data in recent
            ]
            
        except Exception as e:
            logger.error(f"Error listing recent generations: {str(e)}")
            return []
    
    def _create_mock_response(self, generation_id: str, title: str) -> Dict[str, Any]:
        """Create a mock response for testing purposes"""
        educational_script = {
            "title": title,
            "learning_objectives": [
                {"objective": "Understand the main concepts", "level": "understand", "measurable": True},
                {"objective": "Apply knowledge to examples", "level": "apply", "measurable": True}
            ],
            "sections": [
                {
                    "title": "Introduction",
                    "content": "This is an introduction to the topic.",
                    "animations": ["intro_animation"],
                    "duration_minutes": 5
                },
                {
                    "title": "Main Content",
                    "content": "This is the main educational content.",
                    "animations": ["main_animation"],
                    "duration_minutes": 10
                }
            ],
            "assessments": [
                {
                    "type": "quiz",
                    "title": "Knowledge Check",
                    "questions": [
                        {"question": "What is the main concept?", "type": "open_ended", "points": 10},
                        {"question": "How does this apply?", "type": "open_ended", "points": 10}
                    ],
                    "rubric": "Basic understanding assessment"
                }
            ],
            "metadata": {
                "difficulty_level": "intermediate",
                "target_audience": "general",
                "estimated_duration": "15 minutes"
            }
        }
        
        return {
            "generation_id": generation_id,
            "status": "completed",
            "educational_script": educational_script,
            "created_at": datetime.now(),
            "completed_at": datetime.now()
        }
    
    async def generate_manim_code(self, generation_id: str) -> Dict[str, Any]:
        """
        Generate Manim code from an existing educational script
        
        Args:
            generation_id: ID of the completed content generation
            
        Returns:
            Dictionary containing Manim code and validation results
        """
        try:
            # Get the generation result
            if generation_id not in self.generations:
                raise ValueError(f"Generation {generation_id} not found")
            
            generation = self.generations[generation_id]
            
            if generation.get("status") != "completed":
                raise ValueError(f"Generation {generation_id} is not completed")
            
            educational_script = generation.get("educational_script")
            if not educational_script:
                raise ValueError(f"No educational script found for generation {generation_id}")
            
            logger.info(f"Generating Manim code for generation {generation_id}")
            
            # Generate Manim code
            manim_code = self.manim_generator.generate_manim_code(educational_script)
            
            # Validate the generated code
            validation_result = self.manim_generator.validate_manim_code(manim_code)
            
            # Store the result
            manim_result = {
                "generation_id": generation_id,
                "manim_code": manim_code,
                "validation": validation_result,
                "created_at": datetime.now(),
                "estimated_duration": validation_result.get("estimated_duration", 30)
            }
            
            # Update the generation with Manim code
            self.generations[generation_id]["manim_code"] = manim_result
            
            logger.info(f"Successfully generated Manim code for {generation_id}")
            return manim_result
            
        except Exception as e:
            logger.error(f"Error generating Manim code: {str(e)}")
            return {
                "generation_id": generation_id,
                "error": str(e),
                "created_at": datetime.now()
            }