"""
Strands Agents Configuration for Educational Content Generator
"""

from strands import Agent
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv()


# Determine which AI provider to use based on available credentials
def get_available_provider():
    """Determine which AI provider to use based on available environment variables"""
    # Default to bedrock (will use fallbacks if no credentials)
    print(os.environ.get("AWS_ACCESS_KEY_ID"), "-------------------------------------")
    print(os.environ.get("AWS_BEARER_TOKEN_BEDROCK"), "-------------------------------")
    return {
        "model_provider": "bedrock",
        "model_name": "amazon.nova-pro-v1:0",
    }

# Agent Configuration with dynamic provider selection
provider_config = get_available_provider()
AGENT_CONFIG = {
    **provider_config,
    "temperature": 0.7,
    "max_tokens": 4000,
}

# Workflow Configuration
WORKFLOW_CONFIG = {
    "max_retries": 3,
    "timeout": 300,  # 5 minutes
    "parallel_execution": True,
    "failure_threshold": 5,  # Circuit breaker threshold
    "recovery_timeout": 60,  # Circuit breaker recovery time in seconds
}

# Agent Types Configuration
PEDAGOGY_AGENTS = {
    "content_structuring": {
        "name": "Enhanced Content Structuring Agent",
        "description": "Analyzes and organizes educational materials into logical sections with clear hierarchies, improved content flow, and structured learning progressions",
        "system_prompt": """You are an expert educational content structuring agent with advanced capabilities in content analysis and organization. Your role is to transform raw educational content into well-structured, hierarchical learning materials that enhance comprehension and retention.

CORE RESPONSIBILITIES:
1. Analyze content structure and identify main topics, key concepts, and learning themes
2. Create logical section hierarchies that support progressive learning
3. Organize content flow to ensure coherent knowledge building
4. Extract and highlight key concepts for each section
5. Determine appropriate learning outcomes and prerequisites
6. Estimate realistic time requirements for each section

ANALYSIS APPROACH:
- Identify content type (academic, tutorial, technical, conceptual, etc.)
- Extract main topics and subtopics using advanced NLP techniques
- Assess content difficulty level and complexity
- Evaluate structural quality and coherence
- Determine optimal section boundaries and hierarchies

STRUCTURING PRINCIPLES:
- Follow pedagogical best practices for content organization
- Ensure logical progression from basic to advanced concepts
- Create clear section titles that reflect learning objectives
- Maintain appropriate section length for cognitive load management
- Include transition elements to improve content flow
- Support different learning styles through varied content organization

OUTPUT REQUIREMENTS:
Provide a comprehensive content structure including:
- Clear hierarchical section organization
- Key concepts and learning outcomes for each section
- Estimated duration and difficulty assessment
- Content flow analysis and recommendations
- Prerequisites and dependencies between sections

Focus on creating educational content that is accessible, well-organized, and pedagogically sound.""",
        "max_retries": 3,
        "timeout_seconds": 180,  # Increased timeout for complex analysis
        "failure_threshold": 5,
        "recovery_timeout": 60
    },
    "learning_objectives": {
        "name": "Learning Objectives Agent", 
        "description": "Defines educational goals and learning outcomes",
        "system_prompt": """You are a learning objectives agent specialized in creating educational goals. 
        Your role is to analyze content and generate clear, measurable learning objectives aligned with pedagogical frameworks.""",
        "max_retries": 3,
        "timeout_seconds": 120,
        "failure_threshold": 5,
        "recovery_timeout": 60
    },
    "assessment": {
        "name": "Assessment Agent",
        "description": "Creates questions and evaluation criteria",
        "system_prompt": """You are an assessment agent specialized in creating educational evaluations. 
        Your role is to generate quiz questions, rubrics, and assessment criteria aligned with learning objectives.""",
        "max_retries": 3,
        "timeout_seconds": 120,
        "failure_threshold": 5,
        "recovery_timeout": 60
    },
    "visualization": {
        "name": "Visualization Agent",
        "description": "Identifies concepts suitable for animation and visual representation",
        "system_prompt": """You are a visualization agent specialized in identifying concepts for animation. 
        Your role is to analyze educational content and determine which concepts would benefit from visual representation.""",
        "max_retries": 3,
        "timeout_seconds": 120,
        "failure_threshold": 5,
        "recovery_timeout": 60
    },
    "narrative": {
        "name": "Narrative Agent",
        "description": "Ensures content flow and coherent storytelling",
        "system_prompt": """You are a narrative agent specialized in educational storytelling. 
        Your role is to ensure content flows coherently and maintains engaging educational narratives.""",
        "max_retries": 3,
        "timeout_seconds": 120,
        "failure_threshold": 5,
        "recovery_timeout": 60
    }
}

def get_agent_config(agent_type: str) -> Dict[str, Any]:
    """Get configuration for a specific agent type"""
    if agent_type not in PEDAGOGY_AGENTS:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    config = AGENT_CONFIG.copy()
    config.update(PEDAGOGY_AGENTS[agent_type])
    return config

def get_workflow_config() -> Dict[str, Any]:
    """Get workflow configuration"""
    return WORKFLOW_CONFIG.copy()