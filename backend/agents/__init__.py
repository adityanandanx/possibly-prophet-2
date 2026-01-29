"""
Strands Agents Integration for Educational Content Generator

New Pipeline Flow:
1. Text Input -> Pedagogical Agent -> FDA Agent -> Manim Agent -> Video
2. File/URL Input -> FDA Agent -> Manim Agent -> Video
"""

from .base_agent import BaseEducationalAgent
from .content_pipeline import ContentPipeline, InputType
from .pedagogy_workflow import PedagogyWorkflow  # Legacy compatibility
from .agent_factory import AgentFactory
from .manim_generation_agent import ManimGenerationAgent
from .pedagogical_agent import PedagogicalAgent
from .fda_agent import FDAAgent
from .exceptions import (
    AgentError,
    AgentInitializationError,
    AgentExecutionError,
    AgentTimeoutError,
    AgentValidationError,
    AgentCommunicationError,
    WorkflowError,
    WorkflowExecutionError,
    WorkflowTimeoutError,
    WorkflowValidationError,
)
from .retry_handler import CircuitBreaker, RetryHandler

__all__ = [
    "BaseEducationalAgent",
    # New pipeline
    "ContentPipeline",
    "InputType",
    # Legacy compatibility
    "PedagogyWorkflow",
    "AgentFactory",
    # Pipeline agents
    "PedagogicalAgent",
    "FDAAgent",
    "ManimGenerationAgent",
    # Exceptions
    "AgentError",
    "AgentInitializationError",
    "AgentExecutionError",
    "AgentTimeoutError",
    "AgentValidationError",
    "AgentCommunicationError",
    "WorkflowError",
    "WorkflowExecutionError",
    "WorkflowTimeoutError",
    "WorkflowValidationError",
    # Retry and Circuit Breaker
    "CircuitBreaker",
    "RetryHandler",
]
