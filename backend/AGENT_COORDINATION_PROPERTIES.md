# Agent Coordination Property-Based Tests

## Overview

This document describes the property-based tests for agent coordination in the Educational Content Generator system. These tests validate **Property 2** from the design document:

> **Property 2: Agent Coordination**  
> The agent orchestration system must ensure that all required pedagogy agents complete their tasks successfully before proceeding to content generation.

## Test Framework

- **Testing Library**: Hypothesis (Python property-based testing)
- **Test File**: `tests/test_agent_coordination_properties.py`
- **Validates**: Requirements 1.2 (Multi-Agent Coordination)

## Agent Types

The system uses five pedagogy agents organized into two categories:

### Critical Agents (Must Complete)
- **content_structuring**: Organizes raw content into logical sections
- **learning_objectives**: Defines educational goals and outcomes

### Optional Agents (Can Fail)
- **assessment**: Creates questions and evaluation criteria
- **visualization**: Identifies concepts suitable for animation
- **narrative**: Ensures coherent storytelling and flow

## Properties Tested

### 1. Critical Agents Must Complete
**Property**: If any critical agent fails without fallback, workflow must fail.

**Test**: `test_property_critical_agents_must_complete`

**Validates**:
- Critical agents (content_structuring, learning_objectives) are essential
- Workflow fails if critical agent fails without fallback
- Workflow succeeds if fallback is available or no critical failures occur
- Failed agents are tracked in workflow metadata

**Examples Tested**: 50 random scenarios with various failure patterns

### 2. Optional Agents Can Fail
**Property**: Workflow must complete successfully even if optional agents fail.

**Test**: `test_property_optional_agents_can_fail`

**Validates**:
- Optional agents (assessment, visualization, narrative) enhance but aren't essential
- Workflow completes despite optional agent failures
- Failed optional agents are tracked in metadata
- Critical agents still complete successfully

**Examples Tested**: 50 random scenarios with optional agent failures

### 3. All Agents Executed in Order
**Property**: All agents must be executed in the defined sequence.

**Test**: `test_property_all_agents_executed_in_order`

**Validates**:
- Agents execute in correct order: content_structuring → learning_objectives → assessment → visualization → narrative
- All agents are attempted regardless of previous failures
- Execution order is deterministic

**Examples Tested**: 50 random content inputs

### 4. Minimum Results Required
**Property**: Workflow requires at least one critical agent result to proceed.

**Test**: `test_property_minimum_results_required`

**Validates**:
- At minimum, either content_structuring OR learning_objectives must succeed
- Workflow completes with at least one critical agent result
- Workflow fails without critical agent results (unless fallback available)

**Examples Tested**: 50 random agent result combinations

### 5. Context Propagated to Agents
**Property**: Context must be propagated to all agents during execution.

**Test**: `test_property_context_propagated_to_agents`

**Validates**:
- All agents receive workflow context
- Context includes original content
- Context includes previous agent results (for agents after first)
- Each agent can access results from all previous agents

**Examples Tested**: 30 random content and context combinations

### 6. Workflow Metadata Completeness
**Property**: Workflow result must include complete metadata about execution.

**Test**: `test_property_workflow_metadata_completeness`

**Validates**:
- Result contains workflow_metadata
- Metadata includes: execution_id, failed_agents, successful_agents, execution_time
- execution_id is positive integer
- failed_agents and successful_agents are lists
- execution_time is non-negative number
- All agents accounted for (either failed or successful)

**Examples Tested**: 30 random content inputs

## Invariants Tested

### 1. Workflow Never Returns None
**Invariant**: Workflow execution must either return a valid result or raise an exception.

**Test**: `test_invariant_workflow_never_returns_none`

**Validates**:
- Workflow never returns None
- Result is always a dictionary

### 2. Failed Agents Tracked
**Invariant**: All failed agents must be tracked in workflow metadata.

**Test**: `test_invariant_failed_agents_tracked`

**Validates**:
- Failed agents appear in metadata.failed_agents list
- Tracking is accurate and complete

### 3. Execution Count Increments
**Invariant**: Workflow execution count must increment with each execution.

**Test**: `test_invariant_execution_count_increments`

**Validates**:
- Execution IDs increment sequentially (1, 2, 3, ...)
- Workflow tracks total execution count
- Each execution has unique ID

## Test Strategies

### Agent Execution Scenario Strategy
Generates random scenarios with:
- Varying numbers of failing agents (0-5)
- Random content strings (10-500 characters)
- Random fallback availability

### Agent Results Strategy
Generates valid agent results with:
- Random successful agent combinations
- Realistic result structures
- Proper metadata

## Running the Tests

```bash
# Run all property tests
cd backend
uv run pytest tests/test_agent_coordination_properties.py -v

# Run with statistics
uv run pytest tests/test_agent_coordination_properties.py --hypothesis-show-statistics

# Run specific property test
uv run pytest tests/test_agent_coordination_properties.py::TestAgentCoordinationProperties::test_property_critical_agents_must_complete -v
```

## Test Results

All 9 property tests pass successfully:
- ✅ Critical agents must complete
- ✅ Optional agents can fail
- ✅ All agents executed in order
- ✅ Minimum results required
- ✅ Context propagated to agents
- ✅ Workflow metadata completeness
- ✅ Workflow never returns None
- ✅ Failed agents tracked
- ✅ Execution count increments

## Coverage

These property-based tests provide comprehensive coverage of agent coordination by:
1. Testing hundreds of random scenarios automatically
2. Validating critical vs optional agent behavior
3. Ensuring proper error handling and fallback mechanisms
4. Verifying metadata tracking and completeness
5. Confirming execution order and context propagation

## Integration with Error Handling

These tests work in conjunction with:
- `tests/test_agent_error_handling.py`: Unit tests for error handling components
- `agents/retry_handler.py`: Retry logic with exponential backoff
- `agents/exceptions.py`: Custom exception hierarchy
- `agents/pedagogy_workflow.py`: Workflow orchestration with fallback

## Future Enhancements

Potential additions to property testing:
1. Async agent execution properties
2. Concurrent agent execution properties
3. Agent timeout behavior properties
4. Resource cleanup properties
5. Performance degradation properties
