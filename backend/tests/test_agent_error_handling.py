"""
Tests for agent error handling and retry mechanisms
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.exceptions import (
    AgentError,
    AgentInitializationError,
    AgentExecutionError,
    AgentTimeoutError,
    AgentValidationError,
    WorkflowError,
    WorkflowExecutionError
)
from agents.retry_handler import CircuitBreaker, RetryHandler
from agents.base_agent import BaseEducationalAgent, TimeoutException
from agents.pedagogy_workflow import PedagogyWorkflow


class TestAgentExceptions:
    """Test custom agent exceptions"""
    
    def test_agent_error_creation(self):
        """Test AgentError can be created with all parameters"""
        error = AgentError(
            message="Test error",
            agent_type="test_agent",
            context={"key": "value"},
            original_error=ValueError("Original")
        )
        
        assert error.message == "Test error"
        assert error.agent_type == "test_agent"
        assert error.context == {"key": "value"}
        assert isinstance(error.original_error, ValueError)
    
    def test_agent_error_to_dict(self):
        """Test AgentError serialization to dictionary"""
        error = AgentError(
            message="Test error",
            agent_type="test_agent",
            context={"key": "value"}
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "AgentError"
        assert error_dict["message"] == "Test error"
        assert error_dict["agent_type"] == "test_agent"
        assert error_dict["context"] == {"key": "value"}
    
    def test_workflow_error_creation(self):
        """Test WorkflowError can be created with all parameters"""
        error = WorkflowError(
            message="Workflow failed",
            failed_agents=["agent1", "agent2"],
            partial_results={"agent3": {"result": "data"}},
            original_error=Exception("Original")
        )
        
        assert error.message == "Workflow failed"
        assert error.failed_agents == ["agent1", "agent2"]
        assert error.partial_results == {"agent3": {"result": "data"}}
        assert isinstance(error.original_error, Exception)
    
    def test_workflow_error_to_dict(self):
        """Test WorkflowError serialization to dictionary"""
        error = WorkflowError(
            message="Workflow failed",
            failed_agents=["agent1"],
            partial_results={"agent2": {}}
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "WorkflowError"
        assert error_dict["message"] == "Workflow failed"
        assert error_dict["failed_agents"] == ["agent1"]
        assert error_dict["partial_results_available"] is True


class TestCircuitBreaker:
    """Test circuit breaker pattern implementation"""
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker allows calls in CLOSED state"""
        cb = CircuitBreaker(failure_threshold=3)
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        
        assert result == "success"
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures"""
        cb = CircuitBreaker(failure_threshold=3, expected_exception=ValueError)
        
        def failing_func():
            raise ValueError("Test failure")
        
        # Trigger failures up to threshold
        for i in range(3):
            with pytest.raises(ValueError):
                cb.call(failing_func)
        
        assert cb.state == "OPEN"
        assert cb.failure_count == 3
        
        # Next call should fail immediately with AgentExecutionError
        with pytest.raises(AgentExecutionError) as exc_info:
            cb.call(failing_func)
        
        assert "Circuit breaker is OPEN" in str(exc_info.value)
    
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through HALF_OPEN state"""
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0,  # Immediate recovery for testing
            expected_exception=ValueError
        )
        
        def failing_func():
            raise ValueError("Test failure")
        
        def success_func():
            return "success"
        
        # Open the circuit
        for i in range(2):
            with pytest.raises(ValueError):
                cb.call(failing_func)
        
        assert cb.state == "OPEN"
        
        # Should enter HALF_OPEN and succeed
        result = cb.call(success_func)
        
        assert result == "success"
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
    
    def test_circuit_breaker_reset(self):
        """Test manual circuit breaker reset"""
        cb = CircuitBreaker(failure_threshold=2, expected_exception=ValueError)
        
        def failing_func():
            raise ValueError("Test failure")
        
        # Open the circuit
        for i in range(2):
            with pytest.raises(ValueError):
                cb.call(failing_func)
        
        assert cb.state == "OPEN"
        
        # Reset manually
        cb.reset()
        
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
        assert cb.last_failure_time is None


class TestRetryHandler:
    """Test retry handler with exponential backoff"""
    
    def test_retry_success_on_first_attempt(self):
        """Test function succeeds on first attempt"""
        call_count = 0
        
        @RetryHandler.retry_with_backoff(max_retries=3)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = success_func()
        
        assert result == "success"
        assert call_count == 1
    
    def test_retry_success_after_failures(self):
        """Test function succeeds after some failures"""
        call_count = 0
        
        @RetryHandler.retry_with_backoff(
            max_retries=3,
            initial_delay=0.01,  # Fast for testing
            exceptions=(ValueError,)
        )
        def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"
        
        result = eventually_succeeds()
        
        assert result == "success"
        assert call_count == 3
    
    def test_retry_exhausts_attempts(self):
        """Test function fails after all retry attempts"""
        call_count = 0
        
        @RetryHandler.retry_with_backoff(
            max_retries=2,
            initial_delay=0.01,
            exceptions=(ValueError,)
        )
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError) as exc_info:
            always_fails()
        
        assert "Always fails" in str(exc_info.value)
        assert call_count == 3  # Initial + 2 retries
    
    def test_retry_with_callback(self):
        """Test retry callback is called on each retry"""
        callback_calls = []
        
        def retry_callback(attempt, delay, error):
            callback_calls.append({
                "attempt": attempt,
                "delay": delay,
                "error": str(error)
            })
        
        call_count = 0
        
        @RetryHandler.retry_with_backoff(
            max_retries=2,
            initial_delay=0.01,
            exceptions=(ValueError,),
            on_retry=retry_callback
        )
        def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count}")
            return "success"
        
        result = eventually_succeeds()
        
        assert result == "success"
        assert len(callback_calls) == 2
        assert callback_calls[0]["attempt"] == 0
        assert callback_calls[1]["attempt"] == 1
    
    def test_retry_exponential_backoff(self):
        """Test exponential backoff delay calculation"""
        delays = []
        
        def capture_delay(attempt, delay, error):
            delays.append(delay)
        
        call_count = 0
        
        @RetryHandler.retry_with_backoff(
            max_retries=3,
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=10.0,
            exceptions=(ValueError,),
            on_retry=capture_delay
        )
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Fail")
        
        with pytest.raises(ValueError):
            always_fails()
        
        # Check exponential backoff: 1, 2, 4
        assert len(delays) == 3
        assert delays[0] == 1.0
        assert delays[1] == 2.0
        assert delays[2] == 4.0


class TestBaseAgentErrorHandling:
    """Test base agent error handling"""
    
    @patch('agents.base_agent.Agent')
    def test_agent_initialization_error(self, mock_agent_class):
        """Test agent initialization error handling"""
        mock_agent_class.side_effect = Exception("Strands Agent creation failed")
        
        with pytest.raises(AgentInitializationError) as exc_info:
            agent = BaseEducationalAgent("content_structuring")
        
        assert "Failed to create Strands Agent" in str(exc_info.value)
        assert exc_info.value.agent_type == "content_structuring"
    
    @patch('agents.base_agent.Agent')
    def test_agent_validates_empty_content(self, mock_agent_class):
        """Test agent rejects empty content"""
        mock_agent_class.return_value = Mock()
        agent = BaseEducationalAgent("content_structuring")
        
        with pytest.raises(AgentValidationError) as exc_info:
            agent.process_content("", {})
        
        assert "Content cannot be empty" in str(exc_info.value)
    
    @patch('agents.base_agent.Agent')
    def test_agent_validates_content_size(self, mock_agent_class):
        """Test agent rejects oversized content"""
        mock_agent_class.return_value = Mock()
        agent = BaseEducationalAgent("content_structuring")
        
        large_content = "x" * 100001  # Exceeds 100KB limit
        
        with pytest.raises(AgentValidationError) as exc_info:
            agent.process_content(large_content, {})
        
        assert "Content too large" in str(exc_info.value)
    
    @patch('agents.base_agent.Agent')
    def test_agent_validates_output(self, mock_agent_class):
        """Test agent validates output structure"""
        mock_agent_instance = Mock()
        mock_agent_instance.return_value = "Invalid response"
        mock_agent_class.return_value = mock_agent_instance
        
        agent = BaseEducationalAgent("content_structuring")
        
        # Mock the _process_response to return invalid structure (non-empty dict without required field)
        with patch.object(agent, '_process_response', return_value={"some_field": "value"}):
            with pytest.raises(AgentValidationError) as exc_info:
                agent.process_content("Valid content", {})
            
            assert "missing 'processed_content' field" in str(exc_info.value)
    
    @patch('agents.base_agent.Agent')
    def test_agent_circuit_breaker_integration(self, mock_agent_class):
        """Test agent uses circuit breaker"""
        mock_agent_instance = Mock()
        mock_agent_instance.side_effect = Exception("Agent failed")
        mock_agent_class.return_value = mock_agent_instance
        
        agent = BaseEducationalAgent("content_structuring")
        
        # Trigger failures to open circuit
        for i in range(5):
            with pytest.raises((AgentExecutionError, AgentValidationError)):
                agent.process_content("Test content", {})
        
        # Circuit should be open now
        assert agent.circuit_breaker.state == "OPEN"


class TestWorkflowErrorHandling:
    """Test workflow error handling"""
    
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_workflow_initialization_error(self, mock_create_agents):
        """Test workflow handles agent initialization errors"""
        mock_create_agents.side_effect = Exception("Failed to create agents")
        
        with pytest.raises(WorkflowError) as exc_info:
            workflow = PedagogyWorkflow()
        
        assert "Failed to initialize pedagogy agents" in str(exc_info.value)
    
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_workflow_handles_agent_failures(self, mock_create_agents):
        """Test workflow continues with optional agent failures"""
        # Create mock agents
        mock_agents = {}
        for agent_type in ["content_structuring", "learning_objectives", "assessment", "visualization", "narrative"]:
            mock_agent = Mock()
            if agent_type == "visualization":
                # Make visualization agent fail
                mock_agent.process_content.side_effect = AgentExecutionError(
                    "Visualization failed",
                    agent_type=agent_type
                )
            else:
                # Other agents succeed
                mock_agent.process_content.return_value = {
                    "agent_type": agent_type,
                    "processed_content": f"Processed by {agent_type}",
                    "metadata": {}
                }
            mock_agents[agent_type] = mock_agent
        
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        result = workflow.execute("Test content", {})
        
        # Workflow should complete despite visualization failure
        assert result is not None
        assert "workflow_metadata" in result
        assert "visualization" in result["workflow_metadata"]["failed_agents"]
        assert "content_structuring" in result["workflow_metadata"]["successful_agents"]
    
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_workflow_fails_on_critical_agent_failure(self, mock_create_agents):
        """Test workflow fails when critical agent fails"""
        # Create mock agents
        mock_agents = {}
        for agent_type in ["content_structuring", "learning_objectives", "assessment", "visualization", "narrative"]:
            mock_agent = Mock()
            if agent_type == "content_structuring":
                # Make critical agent fail without fallback
                mock_agent.process_content.side_effect = AgentExecutionError(
                    "Critical failure",
                    agent_type=agent_type
                )
            else:
                mock_agent.process_content.return_value = {
                    "agent_type": agent_type,
                    "processed_content": f"Processed by {agent_type}",
                    "metadata": {}
                }
            mock_agents[agent_type] = mock_agent
        
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        
        # Patch fallback to return None (no fallback available)
        with patch.object(workflow, '_create_fallback_result', return_value=None):
            with pytest.raises(WorkflowExecutionError) as exc_info:
                workflow.execute("Test content", {})
            
            # Check that the error message indicates critical agent failure
            assert "content_structuring" in exc_info.value.failed_agents or "Failed to execute agent sequence" in str(exc_info.value)
    
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_workflow_uses_fallback_for_critical_agent(self, mock_create_agents):
        """Test workflow uses fallback when critical agent fails"""
        # Create mock agents
        mock_agents = {}
        for agent_type in ["content_structuring", "learning_objectives", "assessment", "visualization", "narrative"]:
            mock_agent = Mock()
            if agent_type == "content_structuring":
                # Make critical agent fail
                mock_agent.process_content.side_effect = AgentExecutionError(
                    "Critical failure",
                    agent_type=agent_type
                )
            else:
                mock_agent.process_content.return_value = {
                    "agent_type": agent_type,
                    "processed_content": f"Processed by {agent_type}",
                    "metadata": {}
                }
            mock_agents[agent_type] = mock_agent
        
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        result = workflow.execute("Test content", {})
        
        # Workflow should complete using fallback
        assert result is not None
        assert "workflow_metadata" in result
        # content_structuring should be in failed agents but workflow succeeded
        assert "content_structuring" in result["workflow_metadata"]["failed_agents"]


@pytest.mark.unit
class TestErrorHandlingIntegration:
    """Integration tests for error handling system"""
    
    def test_error_to_dict_serialization(self):
        """Test all error types can be serialized to dict"""
        errors = [
            AgentError("Test", agent_type="test"),
            AgentInitializationError("Test", agent_type="test"),
            AgentExecutionError("Test", agent_type="test"),
            AgentTimeoutError("Test", agent_type="test"),
            AgentValidationError("Test", agent_type="test"),
            WorkflowError("Test", failed_agents=["test"]),
            WorkflowExecutionError("Test", failed_agents=["test"])
        ]
        
        for error in errors:
            error_dict = error.to_dict()
            assert isinstance(error_dict, dict)
            assert "error_type" in error_dict
            assert "message" in error_dict
    
    def test_circuit_breaker_with_retry_handler(self):
        """Test circuit breaker works with retry handler"""
        cb = CircuitBreaker(failure_threshold=2, expected_exception=ValueError)
        call_count = 0
        
        @RetryHandler.retry_with_backoff(
            max_retries=2,  # Increased to allow success
            initial_delay=0.01,
            exceptions=(ValueError,)
        )
        def func_with_retry():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Fail")
            return "success"
        
        # First call should retry and succeed
        result = cb.call(func_with_retry)
        assert result == "success"
        assert cb.state == "CLOSED"
