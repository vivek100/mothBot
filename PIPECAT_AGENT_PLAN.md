# Pipecat Agent Implementation Plan

## Overview

Create a Pipecat-powered agent that can:
1. **Call individual tools** (scan_hull, check_oxygen, analyze_atmosphere, etc.)
2. **Execute full plans** using the `execute_plan` tool
3. **Stream responses** to a web frontend in real-time

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Frontend (HTML/JS)                    │
│  - Real-time chat interface                                  │
│  - Displays streaming agent responses                        │
│  - Shows tool execution status                               │
└──────────────────────────┬──────────────────────────────────┘
                           │ WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Pipecat Bot Runner (HTTP Server)                │
│  - Handles WebSocket connections                             │
│  - Spawns bot instances per session                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Pipecat Agent (bot.py)                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  LLM (OpenAI) with Function Calling                 │   │
│  │  - Individual tools: scan_hull, check_oxygen, etc.  │   │
│  │  - Plan execution: execute_plan                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Tool Handlers                                       │   │
│  │  - Individual tool wrappers                          │   │
│  │  - execute_plan wrapper (main tool)                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Marimo Engine Integration                            │   │
│  │  - execute_plan() → streams events                    │   │
│  │  - Individual tools from registry                     │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Phase 1: Setup Pipecat Project Structure

1. **Install Pipecat CLI**
   ```powershell
   pip install pipecat-ai-cli
   # Or using uv
   uv tool install pipecat-ai-cli
   ```

2. **Initialize Pipecat Project**
   ```powershell
   cd toolChainEngine/marimo_engine
   pipecat init
   ```
   - Select: **Text-only bot** (no voice for now)
   - Transport: **WebSocket** (for web frontend)
   - LLM: **OpenAI**
   - Skip STT/TTS for now (text-only)

3. **Generated Structure**
   ```
   marimo_engine/
   ├── agent/                    # New folder for Pipecat agent
   │   ├── bot.py                # Main bot implementation
   │   ├── bot_runner.py         # HTTP server
   │   ├── tools.py              # Tool definitions for Pipecat
   │   └── pyproject.toml        # Dependencies
   ├── client/                      # Frontend (if generated)
   │   ├── index.html
   │   └── app.js
   └── .env                       # API keys
   ```

### Phase 2: Create Tool Wrappers

**File: `agent/tools.py`**

Create Pipecat-compatible tool wrappers:

1. **Individual Tool Wrapper**
   ```python
   from pipecat.frames.frames import ToolCallFrame, ToolCallResultFrame
   from marimo_engine.tools import get_example_tools
   from marimo_engine import execute_plan
   
   # Individual tools
   async def scan_hull_tool() -> str:
       """Scan hull for integrity and breaches."""
       tools = get_example_tools()
       result = tools["scan_hull"]()
       return f"Hull scan complete: {result}"
   
   async def check_oxygen_tool() -> str:
       """Check oxygen levels in atmosphere."""
       tools = get_example_tools()
       result = tools["check_oxygen"]()
       return f"Oxygen level: {result['level']}% ({result['status']})"
   
   # ... more individual tools
   ```

2. **Main Plan Execution Tool**
   ```python
   async def execute_plan_tool(plan_json: str) -> str:
       """
       Execute a diagnostic plan with multiple steps.
       
       Args:
           plan_json: JSON string of the plan to execute
       """
       import json
       from marimo_engine import execute_plan
       from marimo_engine.tools import get_example_tools
       
       plan = json.loads(plan_json)
       tools = get_example_tools()
       
       results = []
       async for event in execute_plan(plan, tools):
           results.append(f"[{event.type.value}] {event.msg}")
       
       return "\n".join(results)
   ```

3. **Tool Registry for Pipecat**
   ```python
   from pipecat.processors.aggregators.openai_function_aggregator import OpenAIFunctionAggregator
   
   def get_tools_for_agent():
       """Return tools configured for OpenAI function calling."""
       return [
           {
               "type": "function",
               "function": {
                   "name": "scan_hull",
                   "description": "Scan the hull for integrity and breaches",
                   "parameters": {"type": "object", "properties": {}"}
               }
           },
           {
               "type": "function",
               "function": {
                   "name": "check_oxygen",
                   "description": "Check oxygen levels in the atmosphere",
                   "parameters": {"type": "object", "properties": {}}
               }
           },
           {
               "type": "function",
               "function": {
                   "name": "execute_plan",
                   "description": "Execute a multi-step diagnostic plan",
                   "parameters": {
                       "type": "object",
                       "properties": {
                           "plan_json": {
                               "type": "string",
                               "description": "JSON string of the plan to execute"
                           }
                       },
                       "required": ["plan_json"]
                   }
               }
           }
       ]
   ```

### Phase 3: Build the Agent

**File: `agent/bot.py`**

```python
import os
from pipecat.processors.aggregators.openai_function_aggregator import OpenAIFunctionAggregator
from pipecat.services.openai import OpenAILLMService
from pipecat.pipelines.pipeline import Pipeline
from pipecat.pipelines.topology import Topology
from pipecat.transports.websocket import WebSocketTransport
from pipecat.frames.frames import TextFrame, ToolCallFrame, ToolCallResultFrame

from .tools import (
    scan_hull_tool,
    check_oxygen_tool,
    analyze_atmosphere_tool,
    execute_plan_tool,
    get_tools_for_agent
)

class DiagnosticAgent:
    def __init__(self):
        self.llm = OpenAILLMService(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o",
            tools=get_tools_for_agent()
        )
        
        self.function_aggregator = OpenAIFunctionAggregator()
        
    async def process_tool_call(self, tool_call):
        """Handle tool calls from the LLM."""
        name = tool_call.function.name
        args = tool_call.function.arguments
        
        # Route to appropriate tool
        if name == "scan_hull":
            result = await scan_hull_tool()
        elif name == "check_oxygen":
            result = await check_oxygen_tool()
        elif name == "analyze_atmosphere":
            result = await analyze_atmosphere_tool(**args)
        elif name == "execute_plan":
            result = await execute_plan_tool(args.get("plan_json", ""))
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

### Phase 4: Create Bot Runner

**File: `agent/bot_runner.py`**

```python
import asyncio
from pipecat.transports.websocket import WebSocketTransport
from pipecat.pipelines.pipeline import Pipeline
from pipecat.server.rest import RESTfulServer
from .bot import DiagnosticAgent

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

### Phase 5: Create Simple Frontend

**File: `client/index.html`**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Marimo Engine Agent</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 0 auto; }
        #messages { border: 1px solid #ccc; height: 400px; overflow-y: auto; padding: 10px; }
        .message { margin: 10px 0; }
        .user { color: blue; }
        .agent { color: green; }
        .tool { color: orange; }
    </style>
</head>
<body>
    <h1>Marimo Engine Diagnostic Agent</h1>
    <div id="messages"></div>
    <input type="text" id="input" placeholder="Ask the agent...">
    <button onclick="sendMessage()">Send</button>
    
    <script>
        const ws = new WebSocket('ws://localhost:8765/ws');
        const messages = document.getElementById('messages');
        const input = document.getElementById('input');
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            addMessage(data.text, 'agent');
        };
        
        function addMessage(text, type) {
            const div = document.createElement('div');
            div.className = `message ${type}`;
            div.textContent = text;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function sendMessage() {
            const text = input.value;
            if (text) {
                addMessage(text, 'user');
                ws.send(JSON.stringify({text: text}));
                input.value = '';
            }
        }
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
```

### Phase 6: Integration & Testing

1. **Update Dependencies**
   ```powershell
   cd agent
   pip install pipecat-ai openai
   ```

2. **Environment Setup**
   ```powershell
   # .env file
   OPENAI_API_KEY=your_key_here
   ```

3. **Run the Agent**
   ```powershell
   python agent/bot_runner.py
   ```

4. **Open Frontend**
   ```powershell
   # Open client/index.html in browser
   # Or serve with: python -m http.server 8080
   ```

## Testing Scenarios

### Test 1: Individual Tool Calls
- User: "Scan the hull"
- Agent calls `scan_hull_tool()`
- Returns hull integrity status

### Test 2: Multiple Tool Calls
- User: "Check oxygen and scan the hull"
- Agent calls both tools
- Returns combined results

### Test 3: Plan Execution
- User: "Run a full diagnostic plan"
- Agent calls `execute_plan_tool()` with a plan JSON
- Streams execution events
- Returns final verdict

### Test 4: Conversational Planning
- User: "I need to check system health"
- Agent decides to use `execute_plan_tool()` with appropriate plan
- Executes and reports results

## File Structure Summary

```
marimo_engine/
├── agent/                          # Pipecat agent implementation
│   ├── __init__.py
│   ├── bot.py                      # Main agent class
│   ├── bot_runner.py               # HTTP/WebSocket server
│   ├── tools.py                    # Tool wrappers for Pipecat
│   └── pyproject.toml              # Agent dependencies
├── client/                         # Frontend
│   ├── index.html                  # Simple chat UI
│   └── app.js                      # WebSocket client (if needed)
├── core/                           # Existing engine core
├── tools/                          # Existing tools
├── plans/                          # Existing plans
├── .env                            # API keys
└── PIPECAT_AGENT_PLAN.md          # This file
```

## Next Steps

1. **Run `pipecat init`** to generate base structure
2. **Adapt generated code** to use marimo_engine tools
3. **Test individual tools** first
4. **Add plan execution tool**
5. **Test streaming** with frontend
6. **Enhance UI** with better visualization of plan execution

## Resources

- [Pipecat Quickstart](https://docs.pipecat.ai/getting-started/quickstart)
- [Pipecat Function Calling](https://docs.pipecat.ai/guides/function-calling)
- [Pipecat WebSocket Transport](https://docs.pipecat.ai/transports/websocket)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
