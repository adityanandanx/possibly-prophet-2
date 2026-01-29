"""
Retry handler with exponential backoff and circuit breaker pattern
"""

import time
import logging
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
from datetime import datetime, timedelta
from .exceptions import AgentError, AgentTimeoutError, AgentExecutionError

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for agent failures
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail immediately
    - HALF_OPEN: Testing if service recovered, limited requests pass through
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to track for failures
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            AgentExecutionError: If circuit is open
        """
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise AgentExecutionError(
                    "Circuit breaker is OPEN - too many recent failures",
                    context={
                        "failure_count": self.failure_count,
                        "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
                        "state": self.state
                    }
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful execution"""
        if self.state == "HALF_OPEN":
            logger.info("Circuit breaker recovered - entering CLOSED state")
        
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
    
    def reset(self):
        """Manually reset circuit breaker"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        logger.info("Circuit breaker manually reset")


class RetryHandler:
    """Handler for retry logic with exponential backoff"""
    
    @staticmethod
    def retry_with_backoff(
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable] = None
    ):
        """
        Decorator for retrying functions with exponential backoff
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff calculation
            exceptions: Tuple of exceptions to catch and retry
            on_retry: Optional callback function called on each retry
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt >= max_retries:
                            logger.error(
                                f"Function {func.__name__} failed after {max_retries} retries: {str(e)}"
                            )
                            raise
                        
                        # Calculate delay with exponential backoff
                        delay = min(
                            initial_delay * (exponential_base ** attempt),
                            max_delay
                        )
                        
                        logger.warning(
                            f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                            f"retrying in {delay:.2f}s: {str(e)}"
                        )
                        
                        # Call retry callback if provided
                        if on_retry:
                            try:
                                on_retry(attempt, delay, e)
                            except Exception as callback_error:
                                logger.error(f"Retry callback failed: {str(callback_error)}")
                        
                        time.sleep(delay)
                
                # This should never be reached, but just in case
                raise last_exception or Exception("Retry failed")
            
            return wrapper
        return decorator
    
    @staticmethod
    def retry_async_with_backoff(
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable] = None
    ):
        """
        Decorator for retrying async functions with exponential backoff
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff calculation
            exceptions: Tuple of exceptions to catch and retry
            on_retry: Optional callback function called on each retry
            
        Returns:
            Decorated async function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                import asyncio
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt >= max_retries:
                            logger.error(
                                f"Async function {func.__name__} failed after {max_retries} retries: {str(e)}"
                            )
                            raise
                        
                        # Calculate delay with exponential backoff
                        delay = min(
                            initial_delay * (exponential_base ** attempt),
                            max_delay
                        )
                        
                        logger.warning(
                            f"Async function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                            f"retrying in {delay:.2f}s: {str(e)}"
                        )
                        
                        # Call retry callback if provided
                        if on_retry:
                            try:
                                if asyncio.iscoroutinefunction(on_retry):
                                    await on_retry(attempt, delay, e)
                                else:
                                    on_retry(attempt, delay, e)
                            except Exception as callback_error:
                                logger.error(f"Retry callback failed: {str(callback_error)}")
                        
                        await asyncio.sleep(delay)
                
                # This should never be reached, but just in case
                raise last_exception or Exception("Retry failed")
            
            return wrapper
        return decorator


def create_retry_callback(agent_type: str) -> Callable:
    """
    Create a retry callback function for logging
    
    Args:
        agent_type: Type of agent being retried
        
    Returns:
        Callback function
    """
    def callback(attempt: int, delay: float, error: Exception):
        logger.info(
            f"Retrying {agent_type} agent - attempt {attempt + 1}, "
            f"waiting {delay:.2f}s after error: {str(error)}"
        )
    
    return callback
