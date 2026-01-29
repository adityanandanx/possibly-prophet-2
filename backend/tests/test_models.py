"""
Tests for content models
"""

import pytest
from datetime import datetime
from app.models.content import (
    ContentRequest, ContentInput, EducationalScript, ContentResponse,
    LearningObjective, ContentSection, Assessment, AssessmentQuestion,
    DifficultyLevel, ContentType, GenerationStatus, BloomLevel, AssessmentType
)

@pytest.mark.unit
def test_content_input_model():
    """Test ContentInput model validation."""
    content_input = ContentInput(
        content_type=ContentType.TEXT,
        content="Sample educational content",
        metadata={"source": "textbook"}
    )
    assert content_input.content_type == ContentType.TEXT
    assert content_input.content == "Sample educational content"
    assert content_input.metadata["source"] == "textbook"

@pytest.mark.unit
def test_content_request_model():
    """Test ContentRequest model validation."""
    request = ContentRequest(
        inputs=[
            ContentInput(
                content_type=ContentType.TEXT,
                content="Photosynthesis content",
                metadata={}
            )
        ],
        topic="Photosynthesis",
        difficulty_level=DifficultyLevel.INTERMEDIATE,
        target_audience="high school students",
        learning_goals=["Understand photosynthesis"]
    )
    assert len(request.inputs) == 1
    assert request.topic == "Photosynthesis"
    assert request.difficulty_level == DifficultyLevel.INTERMEDIATE

@pytest.mark.unit
def test_learning_objective_model():
    """Test LearningObjective model validation."""
    objective = LearningObjective(
        objective="Students will understand photosynthesis",
        bloom_level=BloomLevel.UNDERSTAND,
        measurable=True
    )
    assert objective.bloom_level == BloomLevel.UNDERSTAND
    assert objective.measurable is True

@pytest.mark.unit
def test_assessment_question_model():
    """Test AssessmentQuestion model validation."""
    question = AssessmentQuestion(
        question="What is photosynthesis?",
        question_type="short_answer",
        difficulty=DifficultyLevel.BEGINNER
    )
    assert question.question == "What is photosynthesis?"
    assert question.difficulty == DifficultyLevel.BEGINNER

@pytest.mark.unit
def test_educational_script_model():
    """Test EducationalScript model validation."""
    script = EducationalScript(
        title="Photosynthesis Lesson",
        description="Introduction to photosynthesis",
        learning_objectives=[
            LearningObjective(
                objective="Understand photosynthesis",
                bloom_level=BloomLevel.UNDERSTAND
            )
        ],
        sections=[
            ContentSection(
                title="Introduction",
                content="Photosynthesis is...",
                duration_minutes=10
            )
        ]
    )
    assert script.title == "Photosynthesis Lesson"
    assert len(script.learning_objectives) == 1
    assert len(script.sections) == 1

@pytest.mark.unit
def test_content_response_model():
    """Test ContentResponse model validation."""
    response = ContentResponse(
        generation_id="gen_123",
        status=GenerationStatus.COMPLETED,
        educational_script=EducationalScript(
            title="Test Script",
            sections=[]
        )
    )
    assert response.generation_id == "gen_123"
    assert response.status == GenerationStatus.COMPLETED
    assert response.educational_script.title == "Test Script"
    assert isinstance(response.created_at, datetime)