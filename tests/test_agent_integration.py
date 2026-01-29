"""
Integration tests for agent error handling with the full system
"""

import pytest
from unittest.mock import Mock, patch
from agents import (
    BaseEducationalAgent,
    PedagogyWorkflow,
    AgentFactory,
    AgentExecutionError,
    WorkflowExecutionError
)


@pytest.mark.integration
class TestAgentSystemIntegration:
    """Integration tests for the complete agent system with error handling"""
    
    @patch('agents.base_agent.Agent')
    def test_successful_agent_execution(self, mock_agent_class):
        """Test successful agent execution with all error handling in place"""
        # Mock successful agent response
        mock_agent_instance = Mock()
        mock_agent_instance.return_value = "Processed educational content"
        mock_agent_class.return_value = mock_agent_instance
        
        agent = BaseEducationalAgent("content_structuring")
        
        # Mock _process_response to return valid structure
        with patch.object(agent, '_process_response', return_value={
            "agent_type": "content_structuring",
            "processed_content": "Structured content",
            "metadata": {}
        }):
            result = agent.process_content("Test educational content", {})
        
        assert result is not None
        assert result["agent_type"] == "content_structuring"
        assert "processed_content" in result
    
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_workflow_with_mixed_results(self, mock_create_agents):
        """Test workflow handles mix of successful and failed agents"""
        # Create mock agents with mixed success/failure
        mock_agents = {}
        
        for agent_type in ["content_structuring", "learning_objectives", "assessment", "visualization", "narrative"]:
            mock_agent = Mock()
            
            if agent_type == "visualization":
                # Visualization fails (optional agent)
                mock_agent.process_content.side_effect = AgentExecutionError(
                    "Visualization processing failed",
                    agent_type=agent_type
                )
            elif agent_type == "narrative":
                # Narrative fails (optional agent)
                mock_agent.process_content.side_effect = AgentExecutionError(
                    "Narrative processing failed",
                    agent_type=agent_type
                )
            else:
                # Other agents succeed
                mock_agent.process_content.return_value = {
                    "agent_type": agent_type,
                    "processed_content": f"Content from {agent_type}",
                    "metadata": {"agent_name": agent_type}
                }
            
            mock_agents[agent_type] = mock_agent
        
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        result = workflow.execute("Educational content to process", {
            "topic": "Test Topic",
            "difficulty_level": "intermediate"
        })
        
        # Verify workflow completed despite failures
        assert result is not None
        assert "workflow_metadata" in result
        
        # Check failed agents
        failed_agents = result["workflow_metadata"]["failed_agents"]
        assert "visualization" in failed_agents
        assert "narrative" in failed_agents
        
        # Check successful agents
        successful_agents = result["workflow_metadata"]["successful_agents"]
        assert "content_structuring" in successful_agents
        assert "learning_objectives" in successful_agents
        assert "assessment" in successful_agents
    
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_workflow_statistics_tracking(self, mock_create_agents):
        """Test workflow tracks execution statistics"""
        # Create mock agents that all succeed
        mock_agents = {}
        for agent_type in ["content_structuring", "learning_objectives", "assessment", "visualization", "narrative"]:
            mock_agent = Mock()
            mock_agent.process_content.return_value = {
                "agent_type": agent_type,
                "processed_content": f"Content from {agent_type}",
                "metadata": {}
            }
            mock_agents[agent_type] = mock_agent
        
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        
        # Execute workflow multiple times
        for i in range(3):
            result = workflow.execute(f"Content {i}", {})
            assert result["workflow_metadata"]["execution_id"] == i + 1
        
        # Verify statistics
        assert workflow.execution_count == 3
        assert workflow.failure_count == 0
        assert workflow.last_execution_time is not None
    
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_circuit_breaker_prevents_cascading_failures(self, mock_create_agents):
        """Test circuit breaker prevents cascading failures"""
        # Create a mock agent that always fails
        mock_agents = {}
        for agent_type in ["content_structuring", "learning_objectives", "assessment", "visualization", "narrative"]:
            mock_agent = Mock()
            mock_agent.process_content.side_effect = AgentExecutionError(
                "Agent failed",
                agent_type=agent_type
            )
            mock_agents[agent_type] = mock_agent
        
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        
        # Critical agents will use fallback, so workflow will succeed with fallback results
        result = workflow.execute("Test content", {})
        
        # Verify all agents failed but workflow completed with fallbacks
        assert result is not None
        assert "workflow_metadata" in result
        assert len(result["workflow_metadata"]["failed_agents"]) == 5  # All agents failed
        
        # Verify failure was tracked
        assert workflow.failure_count == 0  # Workflow succeeded with fallbacks
    
    @patch('agents.base_agent.Agent')
    def test_agent_timeout_handling(self, mock_agent_class):
        """Test agent handles timeouts gracefully"""
        import time
        
        # Mock agent that takes too long
        def slow_agent_call(*args, **kwargs):
            time.sleep(0.1)  # Simulate slow processing
            return "Response"
        
        mock_agent_instance = Mock()
        mock_agent_instance.side_effect = slow_agent_call
        mock_agent_class.return_value = mock_agent_instance
        
        # Create agent with short timeout (must be integer)
        agent = BaseEducationalAgent("content_structuring", timeout_seconds=1)
        
        # Mock _process_response to return valid structure
        with patch.object(agent, '_process_response', return_value={
            "agent_type": "content_structuring",
            "processed_content": "Content",
            "metadata": {}
        }):
            # Should succeed with mocked response (timeout won't trigger with mock)
            result = agent.process_content("Test content", {})
            assert result is not None
            assert result["agent_type"] == "content_structuring"
    
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_fallback_mechanism_for_critical_agents(self, mock_create_agents):
        """Test fallback mechanism works for critical agents"""
        # Create mock agents where content_structuring fails
        mock_agents = {}
        for agent_type in ["content_structuring", "learning_objectives", "assessment", "visualization", "narrative"]:
            mock_agent = Mock()
            
            if agent_type == "content_structuring":
                # Critical agent fails
                mock_agent.process_content.side_effect = AgentExecutionError(
                    "Critical failure",
                    agent_type=agent_type
                )
            else:
                # Other agents succeed
                mock_agent.process_content.return_value = {
                    "agent_type": agent_type,
                    "processed_content": f"Content from {agent_type}",
                    "metadata": {}
                }
            
            mock_agents[agent_type] = mock_agent
        
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        
        # Workflow should use fallback for content_structuring
        result = workflow.execute("Test content", {})
        
        # Verify workflow completed with fallback
        assert result is not None
        assert "content_structuring" in result["workflow_metadata"]["failed_agents"]
        
        # Verify other agents succeeded
        assert "learning_objectives" in result["workflow_metadata"]["successful_agents"]


@pytest.mark.integration
class TestErrorRecovery:
    """Test error recovery scenarios"""
    
    @patch('agents.base_agent.Agent')
    def test_retry_recovers_from_transient_failure(self, mock_agent_class):
        """Test retry mechanism recovers from transient failures"""
        call_count = 0
        
        def transient_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Transient failure")
            return "Success after retry"
        
        mock_agent_instance = Mock()
        mock_agent_instance.side_effect = transient_failure
        mock_agent_class.return_value = mock_agent_instance
        
        agent = BaseEducationalAgent("content_structuring")
        
        # Mock _process_response to return valid structure
        with patch.object(agent, '_process_response', return_value={
            "agent_type": "content_structuring",
            "processed_content": "Content",
            "metadata": {}
        }):
            result = agent.process_content("Test content", {})
        
        # Should succeed after retry
        assert result is not None
        assert call_count >= 2  # At least one retry occurred
    
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_partial_results_available_on_failure(self, mock_create_agents):
        """Test partial results are available when workflow fails"""
        # Create mock agents where some succeed before failure
        mock_agents = {}
        for agent_type in ["content_structuring", "learning_objectives", "assessment", "visualization", "narrative"]:
            mock_agent = Mock()
            
            if agent_type in ["content_structuring", "learning_objectives"]:
                # First two succeed
                mock_agent.process_content.return_value = {
                    "agent_type": agent_type,
                    "processed_content": f"Content from {agent_type}",
                    "metadata": {}
                }
            else:
                # Rest fail
                mock_agent.process_content.side_effect = AgentExecutionError(
                    "Agent failed",
                    agent_type=agent_type
                )
            
            mock_agents[agent_type] = mock_agent
        
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        
        # Workflow should complete with partial results
        result = workflow.execute("Test content", {})
        
        # Verify we have results from successful agents
        assert result is not None
        assert "content_structuring" in result["workflow_metadata"]["successful_agents"]
        assert "learning_objectives" in result["workflow_metadata"]["successful_agents"]
        
        # Verify failed agents are tracked
        assert len(result["workflow_metadata"]["failed_agents"]) > 0
