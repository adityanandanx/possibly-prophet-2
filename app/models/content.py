"""
Content-related data models
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

class DifficultyLevel(str, Enum):
    """Difficulty level enumeration"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class ContentType(str, Enum):
    """Content type enumeration"""
    TEXT = "text"
    FILE = "file"
    URL = "url"

class GenerationStatus(str, Enum):
    """Generation status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class BloomLevel(str, Enum):
    """Bloom's taxonomy levels"""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"

class AssessmentType(str, Enum):
    """Assessment type enumeration"""
    QUIZ = "quiz"
    EXERCISE = "exercise"
    PROJECT = "project"
    DISCUSSION = "discussion"

class ContentInput(BaseModel):
    """Input content model"""
    content_type: ContentType = Field(..., description="Type of content input")
    content: str = Field(..., description="Raw content or file path/URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content_type": "text",
                "content": "Photosynthesis is the process by which plants convert sunlight into energy...",
                "metadata": {"source": "textbook", "chapter": "3"}
            }
        }
    )

class ContentRequest(BaseModel):
    """Request model for content generation"""
    inputs: List[ContentInput] = Field(..., description="List of content inputs to process")
    topic: Optional[str] = Field(None, description="Topic or title for the content")
    difficulty_level: DifficultyLevel = Field(DifficultyLevel.INTERMEDIATE, description="Difficulty level")
    target_audience: str = Field("general", description="Target audience for the content")
    learning_goals: List[str] = Field(default_factory=list, description="Specific learning goals")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Generation preferences")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "inputs": [
                    {
                        "content_type": "text",
                        "content": "Photosynthesis is the process by which plants convert sunlight into energy...",
                        "metadata": {}
                    }
                ],
                "topic": "Photosynthesis in Plants",
                "difficulty_level": "intermediate",
                "target_audience": "high school students",
                "learning_goals": ["Understand photosynthesis process", "Identify key components"],
                "preferences": {"include_animations": True, "duration_minutes": 30}
            }
        }
    )

class LearningObjective(BaseModel):
    """Learning objective model"""
    objective: str = Field(..., description="Learning objective description")
    bloom_level: BloomLevel = Field(..., description="Bloom's taxonomy level")
    measurable: bool = Field(True, description="Whether the objective is measurable")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "objective": "Students will be able to explain the process of photosynthesis",
                "bloom_level": "understand",
                "measurable": True
            }
        }
    )

class AnimationSpec(BaseModel):
    """Animation specification model"""
    name: str = Field(..., description="Animation name/identifier")
    description: str = Field(..., description="Animation description")
    concepts: List[str] = Field(default_factory=list, description="Concepts being animated")
    duration_seconds: Optional[int] = Field(None, description="Animation duration in seconds")
    complexity: str = Field("medium", description="Animation complexity: simple, medium, complex")

class ContentSection(BaseModel):
    """Content section model"""
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    learning_objectives: List[str] = Field(default_factory=list, description="Section-specific objectives")
    animations: List[AnimationSpec] = Field(default_factory=list, description="Animation specifications")
    duration_minutes: Optional[int] = Field(None, description="Estimated duration in minutes")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites for this section")

class AssessmentQuestion(BaseModel):
    """Assessment question model"""
    question: str = Field(..., description="Question text")
    question_type: str = Field(..., description="Question type: multiple_choice, short_answer, essay")
    options: List[str] = Field(default_factory=list, description="Answer options for multiple choice")
    correct_answer: Optional[str] = Field(None, description="Correct answer")
    explanation: Optional[str] = Field(None, description="Answer explanation")
    difficulty: DifficultyLevel = Field(DifficultyLevel.INTERMEDIATE, description="Question difficulty")

class Assessment(BaseModel):
    """Assessment model"""
    type: AssessmentType = Field(..., description="Assessment type")
    title: str = Field(..., description="Assessment title")
    questions: List[AssessmentQuestion] = Field(default_factory=list, description="Assessment questions")
    rubric: Optional[str] = Field(None, description="Assessment rubric")
    points: Optional[int] = Field(None, description="Total points possible")
    time_limit_minutes: Optional[int] = Field(None, description="Time limit in minutes")

class EducationalScript(BaseModel):
    """Educational script model"""
    title: str = Field(..., description="Content title")
    description: Optional[str] = Field(None, description="Content description")
    learning_objectives: List[LearningObjective] = Field(default_factory=list)
    sections: List[ContentSection] = Field(default_factory=list)
    assessments: List[Assessment] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    estimated_duration_minutes: Optional[int] = Field(None, description="Total estimated duration")
    prerequisites: List[str] = Field(default_factory=list, description="Course prerequisites")
    tags: List[str] = Field(default_factory=list, description="Content tags")

class GenerationMetadata(BaseModel):
    """Generation metadata model"""
    agent_versions: Dict[str, str] = Field(default_factory=dict, description="Agent versions used")
    processing_time_seconds: Optional[float] = Field(None, description="Total processing time")
    input_tokens: Optional[int] = Field(None, description="Input tokens processed")
    output_tokens: Optional[int] = Field(None, description="Output tokens generated")
    quality_score: Optional[float] = Field(None, description="Content quality score")

class ContentResponse(BaseModel):
    """Response model for generated content"""
    generation_id: str = Field(..., description="Unique identifier for this generation")
    status: GenerationStatus = Field(..., description="Generation status")
    educational_script: Optional[EducationalScript] = Field(None, description="Generated educational script")
    manim_code: Optional[str] = Field(None, description="Generated Manim animation code")
    html_content: Optional[str] = Field(None, description="Generated HTML presentation")
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(None)
    error_message: Optional[str] = Field(None, description="Error message if generation failed")
    generation_metadata: Optional[GenerationMetadata] = Field(None, description="Generation metadata")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "generation_id": "gen_123456",
                "status": "completed",
                "educational_script": {
                    "title": "Photosynthesis in Plants",
                    "description": "An introduction to the process of photosynthesis",
                    "learning_objectives": [
                        {
                            "objective": "Students will be able to explain the process of photosynthesis",
                            "bloom_level": "understand",
                            "measurable": True
                        }
                    ],
                    "sections": [
                        {
                            "title": "Introduction to Photosynthesis",
                            "content": "Photosynthesis is...",
                            "animations": [
                                {
                                    "name": "chloroplast_animation",
                                    "description": "Animation showing chloroplast structure",
                                    "concepts": ["chloroplast", "thylakoid", "stroma"],
                                    "duration_seconds": 30,
                                    "complexity": "medium"
                                }
                            ],
                            "duration_minutes": 5
                        }
                    ],
                    "assessments": [
                        {
                            "type": "quiz",
                            "title": "Photosynthesis Quiz",
                            "questions": [
                                {
                                    "question": "What is photosynthesis?",
                                    "question_type": "short_answer",
                                    "difficulty": "intermediate"
                                }
                            ]
                        }
                    ]
                },
                "created_at": "2024-01-01T12:00:00Z"
            }
        }
    )

# Input storage models
class StoredInputMetadata(BaseModel):
    """Metadata for stored input"""
    storage_id: str = Field(..., description="Unique storage identifier")
    content_type: ContentType = Field(..., description="Type of content")
    content_hash: str = Field(..., description="SHA-256 hash of content")
    stored_at: datetime = Field(..., description="When the input was stored")
    generation_id: Optional[str] = Field(None, description="Associated generation ID")
    content_length: int = Field(..., description="Length of content in characters")
    validation_status: Optional[bool] = Field(None, description="Whether validation passed")
    processing_status: Optional[str] = Field(None, description="Processing status")

class StoredInput(BaseModel):
    """Complete stored input with content and metadata"""
    storage_id: str = Field(..., description="Unique storage identifier")
    content: str = Field(..., description="Stored content")
    metadata: StoredInputMetadata = Field(..., description="Input metadata")
    similarity_score: Optional[float] = Field(None, description="Similarity score for search results")
    search_snippet: Optional[str] = Field(None, description="Content snippet for search results")

class InputSearchRequest(BaseModel):
    """Request model for searching stored inputs"""
    query: str = Field(..., description="Search query text")
    content_type: Optional[ContentType] = Field(None, description="Filter by content type")
    generation_id: Optional[str] = Field(None, description="Filter by generation ID")
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)

class InputListRequest(BaseModel):
    """Request model for listing stored inputs"""
    content_type: Optional[ContentType] = Field(None, description="Filter by content type")
    generation_id: Optional[str] = Field(None, description="Filter by generation ID")
    limit: int = Field(50, description="Maximum number of results", ge=1, le=200)
    offset: int = Field(0, description="Number of results to skip", ge=0)

class InputStorageStats(BaseModel):
    """Storage statistics model"""
    total_inputs: int = Field(..., description="Total number of stored inputs")
    content_type_distribution: Dict[str, int] = Field(..., description="Count by content type")
    total_content_size_bytes: int = Field(..., description="Total content size in bytes")
    total_content_size_mb: float = Field(..., description="Total content size in MB")
    vector_db_stats: Dict[str, Any] = Field(..., description="Vector database statistics")
    file_storage_stats: Dict[str, Any] = Field(..., description="File storage statistics")
    storage_directory: str = Field(..., description="Storage directory path")

class InputHistoryEntry(BaseModel):
    """Entry in input processing history"""
    storage_id: str = Field(..., description="Storage identifier")
    stored_at: str = Field(..., description="Storage timestamp")
    generation_id: Optional[str] = Field(None, description="Associated generation ID")
    validation_result: Dict[str, Any] = Field(default_factory=dict, description="Validation results")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")

# File upload models
class FileUploadResponse(BaseModel):
    """Response model for file uploads"""
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="File MIME type")
    uploaded_at: datetime = Field(default_factory=datetime.now)
    processed: bool = Field(False, description="Whether file has been processed")

class URLProcessingRequest(BaseModel):
    """Request model for URL processing"""
    url: str = Field(..., description="URL to process")
    max_content_length: Optional[int] = Field(None, description="Maximum content length to extract")
    
class URLProcessingResponse(BaseModel):
    """Response model for URL processing"""
    url: str = Field(..., description="Processed URL")
    title: Optional[str] = Field(None, description="Page title")
    content: str = Field(..., description="Extracted content")
    content_length: int = Field(..., description="Content length in characters")
    processed_at: datetime = Field(default_factory=datetime.now)