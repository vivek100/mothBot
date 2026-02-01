"""
Marimo Chain Engine - Execute tool chains using Marimo as the engine.

This package provides a streaming execution engine that:
1. Takes JSON plans as input
2. Executes tools via Marimo's reactive cell system
3. Streams events as execution progresses
4. Returns final verdict and outputs

Usage:
    from marimo_engine import execute_plan, execute_plan_sync
    from marimo_engine.tools import get_example_tools
    from marimo_engine.plans import get_test_plan
    
    # Sync execution
    result = execute_plan_sync(get_test_plan(), get_example_tools())
    print(result.verdict)  # SUCCESS
    
    # Async streaming
    async for event in execute_plan(plan, tools):
        print(event.type, event.msg)
"""

from .core import (
    Event,
    EventType,
    Verdict,
    ExecutionResult,
    execute_plan,
    execute_plan_sync,
)

from .tools import (
    ToolRegistry,
    create_registry,
    get_example_tools,
)

from .plans import (
    Step,
    Plan,
    validate_plan,
    get_test_plan,
    get_example_plans,
)

__version__ = "0.1.0"

__all__ = [
    # Core
    "Event",
    "EventType",
    "Verdict",
    "ExecutionResult",
    "execute_plan",
    "execute_plan_sync",
    # Tools
    "ToolRegistry",
    "create_registry",
    "get_example_tools",
    # Plans
    "Step",
    "Plan",
    "validate_plan",
    "get_test_plan",
    "get_example_plans",
]
