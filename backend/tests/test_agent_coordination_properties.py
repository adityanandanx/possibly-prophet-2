"""
Property-based tests for agent coordination

**Validates: Requirements 1.2**

Property 2: Agent Coordination
The agent orchestration system must ensure that all required pedagogy agents 
complete their tasks successfully before proceeding to content generation.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis import Phase
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Set
from agents.pedagogy_workflow import PedagogyWorkflow
from agents.exceptions import (
    AgentExecutionError,
    WorkflowExecutionError,
    AgentValidationError
)


# Strategy for generating agent types
AGENT_TYPES = ["content_structuring", "learning_objectives", "assessment", "visualization", "narrative"]
CRITICAL_AGENTS = {"content_structuring", "learning_objectives"}
OPTIONAL_AGENTS = {"assessment", "visualization", "narrative"}


@st.composite
def agent_execution_scenario(draw):
    """
    Generate scenarios for agent execution with various success/failure patterns
    
    Returns a dict with:
    - failing_agents: Set of agent types that should fail
    - content: Input content string
    - has_fallback: Whether critical agents have fallback available
    """
    # Generate which agents will fail (can be empty set)
    num_failing = draw(st.integers(min_value=0, max_value=len(AGENT_TYPES)))
    failing_agents = set(draw(st.lists(
        st.sampled_from(AGENT_TYPES),
        min_size=num_failing,
        max_size=num_failing,
        unique=True
    )))
    
    # Generate input content
    content = draw(st.text(min_size=10, max_size=500))
    
    # Determine if critical agents have fallback
    has_fallback = draw(st.booleans())
    
    return {
        "failing_agents": failing_agents,
        "content": content,
        "has_fallback": has_fallback
    }


@st.composite
def agent_results_strategy(draw):
    """
    Generate valid agent results for testing compilation
    """
    # Generate which agents completed successfully
    num_successful = draw(st.integers(min_value=1, max_value=len(AGENT_TYPES)))
    successful_agents = draw(st.lists(
        st.sampled_from(AGENT_TYPES),
        min_size=num_successful,
        max_size=num_successful,
        unique=True
    ))
    
    results = {}
    for agent_type in successful_agents:
        results[agent_type] = {
            "agent_type": agent_type,
            "processed_content": draw(st.text(min_size=10, max_size=200)),
            "metadata": {
                "agent_name": f"{agent_type}_agent",
                "processing_timestamp": "2024-01-01T00:00:00"
            }
        }
    
    return results


class TestAgentCoordinationProperties:
    """Property-based tests for agent coordination"""
    
    @given(scenario=agent_execution_scenario())
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_property_critical_agents_must_complete(self, mock_create_agents, scenario):
        """
        Property: If any critical agent fails without fallback, workflow must fail
        
        Critical agents: content_structuring, learning_objectives
        These agents are essential for generating educational content.
        """
        failing_agents = scenario["failing_agents"]
        content = scenario["content"]
        has_fallback = scenario["has_fallback"]
        
        # Skip if content is empty or whitespace only
        assume(content.strip())
        
        # Check if any critical agent is failing
        critical_failing = failing_agents & CRITICAL_AGENTS
        
        # Create mock agents
        mock_agents = self._create_mock_agents(failing_agents)
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        
        if critical_failing and not has_fallback:
            # Property: Critical agent failure without fallback must cause workflow failure
            with patch.object(workflow, '_create_fallback_result', return_value=None):
                with pytest.raises(WorkflowExecutionError) as exc_info:
                    workflow.execute(content, {})
                
                # Verify that the error mentions critical agent failure
                error = exc_info.value
                assert len(error.failed_agents) > 0, "Failed agents list should not be empty"
                
                # At least one critical agent should be in failed agents
                assert any(agent in error.failed_agents for agent in critical_failing), \
                    f"Critical failing agents {critical_failing} should be in failed_agents {error.failed_agents}"
        else:
            # Property: With fallback or no critical failures, workflow should complete
            if critical_failing and has_fallback:
                # Mock fallback to return valid result
                with patch.object(workflow, '_create_fallback_result') as mock_fallback:
                    mock_fallback.return_value = {
                        "agent_type": "fallback",
                        "processed_content": "Fallback content",
                        "metadata": {"fallback": True}
                    }
                    result = workflow.execute(content, {})
            else:
                result = workflow.execute(content, {})
            
            # Workflow should complete and return a result
            assert result is not None, "Workflow should return a result"
            assert "workflow_metadata" in result, "Result should contain workflow metadata"
    
    @given(
        content=st.text(min_size=10, max_size=500),
        failing_optional_agents=st.lists(
            st.sampled_from(list(OPTIONAL_AGENTS)),
            min_size=1,
            max_size=len(OPTIONAL_AGENTS),
            unique=True
        )
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_property_optional_agents_can_fail(self, mock_create_agents, content, failing_optional_agents):
        """
        Property: Workflow must complete successfully even if optional agents fail
        
        Optional agents: assessment, visualization, narrative
        These agents enhance content but are not essential.
        """
        # Skip if content is empty or whitespace only
        assume(content.strip())
        
        failing_agents = set(failing_optional_agents)
        
        # Create mock agents
        mock_agents = self._create_mock_agents(failing_agents)
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        result = workflow.execute(content, {})
        
        # Property: Workflow completes despite optional agent failures
        assert result is not None, "Workflow should complete with optional agent failures"
        assert "workflow_metadata" in result, "Result should contain workflow metadata"
        
        # Verify failed agents are tracked
        failed_list = result["workflow_metadata"]["failed_agents"]
        for failed_agent in failing_agents:
            assert failed_agent in failed_list, \
                f"Failed optional agent {failed_agent} should be tracked in metadata"
        
        # Verify successful agents completed
        successful_agents = result["workflow_metadata"]["successful_agents"]
        for agent_type in CRITICAL_AGENTS:
            assert agent_type in successful_agents, \
                f"Critical agent {agent_type} should have completed successfully"
    
    @given(
        content=st.text(min_size=10, max_size=500),
        num_agents_to_fail=st.integers(min_value=0, max_value=5)
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_property_all_agents_executed_in_order(self, mock_create_agents, content, num_agents_to_fail):
        """
        Property: All agents must be executed in the defined sequence
        
        The workflow should attempt to execute agents in order:
        1. content_structuring
        2. learning_objectives
        3. assessment
        4. visualization
        5. narrative
        """
        # Skip if content is empty or whitespace only
        assume(content.strip())
        
        execution_order = []
        
        def track_execution(agent_type):
            def mock_process(*args, **kwargs):
                execution_order.append(agent_type)
                return {
                    "agent_type": agent_type,
                    "processed_content": f"Processed by {agent_type}",
                    "metadata": {}
                }
            return mock_process
        
        # Create mock agents that track execution order
        mock_agents = {}
        for agent_type in AGENT_TYPES:
            mock_agent = Mock()
            mock_agent.process_content = Mock(side_effect=track_execution(agent_type))
            mock_agents[agent_type] = mock_agent
        
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        result = workflow.execute(content, {})
        
        # Property: Agents executed in correct order
        expected_order = ["content_structuring", "learning_objectives", "assessment", "visualization", "narrative"]
        assert execution_order == expected_order, \
            f"Agents should execute in order {expected_order}, but got {execution_order}"
        
        # Property: All agents were attempted
        assert len(execution_order) == len(AGENT_TYPES), \
            f"All {len(AGENT_TYPES)} agents should be executed"
    
    @given(results=agent_results_strategy())
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_property_minimum_results_required(self, mock_create_agents, results):
        """
        Property: Workflow requires at least one critical agent result to proceed
        
        At minimum, either content_structuring OR learning_objectives must succeed.
        """
        # Create mock agents
        mock_agents = {}
        for agent_type in AGENT_TYPES:
            mock_agent = Mock()
            if agent_type in results:
                mock_agent.process_content.return_value = results[agent_type]
            else:
                mock_agent.process_content.side_effect = AgentExecutionError(
                    f"{agent_type} failed",
                    agent_type=agent_type
                )
            mock_agents[agent_type] = mock_agent
        
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        
        # Check if we have at least one critical agent result
        has_critical_result = any(agent in results for agent in CRITICAL_AGENTS)
        
        if has_critical_result:
            # Property: With critical agent result, workflow should complete
            result = workflow.execute("Test content", {})
            assert result is not None, "Workflow should complete with critical agent results"
            assert "workflow_metadata" in result
        else:
            # Property: Without critical agent results, workflow should fail
            # (unless fallback is available)
            with patch.object(workflow, '_create_fallback_result', return_value=None):
                with pytest.raises(WorkflowExecutionError) as exc_info:
                    workflow.execute("Test content", {})
                
                error = exc_info.value
                assert "Insufficient agent results" in str(error) or len(error.failed_agents) > 0
    
    @given(
        content=st.text(min_size=10, max_size=500),
        context=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(st.text(max_size=50), st.integers(), st.booleans()),
            max_size=5
        )
    )
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_property_context_propagated_to_agents(self, mock_create_agents, content, context):
        """
        Property: Context must be propagated to all agents during execution
        
        Each agent should receive the workflow context including previous results.
        """
        # Skip if content is empty or whitespace only
        assume(content.strip())
        
        received_contexts = {}
        
        def capture_context(agent_type):
            def mock_process(content, ctx):
                received_contexts[agent_type] = ctx
                return {
                    "agent_type": agent_type,
                    "processed_content": f"Processed by {agent_type}",
                    "metadata": {}
                }
            return mock_process
        
        # Create mock agents that capture context
        mock_agents = {}
        for agent_type in AGENT_TYPES:
            mock_agent = Mock()
            mock_agent.process_content = Mock(side_effect=capture_context(agent_type))
            mock_agents[agent_type] = mock_agent
        
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        result = workflow.execute(content, context)
        
        # Property: All agents received context
        assert len(received_contexts) == len(AGENT_TYPES), \
            "All agents should receive context"
        
        # Property: Context includes original content
        for agent_type, ctx in received_contexts.items():
            assert "original_content" in ctx, \
                f"Agent {agent_type} should receive original_content in context"
            assert ctx["original_content"] == content, \
                f"Agent {agent_type} should receive correct original content"
        
        # Property: Context includes previous results (for agents after first)
        for i, agent_type in enumerate(AGENT_TYPES[1:], start=1):
            ctx = received_contexts[agent_type]
            assert "previous_results" in ctx, \
                f"Agent {agent_type} should receive previous_results in context"
            
            # Should have results from all previous agents
            previous_agent_types = AGENT_TYPES[:i]
            for prev_agent in previous_agent_types:
                assert prev_agent in ctx["previous_results"], \
                    f"Agent {agent_type} should have {prev_agent} in previous_results"
    
    @given(content=st.text(min_size=10, max_size=500))
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_property_workflow_metadata_completeness(self, mock_create_agents, content):
        """
        Property: Workflow result must include complete metadata about execution
        
        Metadata should include:
        - execution_id
        - failed_agents list
        - successful_agents list
        - execution_time
        """
        # Skip if content is empty or whitespace only
        assume(content.strip())
        
        # Create mock agents (all succeed)
        mock_agents = self._create_mock_agents(set())
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        result = workflow.execute(content, {})
        
        # Property: Result contains workflow_metadata
        assert "workflow_metadata" in result, "Result must contain workflow_metadata"
        
        metadata = result["workflow_metadata"]
        
        # Property: Metadata contains required fields
        required_fields = ["execution_id", "failed_agents", "successful_agents", "execution_time"]
        for field in required_fields:
            assert field in metadata, f"Metadata must contain {field}"
        
        # Property: execution_id is positive integer
        assert isinstance(metadata["execution_id"], int), "execution_id must be integer"
        assert metadata["execution_id"] > 0, "execution_id must be positive"
        
        # Property: failed_agents is a list
        assert isinstance(metadata["failed_agents"], list), "failed_agents must be a list"
        
        # Property: successful_agents is a list
        assert isinstance(metadata["successful_agents"], list), "successful_agents must be a list"
        
        # Property: execution_time is a number
        assert isinstance(metadata["execution_time"], (int, float)), "execution_time must be numeric"
        assert metadata["execution_time"] >= 0, "execution_time must be non-negative"
        
        # Property: All agents are accounted for (either failed or successful)
        all_agents = set(metadata["failed_agents"]) | set(metadata["successful_agents"])
        assert len(all_agents) == len(AGENT_TYPES), \
            "All agents should be accounted for in metadata"
    
    # Helper methods
    
    def _create_mock_agents(self, failing_agents: Set[str]) -> Dict[str, Mock]:
        """
        Create mock agents with specified failure patterns
        
        Args:
            failing_agents: Set of agent types that should fail
            
        Returns:
            Dictionary of mock agents
        """
        mock_agents = {}
        
        for agent_type in AGENT_TYPES:
            mock_agent = Mock()
            
            if agent_type in failing_agents:
                # Agent fails
                mock_agent.process_content.side_effect = AgentExecutionError(
                    f"{agent_type} execution failed",
                    agent_type=agent_type
                )
            else:
                # Agent succeeds
                mock_agent.process_content.return_value = {
                    "agent_type": agent_type,
                    "processed_content": f"Processed by {agent_type}",
                    "metadata": {
                        "agent_name": f"{agent_type}_agent",
                        "processing_timestamp": "2024-01-01T00:00:00"
                    }
                }
            
            mock_agents[agent_type] = mock_agent
        
        return mock_agents


@pytest.mark.property
class TestAgentCoordinationInvariants:
    """Test invariants that must hold for agent coordination"""
    
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_invariant_workflow_never_returns_none(self, mock_create_agents):
        """
        Invariant: Workflow execution must either return a valid result or raise an exception
        
        It should never return None.
        """
        # Create mock agents (all succeed)
        mock_agents = {}
        for agent_type in AGENT_TYPES:
            mock_agent = Mock()
            mock_agent.process_content.return_value = {
                "agent_type": agent_type,
                "processed_content": f"Processed by {agent_type}",
                "metadata": {}
            }
            mock_agents[agent_type] = mock_agent
        
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        result = workflow.execute("Test content", {})
        
        # Invariant: Result is never None
        assert result is not None, "Workflow must never return None"
        assert isinstance(result, dict), "Workflow must return a dictionary"
    
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_invariant_failed_agents_tracked(self, mock_create_agents):
        """
        Invariant: All failed agents must be tracked in workflow metadata
        """
        # Make visualization agent fail
        failing_agent = "visualization"
        
        mock_agents = {}
        for agent_type in AGENT_TYPES:
            mock_agent = Mock()
            if agent_type == failing_agent:
                mock_agent.process_content.side_effect = AgentExecutionError(
                    f"{agent_type} failed",
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
        
        # Invariant: Failed agent is tracked
        assert failing_agent in result["workflow_metadata"]["failed_agents"], \
            f"Failed agent {failing_agent} must be tracked in metadata"
    
    @patch('agents.agent_factory.AgentFactory.create_all_agents')
    def test_invariant_execution_count_increments(self, mock_create_agents):
        """
        Invariant: Workflow execution count must increment with each execution
        """
        # Create mock agents (all succeed)
        mock_agents = {}
        for agent_type in AGENT_TYPES:
            mock_agent = Mock()
            mock_agent.process_content.return_value = {
                "agent_type": agent_type,
                "processed_content": f"Processed by {agent_type}",
                "metadata": {}
            }
            mock_agents[agent_type] = mock_agent
        
        mock_create_agents.return_value = mock_agents
        
        workflow = PedagogyWorkflow()
        
        # Execute multiple times
        execution_ids = []
        for i in range(3):
            result = workflow.execute(f"Test content {i}", {})
            execution_ids.append(result["workflow_metadata"]["execution_id"])
        
        # Invariant: Execution IDs increment
        assert execution_ids == [1, 2, 3], \
            "Execution IDs must increment sequentially"
        
        # Invariant: Workflow tracks execution count
        assert workflow.execution_count == 3, \
            "Workflow must track total execution count"
