# toolCallAgent - Diagnostic Voice Agent

A Pipecat AI voice agent with **tool calling** capabilities, integrated with the **marimo_engine** for executing diagnostic plans.

## Features

- **ChatGPT-Style UI**: Full conversation history with text input support
- **Traditional Pipeline**: STT → LLM → TTS (reliable, supports cheaper models)
- **Dual Input**: Type or speak - both work seamlessly
- **Tool Call Visualization**: See tool calls, arguments, and results in the chat
- **Cost-Effective**: Supports cheaper models like `gpt-4o-mini` and `gpt-3.5-turbo`
- **Tool Calling**: 7 diagnostic tools available to the agent
- **Plan Execution**: Execute multi-step diagnostic plans with dependencies
- **Real-time Streaming**: Stream responses to web frontend via WebRTC
- **Observability**: Built-in Whisker + Tail debugging tools

## Available Tools

### Individual Diagnostic Tools

| Tool | Description |
|------|-------------|
| `scan_hull` | Scan hull for structural integrity and breaches |
| `check_oxygen` | Check atmospheric oxygen levels |
| `analyze_atmosphere` | Analyze atmosphere based on oxygen level |
| `check_temperature` | Check temperature in a zone (main, engine, cargo) |
| `scan_systems` | Comprehensive scan of all systems |

### Plan Execution Tools

| Tool | Description |
|------|-------------|
| `execute_diagnostic_plan` | Execute a multi-step diagnostic plan |
| `list_available_plans` | List all available predefined plans |

### Available Plans

| Plan ID | Description |
|---------|-------------|
| `diagnostic_sequence` | Standard diagnostic sequence for system health check |
| `conditional_plan` | Plan with conditional step execution |
| `intervention_plan` | Plan that triggers human intervention |
| `async_plan` | Plan using async tools |
| `complex_plan` | Full system diagnostic with report |

## Configuration

- **Bot Type**: Web (Voice)
- **Transport(s)**: SmallWebRTC, Daily (WebRTC)
- **Pipeline**: Traditional (STT → LLM → TTS)
  - **STT**: Google Speech-to-Text
  - **LLM**: OpenAI (supports gpt-4o-mini, gpt-3.5-turbo, gpt-4o) with function calling
  - **TTS**: Google Text-to-Speech
- **Features**:
  - Speech-to-Speech (native audio processing)
  - Tool calling / Function calling
  - Multiple voice options (alloy, echo, fable, onyx, nova, shimmer)
  - Observability (Whisker + Tail)

## Setup

### Server

1. **Navigate to server directory**:

   ```powershell
   cd server
   ```

2. **Install dependencies**:

   ```powershell
   uv sync
   ```

3. **Configure environment variables**:

   ```powershell
   cp env.example .env
   # Edit .env and add your API keys
   ```

   Required API keys:
   - `OPENAI_API_KEY` - OpenAI API key
   - `GOOGLE_APPLICATION_CREDENTIALS` - Path to Google Cloud credentials JSON
   - `GOOGLE_LOCATION` - Google Cloud region (e.g., us-central1)
   
   Optional configuration:
   - `OPENAI_MODEL` - Model to use (default: gpt-4o-mini for cost savings)
     - Options: `gpt-4o-mini` (recommended), `gpt-3.5-turbo` (cheapest), `gpt-4o` (best quality)
   - `GOOGLE_VOICE_NAME` - Google TTS voice (default: en-US-Neural2-D)
   - `GOOGLE_LANGUAGE_CODE` - Language code (default: en-US)

4. **Run the bot**:

   - SmallWebRTC: `uv run bot.py`
   - Daily: `uv run bot.py --transport daily`

### Client

1. **Navigate to client directory**:

   ```powershell
   cd client
   ```

2. **Install dependencies**:

   ```powershell
   npm install
   ```

3. **Configure environment variables**:

   ```powershell
   cp env.example .env.local
   # Edit .env.local if needed (defaults to localhost:7860)
   ```

4. **Run development server**:

   ```powershell
   npm run dev
   ```

5. **Open browser**:

   http://localhost:3000

## Example Conversations

### Individual Tool Usage

**User**: "Check the oxygen levels"

**Agent**: *Calls `check_oxygen` tool*

"I've checked the oxygen levels. Current reading is 14.5%, which is CRITICAL_LOW. The safe threshold is 18%. I recommend immediate attention to the life support systems."

### Plan Execution

**User**: "Run a full diagnostic"

**Agent**: *Calls `execute_diagnostic_plan` with `complex_plan`*

"I'm running a comprehensive diagnostic. Here's what I found:
- Hull integrity: 98% - OK
- Oxygen: 14.5% - CRITICAL
- Temperature: Normal across all zones
- Systems: Life support is DEGRADED

Overall verdict: INTERVENTION_NEEDED due to critical oxygen levels."

### Conversational

**User**: "Is everything okay?"

**Agent**: *Calls `scan_systems` tool*

"Let me do a quick systems check... I'm seeing some concerns. Power and navigation are nominal, but life support is showing as DEGRADED. I'd recommend checking the oxygen levels specifically."

## Project Structure

```
toolCallAgent/
├── server/                 # Python bot server
│   ├── bot.py              # Main bot with tool calling
│   ├── tools.py            # Tool definitions and handlers
│   ├── pyproject.toml      # Python dependencies
│   ├── env.example         # Environment variables template
│   └── .env                # Your API keys (git-ignored)
├── client/                 # React application
│   ├── src/                # Client source code
│   ├── package.json        # Node dependencies
│   └── ...
├── .gitignore              # Git ignore patterns
└── README.md               # This file
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Frontend (React)                      │
│  - Real-time voice interface                                 │
│  - WebRTC connection                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ WebRTC
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Pipecat Pipeline                          │
│                                                              │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │
│  │  STT    │ → │   LLM   │ → │   TTS   │ → │Transport│     │
│  │ Google  │   │ OpenAI  │   │ Google  │   │ WebRTC  │     │
│  └─────────┘   └────┬────┘   └─────────┘   └─────────┘     │
│                     │                                        │
│                     ▼ Tool Calls                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Tool Handlers (tools.py)                 │   │
│  │  - scan_hull, check_oxygen, analyze_atmosphere        │   │
│  │  - check_temperature, scan_systems                    │   │
│  │  - execute_diagnostic_plan, list_available_plans      │   │
│  └──────────────────────────┬───────────────────────────┘   │
│                              │                               │
│                              ▼                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              marimo_engine Integration                │   │
│  │  - execute_plan() for multi-step diagnostics          │   │
│  │  - Streaming events                                   │   │
│  │  - Conditional execution, intervention support        │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## Observability

### Whisker - Live Pipeline Debugger

**Whisker** is a live graphical debugger that lets you visualize pipelines and debug frames in real time.

**To use Whisker:**

1. Run an ngrok tunnel to expose your bot:

   ```powershell
   ngrok http 9090
   ```

2. Navigate to [https://whisker.pipecat.ai/](https://whisker.pipecat.ai/) and enter your ngrok URL

3. Once your bot is running, press connect

### Tail - Terminal Dashboard

**Tail** is a terminal dashboard that lets you monitor your Pipecat sessions in real time.

**To use Tail:**

1. Run your bot (in one terminal)

2. Launch Tail in another terminal:
   ```powershell
   pipecat tail
   ```

## Extending the Agent

### Adding New Tools

1. Add the tool definition to `TOOL_DEFINITIONS` in `tools.py`:

```python
{
    "type": "function",
    "function": {
        "name": "my_new_tool",
        "description": "Description of what the tool does",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "..."}
            },
            "required": ["param1"]
        }
    }
}
```

2. Add the handler function:

```python
async def handle_my_new_tool(param1: str) -> str:
    # Your tool logic here
    return json.dumps({"result": "..."})
```

3. Register in `TOOL_HANDLERS`:

```python
TOOL_HANDLERS = {
    # ... existing tools
    "my_new_tool": handle_my_new_tool,
}
```

4. Register with the LLM in `bot.py`:

```python
llm.register_function("my_new_tool", handle_tool_call)
```

### Modifying the System Prompt

Edit `SYSTEM_PROMPT` in `tools.py` to change the agent's behavior, personality, or instructions.

## Learn More

- [Pipecat Documentation](https://docs.pipecat.ai/)
- [Voice UI Kit Documentation](https://voiceuikit.pipecat.ai/)
- [Pipecat GitHub](https://github.com/pipecat-ai/pipecat)
- [Pipecat Examples](https://github.com/pipecat-ai/pipecat-examples)
- [Discord Community](https://discord.gg/pipecat)
- [marimo_engine Documentation](../README.md)
