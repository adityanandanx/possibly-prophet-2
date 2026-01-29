"""
Pytest configuration and fixtures for Educational Content Generator tests
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from app.main import app
from app.core.config import settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
async def async_client():
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as async_test_client:
        yield async_test_client

@pytest.fixture
def test_settings():
    """Provide test-specific settings."""
    return settings

@pytest.fixture
def sample_text_content():
    """Sample text content for testing."""
    return """
    Introduction to Photosynthesis
    
    Photosynthesis is the process by which plants convert light energy into chemical energy.
    This process occurs in the chloroplasts of plant cells and involves two main stages:
    
    1. Light-dependent reactions (occur in thylakoids)
    2. Light-independent reactions (Calvin cycle, occurs in stroma)
    
    The overall equation for photosynthesis is:
    6CO2 + 6H2O + light energy → C6H12O6 + 6O2
    """

@pytest.fixture
def sample_educational_script():
    """Sample educational script for testing."""
    return {
        "title": "Introduction to Photosynthesis",
        "learning_objectives": [
            "Understand the basic process of photosynthesis",
            "Identify the two main stages of photosynthesis",
            "Recognize the chemical equation for photosynthesis"
        ],
        "sections": [
            {
                "title": "What is Photosynthesis?",
                "content": "Photosynthesis is the process by which plants convert light energy into chemical energy.",
                "animations": ["chloroplast_structure"],
                "assessments": ["What is photosynthesis?"]
            }
        ],
        "metadata": {
            "difficulty_level": "beginner",
            "estimated_duration": "15 minutes",
            "prerequisites": []
        }
    }