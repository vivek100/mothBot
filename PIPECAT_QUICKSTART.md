# Pipecat Agent Quick Start Guide

## Overview

This guide will help you create a Pipecat agent that can:
- Call individual tools (scan_hull, check_oxygen, etc.)
- Execute full diagnostic plans
- Stream responses to a web frontend

## Step 1: Install Prerequisites

```powershell
# Install Pipecat CLI
pip install pipecat-ai-cli

# Or using uv (recommended)
uv tool install pipecat-ai-cli

# Verify installation
pipecat --version
```

## Step 2: Initialize Pipecat Project

```powershell
cd toolChainEngine/marimo_engine
pipecat init
```

**Interactive prompts:**
- **Bot type**: Choose "Text-only" (no voice for now)
- **Transport**: Choose "WebSocket" (for web frontend)
- **LLM**: Choose "OpenAI"
- **STT/TTS**: Skip (not needed for text-only)
- **Deployment**: Choose "Local" for now

This will create:
```
agent/
├── bot.py
├── bot_runner.py
├── pyproject.toml
└── .env.example

client/
├── index.html
└── app.js
```

## Step 3: Set Up Environment

```powershell
# Copy environment template
cp agent/.env.example agent/.env

# Edit agent/.env and add:
OPENAI_API_KEY=your_openai_api_key_here
```

## Step 4: Create Tool Integration

Create `agent/tools.py`:

```python
"""Tool wrappers for Pipecat agent."""

import json
from typing import Dict, Any
from marimo_engine import execute_plan
from marimo_engine.tools import get_example_tools

# Get all available tools
_marimo_tools = get_example_tools()


async def scan_hull_tool() -> str:
    """Scan the hull for integrity and breaches."""
    result = _marimo_tools["scan_hull"]()
    return json.dumps(result, indent=2)


async def check_oxygen_tool() -> str:
    """Check oxygen levels in the atmosphere."""
    result = _marimo_tools["check_oxygen"]()
    return json.dumps(result, indent=2)


async def analyze_atmosphere_tool(o2_level: float) -> str:
    """Analyze atmosphere based on oxygen level."""
    result = _marimo_tools["analyze_atmosphere"](o2_level)
    return json.dumps(result, indent=2)


async def check_temperature_tool(zone: str = "main") -> str:
    """Check temperature in a specific zone."""
    result = _marimo_tools["check_temperature"](zone)
    return json.dumps(result, indent=2)


async def execute_plan_tool(plan_json: str) -> str:
    """
    Execute a multi-step diagnostic plan.
    
    Args:
        plan_json: JSON string of the plan to execute
        
    Returns:
        Formatted execution results
    """
    plan = json.loads(plan_json)
    tools = get_example_tools()
    
    results = []
    async for event in execute_plan(plan, tools):
        results.append(f"[{event.type.value}] {event.msg}")
        if event.type.value == "FINISH":
            results.append(f"\nVerdict: {event.verdict.value}")
            if event.final_context:
                results.append(f"\nOutputs:\n{json.dumps(event.final_context, indent=2)}")
    
    return "\n".join(results)


# Tool definitions for OpenAI function calling
def get_tool_definitions() -> list:
    """Return OpenAI function calling tool definitions."""
    return [
        {
            "type": "function",
            "function": {
                "name": "scan_hull",
                "description": "Scan the hull for integrity and breaches. Returns integrity percentage and breach status.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_oxygen",
                "description": "Check oxygen levels in the atmosphere. Returns level, status, and threshold information.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_atmosphere",
                "description": "Analyze atmosphere based on oxygen level. Returns recommendation and severity.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "o2_level": {
                            "type": "number",
                            "description": "Oxygen level percentage"
                        }
                    },
                    "required": ["o2_level"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_temperature",
                "description": "Check temperature in a specific zone (main, engine, or cargo).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "zone": {
                            "type": "string",
                            "description": "Zone to check: main, engine, or cargo",
                            "enum": ["main", "engine", "cargo"]
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_plan",
                "description": "Execute a multi-step diagnostic plan. The plan should be a JSON string with 'steps' array. Each step has 'id', 'tool', optional 'args', 'run_if', and 'intervention_if' fields.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "plan_json": {
                            "type": "string",
                            "description": "JSON string of the plan to execute. Example: {\"steps\": [{\"id\": \"s1\", \"tool\": \"scan_hull\"}, {\"id\": \"s2\", \"tool\": \"check_oxygen\"}]}"
                        }
                    },
                    "required": ["plan_json"]
                }
            }
        }
    ]


# Tool handler mapping
TOOL_HANDLERS = {
    "scan_hull": scan_hull_tool,
    "check_oxygen": check_oxygen_tool,
    "analyze_atmosphere": analyze_atmosphere_tool,
    "check_temperature": check_temperature_tool,
    "execute_plan": execute_plan_tool,
}
```

## Step 5: Update Bot Implementation

Edit `agent/bot.py` to integrate tools:

```python
import os
from pipecat.processors.aggregators.openai_function_aggregator import OpenAIFunctionAggregator
from pipecat.services.openai import OpenAILLMService
from pipecat.pipelines.pipeline import Pipeline
from pipecat.transports.websocket import WebSocketTransport
from pipecat.frames.frames import TextFrame, ToolCallFrame, ToolCallResultFrame

from .tools import get_tool_definitions, TOOL_HANDLERS


class DiagnosticAgent:
    def __init__(self):
        self.llm = OpenAILLMService(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o",
            tools=get_tool_definitions()
        )
        
        self.function_aggregator = OpenAIFunctionAggregator()
        
    async def process_tool_call(self, tool_call):
        """Handle tool calls from the LLM."""
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
        
        # Route to appropriate tool handler
        if name in TOOL_HANDLERS:
            handler = TOOL_HANDLERS[name]
            try:
                result = await handler(**args)
            except Exception as e:
                result = f"Error executing {name}: {str(e)}"
        else:
            result = f"Unknown tool: {name}"
        
        return ToolCallResultFrame(
            id=tool_call.id,
            name=name,
            result=result
        )
    
    def create_pipeline(self, transport: WebSocketTransport):
        """Create the processing pipeline."""
        return Pipeline([
            transport.input(),
            self.llm,
            self.function_aggregator,
            transport.output()
        ])
```

## Step 6: Update Bot Runner

Edit `agent/bot_runner.py`:

```python
import os
from pipecat.transports.websocket import WebSocketTransport
from pipecat.pipelines.pipeline import Pipeline
from pipecat.server.rest import RESTfulServer
from dotenv import load_dotenv

from .bot import DiagnosticAgent

# Load environment variables
load_dotenv()


class DiagnosticBotRunner(RESTfulServer):
    def __init__(self):
        super().__init__()
        self.agent = DiagnosticAgent()
    
    async def create_pipeline(self, transport: WebSocketTransport):
        """Create pipeline for each session."""
        return self.agent.create_pipeline(transport)


if __name__ == "__main__":
    runner = DiagnosticBotRunner()
    runner.run(port=8765)
```

## Step 7: Install Dependencies

```powershell
cd agent
pip install -r pyproject.toml
# Or if pyproject.toml doesn't have install section:
pip install pipecat-ai openai python-dotenv
```

## Step 8: Run the Agent

```powershell
# Terminal 1: Start the agent
cd toolChainEngine/marimo_engine/agent
python bot_runner.py

# Terminal 2: Serve the frontend (if needed)
cd toolChainEngine/marimo_engine/client
python -m http.server 8080
```

## Step 9: Test the Agent

Open `client/index.html` in a browser (or navigate to `http://localhost:8080`).

**Test scenarios:**

1. **Individual tool**:**
   - User: "Scan the hull"
   - Agent should call `scan_hull_tool()` and return results

2. **Multiple tools:**
   - User: "Check oxygen levels and scan the hull"
   - Agent should call both tools

3. **Plan execution:**
   - User: "Run a full diagnostic plan"
   - Agent should call `execute_plan_tool()` with a plan

4. **Conversational:**
   - User: "I need to check system health"
   - Agent should decide to use appropriate tools or plans

## Troubleshooting

### Issue: "Module not found: marimo_engine"
**Solution**: Make sure you're running from the correct directory and Python can find the module:
```powershell
# From marimo_engine directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# Or in PowerShell:
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
```

### Issue: "OpenAI API key not found"
**Solution**: Check your `.env` file in the `agent/` directory:
```powershell
# Verify .env exists and has the key
cat agent/.env
```

### Issue: WebSocket connection fails
**Solution**: 
- Check that `bot_runner.py` is running on port 8765
- Verify the WebSocket URL in `client/index.html` matches
- Check browser console for errors

## Next Steps

1. **Enhance UI**: Add better visualization for plan execution events
2. **Add more tools**: Extend with additional diagnostic tools
3. **Error handling**: Improve error messages and recovery
4. **Streaming**: Enhance real-time event streaming from plan execution
5. **Plan templates**: Pre-define common plans for the agent to use

## Resources

- [Pipecat Documentation](https://docs.pipecat.ai)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Marimo Engine README](../README.md)
