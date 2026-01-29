# Agent Coordination Property-Based Tests

## Quick Start

```bash
# Run all agent coordination property tests
cd backend
uv run pytest tests/test_agent_coordination_properties.py -v

# Run with Hypothesis statistics
uv run pytest tests/test_agent_coordination_properties.py --hypothesis-show-statistics

# Run both property tests and error handling tests
uv run pytest tests/test_agent_coordination_properties.py tests/test_agent_error_handling.py -v
```

## What These Tests Validate

These property-based tests validate **Property 2** from the design document:

> **Property 2: Agent Coordination**  
> The agent orchestration system must ensure that all required pedagogy agents complete their tasks successfully before proceeding to content generation.

## Test Coverage

### 6 Core Properties
1. **Critical Agents Must Complete** - Workflow fails if critical agents fail without fallback
2. **Optional Agents Can Fail** - Workflow succeeds even if optional agents fail
3. **All Agents Executed in Order** - Agents execute in defined sequence
4. **Minimum Results Required** - At least one critical agent must succeed
5. **Context Propagated to Agents** - All agents receive workflow context
6. **Workflow Metadata Completeness** - Results include complete execution metadata

### 3 System Invariants
1. **Workflow Never Returns None** - Always returns dict or raises exception
2. **Failed Agents Tracked** - All failures recorded in metadata
3. **Execution Count Increments** - Each execution has unique sequential ID

## Test Statistics

- **Total Tests**: 9 property-based tests
- **Examples per Test**: 30-50 random scenarios
- **Total Scenarios Tested**: ~400 automatically generated test cases
- **Execution Time**: ~1 second for all tests

## Key Features

### Hypothesis Property-Based Testing
- Automatically generates hundreds of test scenarios
- Tests edge cases that manual tests might miss
- Validates properties across wide input ranges
- Provides reproducible test failures with seeds

### Agent Types Tested
- **Critical**: content_structuring, learning_objectives (must succeed)
- **Optional**: assessment, visualization, narrative (can fail)

### Failure Scenarios Covered
- Single agent failures
- Multiple agent failures
- Critical vs optional agent failures
- Fallback mechanism activation
- Context propagation with failures
- Metadata tracking with partial failures

## Integration with Error Handling

These tests complement the error handling tests in `test_agent_error_handling.py`:
- Property tests validate high-level coordination behavior
- Error handling tests validate low-level error mechanisms
- Together they provide comprehensive coverage of the agent system

## Documentation

See `AGENT_COORDINATION_PROPERTIES.md` for detailed documentation of:
- Each property tested
- Test strategies used
- Expected behaviors
- Integration with error handling system

## Troubleshooting

### Test Failures
If a property test fails, Hypothesis will provide:
- A minimal failing example
- A seed to reproduce the failure
- The specific property that was violated

Example:
```
You can add @seed(156949565899626585614965968365207858043) to reproduce this failure.
```

### Running Specific Tests
```bash
# Run single property test
uv run pytest tests/test_agent_coordination_properties.py::TestAgentCoordinationProperties::test_property_critical_agents_must_complete -v

# Run with verbose output
uv run pytest tests/test_agent_coordination_properties.py -vv

# Run with full traceback
uv run pytest tests/test_agent_coordination_properties.py --tb=long
```

### Adjusting Test Parameters
Edit the `@settings` decorator in the test file:
```python
@settings(
    max_examples=50,  # Number of random scenarios to test
    deadline=None,    # No time limit per test
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
```

## Related Files

- `tests/test_agent_coordination_properties.py` - Property-based tests
- `tests/test_agent_error_handling.py` - Error handling unit tests
- `agents/pedagogy_workflow.py` - Workflow implementation
- `agents/base_agent.py` - Base agent with error handling
- `agents/retry_handler.py` - Retry and circuit breaker logic
- `agents/exceptions.py` - Custom exception hierarchy
- `AGENT_COORDINATION_PROPERTIES.md` - Detailed documentation
