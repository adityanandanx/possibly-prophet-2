# Agent Error Handling and Retry Mechanisms

## Overview

This document describes the enhanced error handling and retry mechanisms implemented for the Strands Agents integration in the Educational Content Generator system. These mechanisms ensure robust and reliable agent execution with graceful failure handling per Requirements 1.2.

## Architecture

### Components

1. **Custom Exception Hierarchy** (`agents/exceptions.py`)
2. **Retry Handler with Exponential Backoff** (`agents/retry_handler.py`)
3. **Circuit Breaker Pattern** (`agents/retry_handler.py`)
4. **Enhanced Base Agent** (`agents/base_agent.py`)
5. **Enhanced Pedagogy Workflow** (`agents/pedagogy_workflow.py`)

## Custom Exception Hierarchy

### Agent Exceptions

- **`AgentError`**: Base exception for all agent-related errors
  - Contains: message, agent_type, context, original_error
  - Provides `to_dict()` method for serialization

- **`AgentInitializationError`**: Raised when agent fails to initialize
- **`AgentExecutionError`**: Raised when agent execution fails
- **`AgentTimeoutError`**: Raised when agent execution times out
- **`AgentValidationError`**: Raised when agent input/output validation fails
- **`AgentCommunicationError`**: Raised when agent communication fails

### Workflow Exceptions

- **`WorkflowError`**: Base exception for workflow-related errors
  - Contains: message, failed_agents, partial_results, original_error
  - Provides `to_dict()` method for serialization

- **`WorkflowExecutionError`**: Raised when workflow execution fails
- **`WorkflowTimeoutError`**: Raised when workflow execution times out
- **`WorkflowValidationError`**: Raised when workflow output validation fails

## Retry Handler

### Features

- **Exponential Backoff**: Delays increase exponentially between retries
- **Configurable Parameters**:
  - `max_retries`: Maximum number of retry attempts (default: 3)
  - `initial_delay`: Initial delay in seconds (default: 1.0)
  - `max_delay`: Maximum delay in seconds (default: 60.0)
  - `exponential_base`: Base for exponential calculation (default: 2.0)
  - `exceptions`: Tuple of exceptions to catch and retry
  - `on_retry`: Optional callback function called on each retry

### Usage

```python
from agents.retry_handler import RetryHandler

@RetryHandler.retry_with_backoff(
    max_retries=3,
    initial_delay=1.0,
    max_delay=30.0,
    exceptions=(AgentExecutionError,)
)
def process_content(content):
    # Agent processing logic
    pass
```

### Async Support

The retry handler also supports async functions:

```python
@RetryHandler.retry_async_with_backoff(
    max_retries=3,
    initial_delay=1.0
)
async def async_process_content(content):
    # Async agent processing logic
    pass
```

## Circuit Breaker Pattern

### States

1. **CLOSED**: Normal operation, requests pass through
2. **OPEN**: Too many failures, requests fail immediately
3. **HALF_OPEN**: Testing if service recovered, limited requests pass through

### Configuration

- `failure_threshold`: Number of failures before opening circuit (default: 5)
- `recovery_timeout`: Seconds to wait before attempting recovery (default: 60)
- `expected_exception`: Exception type to track for failures

### Behavior

1. **CLOSED State**: All requests are processed normally
2. **Failure Tracking**: Each failure increments the failure count
3. **Opening**: When failure count reaches threshold, circuit opens
4. **OPEN State**: Requests fail immediately with `AgentExecutionError`
5. **Recovery Attempt**: After recovery timeout, circuit enters HALF_OPEN
6. **HALF_OPEN State**: Next request is allowed through to test recovery
7. **Success**: Circuit closes and failure count resets
8. **Failure**: Circuit reopens

### Usage

```python
from agents.retry_handler import CircuitBreaker

cb = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=AgentExecutionError
)

result = cb.call(agent.process_content, content, context)
```

## Enhanced Base Agent

### Input Validation

- **Empty Content Check**: Rejects empty or whitespace-only content
- **Size Validation**: Enforces 100KB maximum content size
- **Context Validation**: Validates context structure

### Output Validation

- **Non-Empty Result**: Ensures agent returns a result
- **Required Fields**: Validates presence of `processed_content` field
- **Structure Validation**: Ensures result is a dictionary

### Timeout Protection

- **Configurable Timeout**: Default 120 seconds per agent
- **Signal-Based**: Uses SIGALRM for timeout enforcement
- **Graceful Handling**: Raises `AgentTimeoutError` on timeout

### Error Handling Flow

```
process_content()
    ↓
Circuit Breaker Check
    ↓
Retry Handler (with exponential backoff)
    ↓
Input Validation
    ↓
Timeout Protection
    ↓
Agent Execution
    ↓
Output Validation
    ↓
Return Result
```

## Enhanced Pedagogy Workflow

### Critical vs Optional Agents

**Critical Agents** (must succeed):
- `content_structuring`
- `learning_objectives`

**Optional Agents** (can fail):
- `assessment`
- `visualization`
- `narrative`

### Fallback Mechanisms

When a critical agent fails, the workflow attempts to use a fallback:

1. **Content Structuring Fallback**: Returns basic section structure
2. **Learning Objectives Fallback**: Returns generic objectives

If fallback is unavailable, workflow raises `WorkflowExecutionError`.

### Partial Results

The workflow tracks partial results even when some agents fail:

```python
{
    "workflow_metadata": {
        "execution_id": 1,
        "failed_agents": ["visualization"],
        "successful_agents": ["content_structuring", "learning_objectives", "assessment", "narrative"],
        "execution_time": 45.2
    }
}
```

### Error Recovery Strategy

1. **Agent Failure**: Log error and store error information
2. **Critical Agent**: Attempt fallback mechanism
3. **Optional Agent**: Continue with remaining agents
4. **Minimum Results Check**: Ensure at least one critical agent succeeded
5. **Compilation**: Compile results from successful agents
6. **Metadata**: Include failure information in result

## Configuration

### Agent Configuration (`config/agents_config.py`)

Each agent type includes:

```python
{
    "name": "Agent Name",
    "description": "Agent description",
    "system_prompt": "Agent system prompt",
    "max_retries": 3,
    "timeout_seconds": 120,
    "failure_threshold": 5,
    "recovery_timeout": 60
}
```

### Workflow Configuration

```python
WORKFLOW_CONFIG = {
    "max_retries": 3,
    "timeout": 300,  # 5 minutes
    "parallel_execution": True,
    "failure_threshold": 5,
    "recovery_timeout": 60
}
```

## Testing

### Test Coverage

The implementation includes comprehensive tests covering:

1. **Exception Creation and Serialization** (4 tests)
2. **Circuit Breaker Behavior** (4 tests)
3. **Retry Handler Logic** (5 tests)
4. **Base Agent Error Handling** (5 tests)
5. **Workflow Error Handling** (4 tests)
6. **Integration Tests** (2 tests)

**Total: 24 tests, all passing**

### Running Tests

```bash
cd backend
uv run pytest tests/test_agent_error_handling.py -v
```

## Usage Examples

### Basic Agent Usage with Error Handling

```python
from agents.base_agent import BaseEducationalAgent
from agents.exceptions import AgentValidationError, AgentExecutionError

try:
    agent = BaseEducationalAgent("content_structuring")
    result = agent.process_content(content, context)
except AgentValidationError as e:
    # Handle validation errors (bad input/output)
    logger.error(f"Validation error: {e.to_dict()}")
except AgentExecutionError as e:
    # Handle execution errors (agent failed)
    logger.error(f"Execution error: {e.to_dict()}")
except AgentTimeoutError as e:
    # Handle timeout errors
    logger.error(f"Timeout error: {e.to_dict()}")
```

### Workflow Usage with Error Handling

```python
from agents.pedagogy_workflow import PedagogyWorkflow
from agents.exceptions import WorkflowExecutionError

try:
    workflow = PedagogyWorkflow()
    result = workflow.execute(content, context)
    
    # Check for partial failures
    if result["workflow_metadata"]["failed_agents"]:
        logger.warning(f"Some agents failed: {result['workflow_metadata']['failed_agents']}")
    
except WorkflowExecutionError as e:
    # Handle workflow failures
    logger.error(f"Workflow failed: {e.to_dict()}")
    
    # Access partial results if available
    if e.partial_results:
        logger.info(f"Partial results available: {list(e.partial_results.keys())}")
```

## Benefits

1. **Reliability**: Automatic retries with exponential backoff reduce transient failures
2. **Resilience**: Circuit breaker prevents cascading failures
3. **Observability**: Detailed error information and logging
4. **Graceful Degradation**: Fallback mechanisms for critical agents
5. **Partial Success**: Workflow continues with available results
6. **Configurability**: All parameters are configurable per agent
7. **Testability**: Comprehensive test coverage ensures correctness

## Monitoring and Debugging

### Logging

All error handling components include detailed logging:

- Agent initialization and execution
- Retry attempts with delays
- Circuit breaker state changes
- Workflow execution progress
- Fallback mechanism usage

### Error Serialization

All exceptions provide `to_dict()` method for:

- Structured logging
- API error responses
- Monitoring and alerting
- Debugging and analysis

### Metrics

The workflow tracks:

- Execution count
- Failure count
- Last execution time
- Failed agents per execution
- Successful agents per execution
- Execution duration

## Future Enhancements

Potential improvements for future iterations:

1. **Async Workflow**: Support for parallel agent execution
2. **Persistent Circuit Breaker**: Store circuit state in database
3. **Advanced Metrics**: Integration with monitoring systems (Prometheus, DataDog)
4. **Adaptive Retry**: Adjust retry parameters based on error patterns
5. **Agent Health Checks**: Proactive health monitoring
6. **Distributed Tracing**: Integration with OpenTelemetry
7. **Rate Limiting**: Prevent overwhelming downstream services
8. **Bulkhead Pattern**: Isolate agent failures

## Compliance with Requirements

This implementation satisfies **Requirements 1.2: Multi-Agent Coordination**:

✅ Multiple pedagogy agents can be configured with different specializations
✅ Agents communicate effectively through Strands Agents framework
✅ Agent coordination follows defined workflows for content generation
✅ **System handles agent failures gracefully with fallback mechanisms**

The enhanced error handling and retry mechanisms ensure robust agent coordination with comprehensive failure recovery strategies.
