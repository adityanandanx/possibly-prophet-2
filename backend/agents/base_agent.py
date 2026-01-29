"""
Base Agent class for Educational Content Generator
"""

from strands import Agent
from typing import Dict, Any, Optional
from config.agents_config import get_agent_config
from .exceptions import (
    AgentInitializationError,
    AgentExecutionError,
    AgentTimeoutError,
    AgentValidationError,
)
from .retry_handler import RetryHandler, CircuitBreaker, create_retry_callback
import logging
import signal
from contextlib import contextmanager
from strands.models import BedrockModel


logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """Exception raised when operation times out"""

    pass


@contextmanager
def timeout(seconds: int):
    """
    Context manager for timing out operations

    Args:
        seconds: Timeout in seconds (must be integer)

    Raises:
        TimeoutException: If operation exceeds timeout
    """

    def timeout_handler(signum, frame):
        raise TimeoutException(f"Operation timed out after {seconds} seconds")

    # Convert to integer and set the signal handler and alarm
    timeout_int = int(seconds)
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_int)

    try:
        yield
    finally:
        # Restore the old handler and cancel the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class BaseEducationalAgent:
    """Base class for all educational content generation agents with enhanced error handling"""

    def __init__(self, agent_type: str, **kwargs):
        """
        Initialize base educational agent

        Args:
            agent_type: Type of agent (content_structuring, learning_objectives, etc.)
            **kwargs: Additional configuration parameters

        Raises:
            AgentInitializationError: If agent initialization fails
        """
        try:
            self.model = BedrockModel(
                model_id="us.amazon.nova-premier-v1:0",
                temperature=0.3,
                top_p=0.8,
            )
            self.agent_type = agent_type
            config = get_agent_config(agent_type)
            print(config)

            # Merge config with any provided kwargs
            config.update(kwargs)

            # Create the Strands Agent
            try:
                self.agent = Agent(
                    model=self.model,
                    system_prompt=config["system_prompt"],
                    callback_handler=None,  # Suppress intermediate output
                )
            except Exception as e:
                raise AgentInitializationError(
                    f"Failed to create Strands Agent for {agent_type}",
                    agent_type=agent_type,
                    original_error=e,
                )

            self.name = config["name"]
            self.description = config["description"]

            # Initialize circuit breaker for this agent
            self.circuit_breaker = CircuitBreaker(
                failure_threshold=config.get("failure_threshold", 5),
                recovery_timeout=config.get("recovery_timeout", 60),
                expected_exception=AgentExecutionError,
            )

            # Configuration for retries and timeouts
            self.max_retries = config.get("max_retries", 3)
            self.timeout_seconds = config.get("timeout_seconds", 120)

            logger.info(f"Initialized {self.agent_type} agent: {self.name}")

        except AgentInitializationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing {agent_type} agent: {str(e)}")
            raise AgentInitializationError(
                f"Unexpected error during agent initialization",
                agent_type=agent_type,
                original_error=e,
            )

    def process_content(
        self, content: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process educational content based on agent specialization with retry and error handling

        Args:
            content: Raw educational content to process
            context: Additional context for processing

        Returns:
            Processed content with agent-specific enhancements

        Raises:
            AgentExecutionError: If agent execution fails after retries
            AgentTimeoutError: If agent execution times out
            AgentValidationError: If response validation fails
        """
        try:
            # Use circuit breaker to protect against repeated failures
            return self.circuit_breaker.call(
                self._process_content_with_retry, content, context
            )
        except (AgentExecutionError, AgentValidationError, AgentTimeoutError):
            # Re-raise agent-specific errors as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {self.agent_type} agent: {str(e)}")
            raise AgentExecutionError(
                f"Unexpected error processing content",
                agent_type=self.agent_type,
                context=context,
                original_error=e,
            )

    @RetryHandler.retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        max_delay=30.0,
        exceptions=(AgentExecutionError, TimeoutException),
        on_retry=None,  # Will be set dynamically
    )
    def _process_content_with_retry(
        self, content: str, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Internal method to process content with retry logic

        Args:
            content: Raw educational content to process
            context: Additional context for processing

        Returns:
            Processed content with agent-specific enhancements

        Raises:
            AgentExecutionError: If agent execution fails
            AgentTimeoutError: If agent execution times out
        """
        try:
            # Validate input
            self._validate_input(content, context)

            # Prepare the prompt with content and context
            prompt = self._prepare_prompt(content, context or {})

            # Execute the agent with timeout
            try:
                with timeout(self.timeout_seconds):
                    agent_result = self.agent(prompt)
            except TimeoutException as e:
                logger.error(
                    f"{self.agent_type} agent timed out after {self.timeout_seconds}s"
                )
                raise AgentTimeoutError(
                    f"Agent execution timed out after {self.timeout_seconds} seconds",
                    agent_type=self.agent_type,
                    context=context,
                    original_error=e,
                )

            # Convert AgentResult to string for processing
            # The Strands SDK returns an AgentResult object, but _process_response expects a string
            response = str(agent_result)

            # Process and validate response
            result = self._process_response(response)

            # Validate output
            self._validate_output(result)

            logger.info(f"Successfully processed content with {self.agent_type} agent")
            return result

        except (AgentTimeoutError, AgentValidationError):
            raise
        except Exception as e:
            logger.error(
                f"Error processing content with {self.agent_type} agent: {str(e)}"
            )
            raise AgentExecutionError(
                f"Failed to process content",
                agent_type=self.agent_type,
                context=context,
                original_error=e,
            )

    def _validate_input(self, content: str, context: Optional[Dict[str, Any]]):
        """
        Validate input before processing

        Args:
            content: Content to validate
            context: Context to validate

        Raises:
            AgentValidationError: If validation fails
        """
        if not content or not content.strip():
            raise AgentValidationError(
                "Content cannot be empty",
                agent_type=self.agent_type,
                context={"content_length": len(content) if content else 0},
            )

        if len(content) > 100000:  # 100KB limit
            raise AgentValidationError(
                f"Content too large: {len(content)} characters (max 100000)",
                agent_type=self.agent_type,
                context={"content_length": len(content)},
            )

    def _validate_output(self, result: Dict[str, Any]):
        """
        Validate agent output

        Args:
            result: Result to validate

        Raises:
            AgentValidationError: If validation fails
        """
        if not result:
            raise AgentValidationError(
                "Agent returned empty result", agent_type=self.agent_type
            )

        if "processed_content" not in result:
            raise AgentValidationError(
                "Agent result missing 'processed_content' field",
                agent_type=self.agent_type,
                context={"result_keys": list(result.keys())},
            )

    def _prepare_prompt(self, content: str, context: Dict[str, Any]) -> str:
        """Prepare prompt for agent execution"""
        prompt_parts = [
            f"Educational Content to Process:\n{content}",
        ]

        if context:
            prompt_parts.append(f"Additional Context:\n{context}")

        return "\n\n".join(prompt_parts)

    def _process_response(self, response: str) -> Dict[str, Any]:
        """Process agent response into structured format"""
        return {
            "agent_type": self.agent_type,
            "processed_content": response,
            "metadata": {
                "agent_name": self.name,
                "processing_timestamp": None,  # Will be set by workflow
            },
        }
