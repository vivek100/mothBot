# Marimo Chain Engine - Architecture

## Vision

Use **Marimo as the execution engine** for tool chains, not just a display layer.

```
JSON Plan → Marimo Notebook (in-memory) → Execute via Marimo → Stream Events → Return Results
```

## Why Marimo as Engine?

1. **Reactive DAG execution** - Marimo automatically handles step dependencies
2. **Rich ecosystem** - Markdown cells, visualizations, UI elements as "tools"
3. **No custom executor** - Leverage Marimo's battle-tested execution model
4. **Future extensibility** - Markdown as tools, interactive debugging, etc.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pipecat / Your Agent                         │
│                                                                 │
│  tools = [scan_hull, check_oxygen, analyze_atmosphere, ...]    │
│                          │                                      │
│                          ▼                                      │
│         execute_plan(plan_json, tools) → AsyncIterator[Event]  │
│                          │                                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Marimo Engine Wrapper                         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Generator: JSON Plan → Marimo App (in-memory)        │   │
│  │    - Each step becomes a @app.cell                      │   │
│  │    - Dependencies ($s2.level) → cell function args      │   │
│  │    - Tools injected into cell scope                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 2. Executor: Run cells programmatically                 │   │
│  │    - Execute cells in dependency order                  │   │
│  │    - Yield events (STEP_START, STEP_COMPLETE, etc.)     │   │
│  │    - Handle errors and intervention conditions          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 3. Result: Final verdict + all step outputs             │   │
│  │    - SUCCESS / FAILURE / INTERVENTION_NEEDED            │   │
│  │    - All step outputs in context                        │   │
│  │    - Duration, error details if any                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Folder Structure

```
marimo_engine/
├── ARCHITECTURE.md          # This file
├── README.md                # Usage guide
├── requirements.txt         # Dependencies
│
├── core/                    # Core engine components
│   ├── __init__.py
│   ├── events.py           # Event types (START, STEP_COMPLETE, etc.)
│   ├── generator.py        # JSON → Marimo notebook generator
│   ├── executor.py         # Marimo execution wrapper
│   └── expressions.py      # Safe expression evaluation (run_if)
│
├── tools/                   # Tool management
│   ├── __init__.py
│   ├── registry.py         # Tool registration
│   └── examples.py         # Example tools (scan_hull, etc.)
│
├── plans/                   # Plan schemas
│   ├── __init__.py
│   ├── schema.py           # Pydantic models for plans
│   └── examples.py         # Example plans
│
├── app.py                   # Marimo visualization app (optional)
└── test_engine.py          # Tests
```

---

## Core Components

### 1. Events (`core/events.py`)

```python
class EventType(str, Enum):
    START = "START"
    STEP_START = "STEP_START"
    STEP_COMPLETE = "STEP_COMPLETE"
    STEP_SKIPPED = "STEP_SKIPPED"
    ERROR = "ERROR"
    INTERVENTION_NEEDED = "INTERVENTION_NEEDED"
    FINISH = "FINISH"

class Verdict(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    INTERVENTION_NEEDED = "INTERVENTION_NEEDED"
```

### 2. Generator (`core/generator.py`)

Converts JSON plan to executable Marimo cells:

```python
def generate_cells(plan: Plan, tools: ToolRegistry) -> List[Cell]:
    """
    Convert plan steps to Marimo cells.
    
    Input:
    {
        "steps": [
            {"id": "s1", "tool": "scan_hull"},
            {"id": "s2", "tool": "check_oxygen"},
            {"id": "s3", "tool": "analyze", "args": {"o2": "$s2.level"}}
        ]
    }
    
    Output: List of Cell objects ready for execution
    """
```

### 3. Executor (`core/executor.py`)

Main entry point - wraps Marimo execution:

```python
async def execute_plan(
    plan: dict | Plan,
    tools: dict[str, Callable]
) -> AsyncIterator[Event]:
    """
    Execute a plan using Marimo as the engine.
    
    Yields events as execution progresses.
    Returns final verdict and outputs.
    """

def execute_plan_sync(
    plan: dict | Plan,
    tools: dict[str, Callable]
) -> ExecutionResult:
    """
    Synchronous wrapper for simple use cases.
    """
```

---

## Plan Schema

```python
class Step(BaseModel):
    id: str                           # Unique step identifier
    tool: str                         # Tool name to execute
    description: Optional[str]        # Human-readable description
    args: Optional[Dict[str, Any]]    # Tool arguments (supports $references)
    run_if: Optional[str]             # Conditional execution expression
    key_finding: Optional[bool]       # Mark as critical finding
    intervention_if: Optional[str]    # Trigger INTERVENTION_NEEDED if true

class Plan(BaseModel):
    id: Optional[str]
    name: Optional[str]
    steps: List[Step]
```

---

## Event Flow

```
execute_plan(plan, tools)
    │
    ├─► yield Event(type=START, plan_id="...")
    │
    ├─► For each step:
    │       │
    │       ├─► yield Event(type=STEP_START, step_id="s1", tool="scan_hull")
    │       │
    │       ├─► [Check run_if condition]
    │       │       └─► If false: yield Event(type=STEP_SKIPPED)
    │       │
    │       ├─► [Execute tool via Marimo cell]
    │       │
    │       ├─► [Check intervention_if condition]
    │       │       └─► If true: yield Event(type=INTERVENTION_NEEDED)
    │       │
    │       └─► yield Event(type=STEP_COMPLETE, output={...})
    │
    └─► yield Event(type=FINISH, verdict=SUCCESS, outputs={...})
```

---

## Usage Examples

### Basic Usage (Sync)

```python
from marimo_engine import execute_plan_sync
from marimo_engine.tools import get_example_tools

plan = {
    "steps": [
        {"id": "s1", "tool": "scan_hull"},
        {"id": "s2", "tool": "check_oxygen", "key_finding": True},
        {"id": "s3", "tool": "analyze_atmosphere", "args": {"o2_level": "$s2.level"}}
    ]
}

result = execute_plan_sync(plan, tools=get_example_tools())
print(result.verdict)  # SUCCESS
print(result.outputs)  # {"s1": {...}, "s2": {...}, "s3": {...}}
```

### Streaming Usage (Async)

```python
from marimo_engine import execute_plan
from marimo_engine.tools import get_example_tools

async def run():
    plan = {"steps": [...]}
    
    async for event in execute_plan(plan, tools=get_example_tools()):
        if event.type == "STEP_START":
            print(f"Starting: {event.step_id}")
        elif event.type == "STEP_COMPLETE":
            print(f"Completed: {event.step_id} → {event.output}")
        elif event.type == "FINISH":
            print(f"Done! Verdict: {event.verdict}")
```

### Pipecat Integration

```python
from pipecat.frames import Frame
from marimo_engine import execute_plan

async def diagnostic_tool(plan_json: str) -> AsyncIterator[Frame]:
    """
    Pipecat tool that executes a diagnostic plan.
    """
    plan = json.loads(plan_json)
    
    async for event in execute_plan(plan, tools=registered_tools):
        # Convert events to Pipecat frames
        yield TextFrame(f"[{event.type}] {event.msg}")
    
    # Final result
    yield TextFrame(f"Verdict: {event.verdict}")
```

---

## Verdicts

| Verdict | When | Action |
|---------|------|--------|
| `SUCCESS` | All steps completed without issues | Continue |
| `FAILURE` | An error occurred (exception, missing tool) | Stop, report error |
| `INTERVENTION_NEEDED` | Step result triggers intervention condition | Pause for human review |

### Intervention Triggers

```python
# In plan step:
{
    "id": "s2",
    "tool": "check_oxygen",
    "intervention_if": "$s2.level < 15"  # Trigger if oxygen critical
}

# Or based on tool result:
{
    "id": "s3",
    "tool": "analyze_atmosphere",
    "intervention_if": "$s3.severity == 'HIGH'"
}
```

---

## Expression Evaluation

The `run_if` and `intervention_if` fields support safe expressions:

```python
# Simple reference (truthy check)
"run_if": "$s1.breach_detected"

# Comparison
"run_if": "$s2.level < 15"

# Equality
"run_if": "$s3.status == 'CRITICAL'"

# Boolean operators
"run_if": "$s1.value > 10 and $s2.status == 'OK'"
```

**Safety**: Only comparisons and boolean operators allowed. No function calls, imports, or file access.

---

## Future Enhancements

1. **Markdown as Tools** - Execute markdown cells with embedded Python
2. **Parallel Execution** - Run independent steps concurrently
3. **Loops** - Iterate over items from previous step
4. **Branching** - If/else paths based on conditions
5. **Sub-plans** - Nested plan execution
6. **Retry Logic** - Automatic retry on transient failures
