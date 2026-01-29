"""
Custom exceptions for agent system error handling
"""

from typing import Optional, Dict, Any


class AgentError(Exception):
    """Base exception for all agent-related errors"""
    
    def __init__(
        self,
        message: str,
        agent_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize agent error
        
        Args:
            message: Error message
            agent_type: Type of agent that failed
            context: Additional context about the error
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.agent_type = agent_type
        self.context = context or {}
        self.original_error = original_error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "agent_type": self.agent_type,
            "context": self.context,
            "original_error": str(self.original_error) if self.original_error else None
        }


class AgentInitializationError(AgentError):
    """Raised when agent fails to initialize"""
    pass


class AgentExecutionError(AgentError):
    """Raised when agent execution fails"""
    pass


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out"""
    pass


class AgentValidationError(AgentError):
    """Raised when agent output validation fails"""
    pass


class AgentCommunicationError(AgentError):
    """Raised when agent communication fails"""
    pass


class WorkflowError(Exception):
    """Base exception for workflow-related errors"""
    
    def __init__(
        self,
        message: str,
        failed_agents: Optional[list] = None,
        partial_results: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize workflow error
        
        Args:
            message: Error message
            failed_agents: List of agents that failed
            partial_results: Partial results from successful agents
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.failed_agents = failed_agents or []
        self.partial_results = partial_results or {}
        self.original_error = original_error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "failed_agents": self.failed_agents,
            "partial_results_available": bool(self.partial_results),
            "original_error": str(self.original_error) if self.original_error else None
        }


class WorkflowExecutionError(WorkflowError):
    """Raised when workflow execution fails"""
    pass


class WorkflowTimeoutError(WorkflowError):
    """Raised when workflow execution times out"""
    pass


class WorkflowValidationError(WorkflowError):
    """Raised when workflow output validation fails"""
    pass
