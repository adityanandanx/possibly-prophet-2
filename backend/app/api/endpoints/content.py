"""
Content generation endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Dict, Any, Optional, List
from pathlib import Path
import magic
import os
import aiofiles
import tempfile

from ...models.content import ContentRequest, ContentResponse, ContentInput
from ...services.content_service import ContentService
from ...services.content_validator import ContentValidator
from ...core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize content service and validator
content_service = ContentService()
content_validator = ContentValidator()


async def validate_file(file: UploadFile) -> None:
    """
    Comprehensive validation for uploaded files

    Args:
        file: Uploaded file to validate

    Raises:
        HTTPException: If file validation fails
    """
    # Check if file is provided
    if not file or not file.filename:
        raise HTTPException(
            status_code=400, detail="No file provided or filename is empty"
        )

    # Check file size by reading content
    content = await file.read()
    file_size = len(content)

    # Reset file pointer for later use
    await file.seek(0)

    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB, got {file_size / (1024*1024):.1f}MB",
        )

    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file_ext}'. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}",
        )

    # Check MIME type using python-magic for more accurate detection
    try:
        # Create temporary file to check MIME type
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Detect MIME type
        mime_type = magic.from_file(temp_file_path, mime=True)

        # Clean up temporary file
        os.unlink(temp_file_path)

        # Reset file pointer again
        await file.seek(0)

        if mime_type not in settings.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported MIME type '{mime_type}'. File content doesn't match expected format for '{file_ext}' files.",
            )

    except Exception as e:
        logger.warning(f"Could not detect MIME type for file {file.filename}: {str(e)}")
        # If MIME detection fails, rely on file extension validation
        pass

    # Additional validation for specific file types
    if file_ext == ".pdf":
        await _validate_pdf_file(content)
    elif file_ext in [".doc", ".docx"]:
        await _validate_doc_file(content, file_ext)
    elif file_ext == ".txt":
        await _validate_text_file(content)


async def _validate_pdf_file(content: bytes) -> None:
    """Validate PDF file content"""
    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=415, detail="File does not appear to be a valid PDF"
        )


async def _validate_doc_file(content: bytes, file_ext: str) -> None:
    """Validate DOC/DOCX file content"""
    if file_ext == ".docx":
        # DOCX files are ZIP archives with specific structure
        if not content.startswith(b"PK"):
            raise HTTPException(
                status_code=415,
                detail="File does not appear to be a valid DOCX document",
            )
    elif file_ext == ".doc":
        # DOC files have specific binary signatures
        if not (
            content.startswith(b"\xd0\xcf\x11\xe0")
            or content.startswith(b"\x0d\x44\x4f\x43")
        ):
            raise HTTPException(
                status_code=415,
                detail="File does not appear to be a valid DOC document",
            )


async def _validate_text_file(content: bytes) -> None:
    """Validate text file content"""
    try:
        # Try to decode as UTF-8 first (most common)
        text_content = content.decode("utf-8")
        if len(text_content.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Text file content too short. Please provide at least 10 characters.",
            )
    except UnicodeDecodeError:
        try:
            # Try latin-1 encoding (common for older files)
            text_content = content.decode("latin-1")
            # Check if the decoded content looks like valid text
            # If it contains too many control characters or null bytes, it's likely not valid text
            control_chars = sum(
                1 for c in text_content if ord(c) < 32 and c not in "\t\n\r"
            )
            if (
                control_chars > len(text_content) * 0.1
            ):  # More than 10% control characters
                raise HTTPException(
                    status_code=415,
                    detail="Text file contains invalid characters and cannot be decoded",
                )
            if len(text_content.strip()) < 10:
                raise HTTPException(
                    status_code=400,
                    detail="Text file content too short. Please provide at least 10 characters.",
                )
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=415,
                detail="Text file contains invalid characters and cannot be decoded",
            )


@router.post("/generate", response_model=ContentResponse)
async def generate_content(request: ContentRequest) -> ContentResponse:
    """
    Generate educational content from multiple inputs

    Args:
        request: Content generation request with multiple inputs

    Returns:
        Generated educational content response
    """
    try:
        logger.info(f"Generating content for topic: {request.topic}")

        # Validate that we have at least one input
        if not request.inputs:
            raise HTTPException(
                status_code=400, detail="At least one content input is required."
            )

        # Validate each text input
        total_content_length = 0
        for i, content_input in enumerate(request.inputs):
            if content_input.content_type == "text":
                content_length = len(content_input.content.strip())
                if content_length < 10:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Content input {i+1} too short. Please provide at least 10 characters.",
                    )
                total_content_length += content_length

        # Check total content length
        if total_content_length > 100000:  # 100KB text limit
            raise HTTPException(
                status_code=400,
                detail="Total content too long. Please limit to 100,000 characters.",
            )

        # Generate content using the content service
        result = await content_service.generate_from_inputs(
            inputs=request.inputs,
            topic=request.topic,
            difficulty_level=request.difficulty_level,
            target_audience=request.target_audience,
            learning_goals=request.learning_goals,
            preferences=request.preferences,
        )

        return ContentResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Content generation failed: {str(e)}"
        )


@router.post("/text", response_model=ContentResponse)
async def generate_from_text_prompt(
    content: str = Form(..., description="Text content to process"),
    topic: Optional[str] = Form(None, description="Optional topic override"),
    difficulty_level: str = Form(
        "intermediate", description="Content difficulty level"
    ),
    target_audience: str = Form(..., description="Target audience for content"),
    learning_goals: str = Form("", description="Comma-separated learning goals"),
) -> ContentResponse:
    """
    Generate educational content from a simple text prompt

    This is a simplified endpoint for text-only input that creates a ContentRequest
    internally and processes it through the main generation pipeline.

    Args:
        content: Raw text content to process
        topic: Optional topic override
        difficulty_level: Content difficulty level
        target_audience: Target audience for content
        learning_goals: Comma-separated learning goals

    Returns:
        Generated educational content response
    """
    try:
        logger.info(f"Generating content from text prompt for topic: {topic}")

        # Validate content length
        if len(content.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Content too short. Please provide at least 10 characters.",
            )

        if len(content) > 100000:  # 100KB text limit
            raise HTTPException(
                status_code=400,
                detail="Content too long. Please limit to 100,000 characters.",
            )

        # Parse learning goals
        parsed_learning_goals = []
        if learning_goals.strip():
            parsed_learning_goals = [
                goal.strip() for goal in learning_goals.split(",") if goal.strip()
            ]

        # Create ContentRequest from simple inputs
        content_request = ContentRequest(
            inputs=[
                ContentInput(
                    content_type="text",
                    content=content,
                    metadata={"source": "text_prompt"},
                )
            ],
            topic=topic,
            difficulty_level=difficulty_level,
            target_audience=target_audience,
            learning_goals=parsed_learning_goals,
            preferences={},
        )

        # Use the main generate_content function
        return await generate_content(content_request)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating content from text prompt: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Text prompt processing failed: {str(e)}"
        )


@router.post("/upload", response_model=ContentResponse)
async def upload_and_generate(
    file: UploadFile = File(
        ..., description="Educational content file (PDF, DOC, DOCX, TXT)"
    ),
    topic: Optional[str] = Form(None, description="Optional topic override"),
    difficulty_level: str = Form(
        "intermediate", description="Content difficulty level"
    ),
    target_audience: str = Form(..., description="Target audience for content"),
    learning_goals: str = Form("", description="Comma-separated learning goals"),
) -> ContentResponse:
    """
    Upload a file and generate educational content

    Accepts educational content files in supported formats and generates
    structured educational materials including learning objectives, content sections,
    and assessments.

    Supported file types:
    - PDF (.pdf): Portable Document Format files
    - DOC (.doc): Microsoft Word 97-2003 documents
    - DOCX (.docx): Microsoft Word 2007+ documents
    - TXT (.txt): Plain text files

    Args:
        file: Uploaded file (PDF, DOC, DOCX, TXT)
        topic: Optional topic override for the generated content
        difficulty_level: Content difficulty level (beginner, intermediate, advanced)
        target_audience: Target audience for content (e.g., "high school students")
        learning_goals: Comma-separated learning goals

    Returns:
        Generated educational content response with script, metadata, and generation ID

    Raises:
        HTTPException:
            - 400: Invalid file, empty file, or validation errors
            - 413: File too large (exceeds 10MB limit)
            - 415: Unsupported file type or invalid file format
            - 422: Invalid form parameters
            - 500: Internal processing error
    """
    try:
        logger.info(
            f"Processing uploaded file: {file.filename} (size: {file.size if hasattr(file, 'size') else 'unknown'})"
        )

        # Comprehensive file validation
        await validate_file(file)

        # Parse learning goals
        parsed_learning_goals = []
        if learning_goals.strip():
            parsed_learning_goals = [
                goal.strip() for goal in learning_goals.split(",") if goal.strip()
            ]

        # Validate difficulty level
        valid_difficulty_levels = ["beginner", "intermediate", "advanced"]
        if difficulty_level not in valid_difficulty_levels:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid difficulty level '{difficulty_level}'. Must be one of: {', '.join(valid_difficulty_levels)}",
            )

        # Validate target audience (basic check)
        if not target_audience.strip():
            raise HTTPException(
                status_code=422, detail="Target audience cannot be empty"
            )

        if len(target_audience) > 200:
            raise HTTPException(
                status_code=422,
                detail="Target audience description too long (max 200 characters)",
            )

        # Generate content from uploaded file
        result = await content_service.generate_from_file(
            file=file,
            topic=topic,
            difficulty_level=difficulty_level,
            target_audience=target_audience,
            learning_goals=parsed_learning_goals,
        )

        logger.info(
            f"Successfully processed file: {file.filename}, generation_id: {result.get('generation_id')}"
        )
        return ContentResponse(**result)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error processing uploaded file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")


@router.post("/url", response_model=ContentResponse)
async def generate_from_url(
    url: str = Form(..., description="Web URL to process"),
    topic: Optional[str] = Form(None, description="Optional topic override"),
    difficulty_level: str = Form(
        "intermediate", description="Content difficulty level"
    ),
    target_audience: str = Form(..., description="Target audience for content"),
    learning_goals: str = Form("", description="Comma-separated learning goals"),
) -> ContentResponse:
    """
    Generate educational content from a web URL

    Scrapes content from the provided URL and generates structured educational materials
    including learning objectives, content sections, and assessments.

    Supported URL types:
    - Educational websites and articles
    - Blog posts and tutorials
    - Documentation pages
    - News articles with educational content

    Args:
        url: Web URL to process (must start with http:// or https://)
        topic: Optional topic override for the generated content
        difficulty_level: Content difficulty level (beginner, intermediate, advanced)
        target_audience: Target audience for content (e.g., "high school students")
        learning_goals: Comma-separated learning goals

    Returns:
        Generated educational content response with script, metadata, and generation ID

    Raises:
        HTTPException:
            - 400: Invalid URL format or insufficient content
            - 403: Access forbidden by the website
            - 404: URL not found
            - 408: Request timeout
            - 415: Unsupported content type
            - 422: Invalid form parameters
            - 503: Connection error
            - 500: Internal processing error
    """
    try:
        logger.info(f"Processing URL: {url}")

        # Enhanced URL validation
        if not url.strip():
            raise HTTPException(status_code=400, detail="URL cannot be empty")

        # Normalize URL
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            raise HTTPException(
                status_code=400,
                detail="Invalid URL format. Must start with http:// or https://",
            )

        # Check URL length
        if len(url) > 2048:
            raise HTTPException(
                status_code=400,
                detail="URL too long. Maximum length is 2048 characters.",
            )

        # Basic URL structure validation
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                raise HTTPException(
                    status_code=400, detail="Invalid URL format. Missing domain name."
                )
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid URL format")

        # Validate difficulty level
        valid_difficulty_levels = ["beginner", "intermediate", "advanced"]
        if difficulty_level not in valid_difficulty_levels:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid difficulty level '{difficulty_level}'. Must be one of: {', '.join(valid_difficulty_levels)}",
            )

        # Validate target audience
        if not target_audience.strip():
            raise HTTPException(
                status_code=422, detail="Target audience cannot be empty"
            )

        if len(target_audience) > 200:
            raise HTTPException(
                status_code=422,
                detail="Target audience description too long (max 200 characters)",
            )

        # Parse learning goals
        parsed_learning_goals = []
        if learning_goals.strip():
            parsed_learning_goals = [
                goal.strip() for goal in learning_goals.split(",") if goal.strip()
            ]
            if len(parsed_learning_goals) > 10:
                raise HTTPException(
                    status_code=422, detail="Too many learning goals. Maximum is 10."
                )

        # Generate content from URL
        result = await content_service.generate_from_url(
            url=url,
            topic=topic,
            difficulty_level=difficulty_level,
            target_audience=target_audience,
            learning_goals=parsed_learning_goals,
        )

        logger.info(
            f"Successfully processed URL: {url}, generation_id: {result.get('generation_id')}"
        )
        return ContentResponse(**result)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error processing URL {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"URL processing failed: {str(e)}")


@router.get("/status/{generation_id}")
async def get_generation_status(generation_id: str) -> Dict[str, Any]:
    """
    Get the status of a content generation request

    Args:
        generation_id: Unique identifier for the generation request

    Returns:
        Generation status information
    """
    try:
        # Validate generation_id format
        if not generation_id or len(generation_id) < 10:
            raise HTTPException(status_code=400, detail="Invalid generation ID format")

        status = await content_service.get_generation_status(generation_id)
        return status

    except ValueError as e:
        logger.error(f"Generation not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting generation status: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Status retrieval failed: {str(e)}"
        )


@router.get("/")
async def list_generations() -> Dict[str, Any]:
    """
    List recent content generations (for development/debugging)

    Returns:
        List of recent generations
    """
    try:
        generations = await content_service.list_recent_generations()
        return {"generations": generations, "count": len(generations)}
    except Exception as e:
        logger.error(f"Error listing generations: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list generations: {str(e)}"
        )


@router.post("/validate/text")
async def validate_text_content(
    content: str = Form(..., description="Text content to validate"),
    content_type: str = Form("text", description="Type of content"),
) -> Dict[str, Any]:
    """
    Validate text content without generating educational materials

    This endpoint allows users to validate their content before submitting
    it for full educational content generation. It provides feedback on
    content quality, educational suitability, and potential issues.

    Args:
        content: Text content to validate
        content_type: Type of content (text, extracted_text, etc.)

    Returns:
        Validation result with quality metrics and recommendations
    """
    try:
        logger.info(f"Validating text content: {len(content)} characters")

        # Validate content
        validation_result = await content_validator.validate_text_content(
            content, content_type, {"endpoint": "validate_text"}
        )

        # Prepare response
        response = {
            "is_valid": validation_result.is_valid,
            "content_length": len(content),
            "sanitized_content_length": (
                len(validation_result.sanitized_content)
                if validation_result.sanitized_content
                else 0
            ),
            "warnings": validation_result.warnings,
            "errors": validation_result.errors,
            "quality_metrics": validation_result.metadata,
            "content_hash": validation_result.content_hash,
            "recommendations": [],
        }

        # Add recommendations based on validation results
        if validation_result.metadata.get("quality_score", 0) < 0.5:
            response["recommendations"].append(
                "Consider adding more detailed explanations and examples"
            )

        if validation_result.metadata.get("educational_score", 0) < 0.3:
            response["recommendations"].append(
                "Add more educational context and learning-focused language"
            )

        if validation_result.metadata.get("word_count", 0) < 100:
            response["recommendations"].append(
                "Content is quite short - consider expanding with more details"
            )

        if not validation_result.metadata.get("has_structure", False):
            response["recommendations"].append(
                "Consider adding headings or bullet points to improve structure"
            )

        logger.info(
            f"Text validation completed: valid={validation_result.is_valid}, quality={validation_result.metadata.get('quality_score', 0):.2f}"
        )
        return response

    except Exception as e:
        logger.error(f"Error validating text content: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Content validation failed: {str(e)}"
        )


@router.post("/validate/url")
async def validate_url_content(
    url: str = Form(..., description="URL to validate")
) -> Dict[str, Any]:
    """
    Validate URL format and accessibility without scraping content

    This endpoint validates URL format, checks for security issues,
    and provides recommendations for URL-based content generation.

    Args:
        url: URL to validate

    Returns:
        URL validation result with security and accessibility information
    """
    try:
        logger.info(f"Validating URL: {url}")

        # Validate URL
        validation_result = await content_validator.validate_url_content(url)

        # Prepare response
        response = {
            "is_valid": validation_result.is_valid,
            "url": url,
            "warnings": validation_result.warnings,
            "errors": validation_result.errors,
            "url_metadata": validation_result.metadata,
            "recommendations": [],
        }

        # Add recommendations based on validation results
        if validation_result.metadata.get("domain"):
            domain = validation_result.metadata["domain"]
            if any(
                indicator in domain.lower()
                for indicator in ["blog", "wiki", "edu", "org"]
            ):
                response["recommendations"].append(
                    "This appears to be an educational or informational site - good for content generation"
                )
            elif any(
                indicator in domain.lower()
                for indicator in ["shop", "store", "buy", "sell"]
            ):
                response["recommendations"].append(
                    "This appears to be a commercial site - may have limited educational content"
                )

        if validation_result.warnings:
            response["recommendations"].append(
                "Review warnings before proceeding with content extraction"
            )

        logger.info(
            f"URL validation completed: valid={validation_result.is_valid}, domain={validation_result.metadata.get('domain', 'unknown')}"
        )
        return response

    except Exception as e:
        logger.error(f"Error validating URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"URL validation failed: {str(e)}")


@router.post("/validate/batch")
async def validate_batch_content(request: ContentRequest) -> Dict[str, Any]:
    """
    Validate multiple content inputs in batch

    This endpoint validates all content inputs in a ContentRequest
    without generating educational materials. Useful for pre-validation
    before submitting for full content generation.

    Args:
        request: Content request with multiple inputs to validate

    Returns:
        Batch validation results for all inputs
    """
    try:
        logger.info(f"Validating batch content: {len(request.inputs)} inputs")

        # Prepare content items for validation
        content_items = []
        for i, content_input in enumerate(request.inputs):
            content_items.append(
                {
                    "content_type": content_input.content_type,
                    "content": content_input.content,
                    "metadata": {
                        **content_input.metadata,
                        "input_index": i,
                        "endpoint": "validate_batch",
                    },
                }
            )

        # Validate all content items
        validation_results = await content_validator.validate_batch_content(
            content_items
        )

        # Prepare response
        response = {
            "total_inputs": len(request.inputs),
            "valid_inputs": sum(1 for result in validation_results if result.is_valid),
            "invalid_inputs": sum(
                1 for result in validation_results if not result.is_valid
            ),
            "results": [],
            "overall_recommendations": [],
        }

        # Process individual results
        for i, result in enumerate(validation_results):
            input_result = {
                "input_index": i,
                "content_type": request.inputs[i].content_type,
                "is_valid": result.is_valid,
                "warnings": result.warnings,
                "errors": result.errors,
                "quality_metrics": result.metadata if result.is_valid else {},
                "content_hash": result.content_hash,
            }
            response["results"].append(input_result)

        # Add overall recommendations
        if response["invalid_inputs"] > 0:
            response["overall_recommendations"].append(
                f"{response['invalid_inputs']} inputs failed validation - review errors before proceeding"
            )

        total_warnings = sum(len(result.warnings) for result in validation_results)
        if total_warnings > 0:
            response["overall_recommendations"].append(
                f"{total_warnings} warnings found across all inputs - review for quality improvements"
            )

        if response["valid_inputs"] > 0:
            avg_quality = (
                sum(
                    result.metadata.get("quality_score", 0)
                    for result in validation_results
                    if result.is_valid
                )
                / response["valid_inputs"]
            )
            if avg_quality < 0.5:
                response["overall_recommendations"].append(
                    "Average content quality is low - consider improving content before generation"
                )

        logger.info(
            f"Batch validation completed: {response['valid_inputs']}/{response['total_inputs']} valid inputs"
        )
        return response

    except Exception as e:
        logger.error(f"Error validating batch content: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Batch validation failed: {str(e)}"
        )


def get_content_service() -> ContentService:
    """Dependency to get content service instance"""
    return content_service


@router.post("/generate/manim/{generation_id}")
async def generate_manim_code(
    generation_id: str, content_service: ContentService = Depends(get_content_service)
):
    """
    Generate Manim code from an existing educational script

    Args:
        generation_id: ID of the completed content generation

    Returns:
        Manim code and validation results
    """
    try:
        result = await content_service.generate_manim_code(generation_id)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in Manim generation endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/render/video/{generation_id}")
async def render_video(
    generation_id: str,
    quality: str = "medium_quality",
    frame_rate: int = 30,
    content_service: ContentService = Depends(get_content_service),
):
    """
    Render Manim code to video and upload to S3.

    This endpoint:
    1. Takes the generated Manim code
    2. Executes it with Manim to render a video
    3. Uploads the video to S3
    4. Returns the S3 URL and local URL for playback

    Args:
        generation_id: ID of the generation with Manim code
        quality: Video quality - one of: low_quality, medium_quality, high_quality, production_quality
        frame_rate: Video frame rate (default: 30)

    Returns:
        Video URL (S3 and local) and render metadata
    """
    try:
        result = await content_service.render_video(
            generation_id=generation_id,
            quality=quality,
            frame_rate=frame_rate,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=400, detail=result.get("error", "Video rendering failed")
            )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in video render endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/generation/{generation_id}")
async def get_generation_details(
    generation_id: str, content_service: ContentService = Depends(get_content_service)
):
    """
    Get the detailed results of a content generation

    Args:
        generation_id: ID of the generation to retrieve

    Returns:
        Complete generation results including educational script and any generated code
    """
    try:
        result = await content_service.get_generation_status(generation_id)
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting generation details: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/generations/recent")
async def list_recent_generations_detailed(
    limit: int = 10, content_service: ContentService = Depends(get_content_service)
):
    """
    List recent content generations with summary information

    Args:
        limit: Maximum number of generations to return

    Returns:
        List of recent generation summaries
    """
    try:
        result = await content_service.list_recent_generations(limit)
        return {"generations": result, "count": len(result)}

    except Exception as e:
        logger.error(f"Error listing recent generations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
