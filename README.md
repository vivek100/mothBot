# Marimo Chain Engine

A streaming execution engine for tool chains, designed to use Marimo as the execution backend.

## Vision

Use **Marimo as the execution engine** for tool chains, not just a display layer.

```
JSON Plan → Marimo Cells → Execute → Stream Events → Return Results
```

## Features

- **Streaming Execution**: Async generator yields events as execution progresses
- **Sync & Async Tools**: Supports both synchronous and asynchronous tool functions
- **Conditional Execution**: `run_if` conditions to skip steps
- **Intervention Support**: `intervention_if` triggers human review
- **Expression Evaluation**: Safe evaluation of `$s1.value > 10` style conditions
- **Pydantic Validation**: Type-safe plan and event schemas
- **Pipecat Compatible**: Designed for integration with Pipecat agents

## Installation

```powershell
cd toolChainEngine
pip install -r requirements.txt
```

## Quick Start

### Interactive Testing (Recommended)

The easiest way to get started is using the interactive Marimo app:

```powershell
cd toolChainEngine/marimo_engine
marimo run app.py
```

This opens a web interface where you can:
- Select from example plans (Diagnostic Sequence, Conditional Execution, etc.)
- Run plans and see real-time execution
- View detailed reports and findings

### Synchronous Execution

```python
from marimo_engine import execute_plan_sync, get_example_tools, get_test_plan

# Get example tools and plan
tools = get_example_tools()
plan = get_test_plan()

# Execute
result = execute_plan_sync(plan, tools)

print(f"Verdict: {result.verdict}")
print(f"Outputs: {result.outputs}")
```

### Async Streaming

```python
import asyncio
from marimo_engine import execute_plan, get_example_tools

async def main():
    tools = get_example_tools()
    plan = {
        "steps": [
            {"id": "s1", "tool": "scan_hull"},
            {"id": "s2", "tool": "check_oxygen", "key_finding": True},
            {"id": "s3", "tool": "analyze_atmosphere", "args": {"o2_level": "$s2.level"}}
        ]
    }
    
    async for event in execute_plan(plan, tools):
        print(f"[{event.type.value}] {event.msg}")

asyncio.run(main())
```

### Custom Tools

```python
from marimo_engine import execute_plan_sync, create_registry

# Define your tools
def my_tool(param: str) -> dict:
    return {"result": f"Processed: {param}"}

async def my_async_tool(value: int) -> dict:
    await asyncio.sleep(0.1)
    return {"doubled": value * 2}

# Create registry
tools = create_registry(my_tool, my_async_tool)

# Or as dict
tools = {
    "my_tool": my_tool,
    "my_async_tool": my_async_tool,
}

# Execute plan
plan = {
    "steps": [
        {"id": "s1", "tool": "my_tool", "args": {"param": "hello"}},
        {"id": "s2", "tool": "my_async_tool", "args": {"value": 21}},
    ]
}

result = execute_plan_sync(plan, tools)
```

## Plan Schema

```python
{
    "id": "plan_id",           # Optional identifier
    "name": "Plan Name",       # Optional name
    "description": "...",      # Optional description
    "steps": [
        {
            "id": "s1",                    # Required: unique step ID
            "tool": "tool_name",           # Required: tool to execute
            "description": "...",          # Optional: human-readable
            "args": {"key": "value"},      # Optional: tool arguments
            "run_if": "$s0.flag == True",  # Optional: skip if false
            "key_finding": true,           # Optional: mark as critical
            "intervention_if": "$s1.severity == 'HIGH'"  # Optional: trigger review
        }
    ]
}
```

## Reference Syntax

Use `$` to reference previous step outputs:

```python
"$s1"           # Entire output of step s1
"$s1.value"     # s1's output["value"]
"$s1.data.nested"  # s1's output["data"]["nested"]
```

## Condition Expressions

Supported in `run_if` and `intervention_if`:

```python
"$s1.flag"                    # Truthy check
"$s1.value > 10"              # Comparison
"$s1.status == 'OK'"          # Equality
"$s1.value > 10 and $s2.ok"   # Boolean AND
"$s1.value > 10 or $s2.ok"    # Boolean OR
"not $s1.error"               # Negation
```

## Event Types

| Event | When | Key Fields |
|-------|------|------------|
| `START` | Execution begins | `plan_id` |
| `STEP_START` | Step begins | `step_id`, `tool` |
| `STEP_COMPLETE` | Step succeeds | `step_id`, `output` |
| `STEP_SKIPPED` | Condition false | `step_id`, `msg` |
| `ERROR` | Step fails | `step_id`, `error` |
| `INTERVENTION_NEEDED` | Review required | `step_id`, `intervention_reason` |
| `FINISH` | Execution ends | `verdict`, `final_context` |

## Verdicts

| Verdict | Meaning |
|---------|---------|
| `SUCCESS` | All steps completed |
| `FAILURE` | An error occurred |
| `INTERVENTION_NEEDED` | Human review required |

## Pipecat Agent Integration

This engine is designed to work with Pipecat agents. You can create an agent that:
- Calls individual tools (scan_hull, check_oxygen, etc.)
- Executes full diagnostic plans
- Streams responses to a web frontend

### Quick Start with Pipecat

See [PIPECAT_QUICKSTART.md](PIPECAT_QUICKSTART.md) for a step-by-step guide to:
1. Setting up a Pipecat agent
2. Integrating individual tools
3. Adding plan execution capability
4. Creating a web frontend

### Detailed Implementation Plan

See [PIPECAT_AGENT_PLAN.md](PIPECAT_AGENT_PLAN.md) for:
- Architecture overview
- Complete implementation steps
- File structure
- Testing scenarios

### Basic Pipecat Tool Example

```python
from pipecat.frames import TextFrame
from marimo_engine import execute_plan

async def diagnostic_tool(plan_json: str):
    """Pipecat tool that executes diagnostic plans."""
    import json
    plan = json.loads(plan_json)
    
    async for event in execute_plan(plan, registered_tools):
        yield TextFrame(f"[{event.type.value}] {event.msg}")
```

## Testing

### Interactive Testing with Marimo App

The easiest way to test the engine is using the interactive Marimo app:

```powershell
cd toolChainEngine/marimo_engine
marimo run app.py
```

This will open a web interface where you can:
- Select from multiple example plans
- Toggle verbose output to see detailed step results
- Run plans and see real-time execution events
- View final execution reports with verdicts, duration, and critical findings

The app provides a visual, interactive way to test the engine without writing code.

### Unit Testing

For programmatic testing:

```powershell
cd toolChainEngine/marimo_engine
python test_engine.py
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design documentation.

## Project Structure

```
marimo_engine/
├── core/
│   ├── events.py       # Event types and schemas
│   ├── executor.py     # Main execution logic
│   ├── generator.py    # JSON → Marimo cells
│   └── expressions.py  # Safe expression evaluation
├── tools/
│   ├── registry.py     # Tool management
│   └── examples.py     # Example tools
├── plans/
│   ├── schema.py       # Pydantic models
│   └── examples.py     # Example plans
├── agent/              # Pipecat agent (see PIPECAT_QUICKSTART.md)
│   ├── bot.py          # Agent implementation
│   ├── bot_runner.py    # HTTP/WebSocket server
│   └── tools.py        # Tool wrappers
├── client/             # Web frontend (if using Pipecat)
│   ├── index.html
│   └── app.js
├── app.py              # Interactive Marimo app for testing
├── test_engine.py      # Unit tests
├── PIPECAT_AGENT_PLAN.md    # Detailed implementation plan
├── PIPECAT_QUICKSTART.md    # Quick start guide
└── README.md           # This file
```
