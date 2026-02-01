# toolCallAgent - Diagnostic Voice Agent

A Pipecat AI voice agent with **tool calling** and **tool chaining** capabilities, integrated with the **marimo_engine** for executing diagnostic sequences.

## Features

- **ChatGPT-Style UI**: Full conversation history with text input support
- **Traditional Pipeline**: STT → LLM → TTS (reliable, supports cheaper models)
- **Dual Input**: Type or speak - both work seamlessly
- **Tool Call Visualization**: See tool calls, arguments, and results in the chat
- **Cost-Effective**: Supports cheaper models like `gpt-4o-mini` and `gpt-3.5-turbo`
- **Tool Calling**: Individual diagnostic tools available to the agent
- **Tool Chaining**: Create and execute sequences of tools with data passing
- **Saved Skills**: Pre-defined tool chains with usage guidance
- **Runtime Chain Creation**: Agent can create custom tool chains on-the-fly
- **Real-time Streaming**: Stream responses to web frontend via WebRTC
- **Observability**: Built-in Whisker + Tail debugging tools
- **Weave Tracing**: Full observability with Weights & Biases Weave for tracking threads, LLM calls, and tool executions

## Core Concepts

### Individual Tools
Single-purpose diagnostic functions that return immediate results. Each tool takes 3-6 seconds (simulated sensor delays).

### Tool Chains
Sequences of tools executed in order. Features:
- **Data passing**: Output from one step feeds into the next (`$step_id.field`)
- **Conditional execution**: Steps can be skipped based on conditions
- **Key findings**: Important results are highlighted
- **Intervention triggers**: Automatic alerts for critical conditions

### Skills (Saved Tool Chains)
Pre-defined tool chains with rich metadata:
- When to use the skill
- Expected outcomes
- Debug tips if something fails
- Fallback tools to try individually

## Available Tools

### Individual Diagnostic Tools

| Tool | Description | Delay |
|------|-------------|-------|
| `scan_hull` | Scan hull for structural integrity and breaches | 3-6s |
| `check_oxygen` | Check atmospheric oxygen levels | 3-6s |
| `analyze_atmosphere` | Analyze atmosphere based on oxygen level | 3-6s |
| `check_temperature` | Check temperature in a zone (main, engine, cargo) | 3-6s |
| `scan_systems` | Comprehensive scan of all systems | 3-6s |

### Skill & Tool Chain Management

| Tool | Description |
|------|-------------|
| `list_skills` | List all saved skills with usage guidance |
| `get_skill_details` | Get detailed info about a specific skill |
| `execute_skill` | Execute a saved skill by ID |
| `create_and_run_tool_chain` | Create a custom tool chain at runtime |
| `save_tool_chain_as_skill` | Save a tool chain as a reusable skill |
| `delete_saved_skill` | Delete a dynamically saved skill |

### Available Skills (Saved Tool Chains)

| Skill ID | Name | Description |
|----------|------|-------------|
| `diagnostic_sequence` | System Diagnostic Sequence | Standard health check (hull → oxygen → atmosphere) |
| `conditional_plan` | Safe Engine Check | Check engine only if hull is intact |
| `intervention_plan` | Critical Oxygen Alert | Demonstrates intervention triggers |
| `async_plan` | Quick Systems Overview | Fast overview using async tools |
| `complex_plan` | Full System Diagnostic | Comprehensive check with report generation |

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
   
   Weave Tracing (optional but recommended):
   - `WANDB_API_KEY` - Your Weights & Biases API key (get from https://wandb.ai/authorize)
   - `WEAVE_PROJECT_NAME` - Project name for traces (default: toolCallAgent)
   - `WEAVE_DISABLED` - Set to "true" to disable tracing
   - `WEAVE_THREAD_ID` - Optional explicit thread ID for grouping (default: auto-generated per run)

4. **Run the bot**:

   - SmallWebRTC: `uv run bot.py`
   - Daily: `uv run bot.py --transport daily`

5. **Skills API (auto-started with the bot)**:

   The Skills API now starts automatically when you run `uv run bot.py`.
   It runs on `http://localhost:7861` by default.

   Optional overrides in `.env`:
   - `SKILLS_API_ENABLED` (true/false)
   - `SKILLS_API_HOST` (default: 0.0.0.0)
   - `SKILLS_API_PORT` (default: 7861)

   You can still run it manually if desired:
   ```powershell
   uvicorn skills_api:app --host 0.0.0.0 --port 7861
   ```

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

### Using a Saved Skill

**User**: "Run a full diagnostic"

**Agent**: *Calls `execute_skill` with `complex_plan`*

"I'm running the Full System Diagnostic skill. Here's what I found:
- Hull integrity: 98% - OK
- Oxygen: 14.5% - CRITICAL
- Temperature: Normal across all zones
- Systems: Life support is DEGRADED

Overall verdict: INTERVENTION_NEEDED due to critical oxygen levels."

### Creating a Custom Tool Chain

**User**: "Check oxygen and then analyze the atmosphere"

**Agent**: *Calls `create_and_run_tool_chain`*

```json
{
  "name": "Oxygen Analysis Chain",
  "steps": [
    {"id": "s1", "tool": "check_oxygen"},
    {"id": "s2", "tool": "analyze_atmosphere", "args": {"o2_level": "$s1.level"}}
  ]
}
```

"I've created and run a custom tool chain. The oxygen level is 14.5% (CRITICAL_LOW), and the atmosphere analysis recommends EVACUATE due to the low oxygen."

### Saving a Tool Chain as a Skill

**User**: "That was useful, save it as a skill"

**Agent**: *Calls `save_tool_chain_as_skill`*

```json
{
  "skill_id": "oxygen_analysis",
  "name": "Oxygen Analysis Chain",
  "description": "Check oxygen levels and analyze atmosphere",
  "steps": [
    {"id": "s1", "tool": "check_oxygen"},
    {"id": "s2", "tool": "analyze_atmosphere", "args": {"o2_level": "$s1.level"}}
  ],
  "when_to_use": "Use when you need to check oxygen and get atmosphere recommendations",
  "keywords": ["oxygen", "atmosphere", "analysis"]
}
```

"I've saved the tool chain as a skill called 'Oxygen Analysis Chain'. You can now run it anytime using `execute_skill` with ID 'oxygen_analysis'."

### Debugging a Failed Chain

**User**: "The diagnostic failed, what happened?"

**Agent**: *Calls `get_skill_details` for the skill, then runs individual tools*

"Let me check the skill details... The debug tips suggest running `check_oxygen` individually first. Let me try that... The tool works fine. The issue was that the previous step didn't complete. Let me re-run the skill."

### Conversational

**User**: "Is everything okay?"

**Agent**: *Calls `scan_systems` tool*

"Let me do a quick systems check... I'm seeing some concerns. Power and navigation are nominal, but life support is showing as DEGRADED. I'd recommend checking the oxygen levels specifically."

## Web Interface Pages

The client application includes several pages:

| Page | URL | Description |
|------|-----|-------------|
| **Chat** | `/` | Main voice/text chat interface with spaceship visualization |
| **Skills** | `/skills` | Browse and view details of all available skills |
| **Evals** | `/evals` | Evaluation and testing interface |

### Skills Page

The Skills page (`/skills`) provides a visual interface to:
- Browse all available skills (built-in and custom)
- View detailed information about each skill
- See execution steps, conditions, and intervention triggers
- View usage guidance and debug tips
- Identify trigger keywords for each skill

**Note**: The Skills page requires the Skills API to be running (see below).

## Project Structure

```
toolCallAgent/
├── server/                 # Python bot server
│   ├── bot.py              # Main bot with tool calling
│   ├── tools.py            # Tool definitions and handlers
│   ├── skills_api.py       # FastAPI server for Skills page
│   ├── weave_tracing.py    # Weave tracing integration
│   ├── pyproject.toml      # Python dependencies
│   ├── env.example         # Environment variables template
│   └── .env                # Your API keys (git-ignored)
├── client/                 # React application
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           # Main chat page
│   │   │   ├── skills/page.tsx    # Skills browser page
│   │   │   ├── evals/page.tsx     # Evals page
│   │   │   ├── api/skills/        # Skills API routes
│   │   │   └── components/        # React components
│   │   └── config.ts
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

### Weave Tracing (Weights & Biases)

**Weave** provides comprehensive tracing for LLM applications, tracking:
- **Threads**: Each conversation session is tracked as a thread
- **Turns**: User messages, assistant responses, and tool calls within each turn
- **Tool Executions**: All tool calls with inputs, outputs, duration, and success/failure status
- **LLM Calls**: Automatically traced via the `@weave.op()` decorator

**To use Weave:**

1. Get your W&B API key from [https://wandb.ai/authorize](https://wandb.ai/authorize)

2. Add to your `.env` file:
   ```
   WANDB_API_KEY=your_api_key_here
   WEAVE_PROJECT_NAME=toolCallAgent
   ```

3. Run your bot - traces will automatically appear in your W&B dashboard

4. View traces at [https://wandb.ai](https://wandb.ai) → Your Project → Weave

**What gets traced:**
- Each conversation session as a thread
- User messages (voice transcriptions)
- Assistant responses
- Tool calls with arguments and results
- Execution timing for all operations
 - Thread context is created per participant/session (or `WEAVE_THREAD_ID` if set)

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

## Tool Chain Reference Syntax

When creating tool chains, you can reference outputs from previous steps:

| Syntax | Description | Example |
|--------|-------------|---------|
| `$step_id` | Entire output of a step | `$s1` |
| `$step_id.field` | Specific field | `$s1.level` |
| `$step_id.nested.field` | Nested field | `$s1.data.value` |

### Example Tool Chain

```json
{
  "name": "Custom Safety Check",
  "steps": [
    {"id": "s1", "tool": "check_oxygen"},
    {"id": "s2", "tool": "check_temperature", "args": {"zone": "main"}},
    {"id": "s3", "tool": "analyze_atmosphere", "args": {"o2_level": "$s1.level"}},
    {"id": "s4", "tool": "scan_hull", "run_if": "$s3.severity == 'HIGH'"}
  ]
}
```

## Extending the Agent

### Adding New Tools

1. Add the tool implementation to `marimo_engine/tools/examples.py`:

```python
def my_new_tool(param1: str) -> Dict[str, Any]:
    delay = simulate_work("my_operation")
    return {
        "result": "...",
        "execution_delay_ms": int(delay * 1000)
    }
```

2. Register in `get_example_tools()`:

```python
return {
    # ... existing tools
    "my_new_tool": my_new_tool,
}
```

3. Add the tool definition to `TOOL_DEFINITIONS` in `tools.py`:

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

4. Add the handler function in `tools.py`:

```python
async def handle_my_new_tool(param1: str) -> str:
    result = _marimo_tools["my_new_tool"](param1)
    return json.dumps({
        "tool": "my_new_tool",
        "status": "success",
        "result": result
    }, indent=2)
```

5. Register in `TOOL_HANDLERS` and `bot.py`.

### Adding New Skills (Saved Tool Chains)

Add to `marimo_engine/plans/examples.py`:

```python
def get_my_skill() -> Dict[str, Any]:
    return {
        "id": "my_skill",
        "name": "My Custom Skill",
        "description": "What this skill does",
        "when_to_use": "Use when...",
        "expected_outcome": "After running...",
        "debug_tips": ["If X fails, try Y"],
        "fallback_tools": ["tool1", "tool2"],
        "steps": [
            {"id": "s1", "tool": "tool1"},
            {"id": "s2", "tool": "tool2", "args": {"param": "$s1.value"}}
        ]
    }
```

### Configuring Tool Delays

In `marimo_engine/tools/examples.py`:

```python
from marimo_engine.tools.examples import set_delay_config, disable_delays

# Set custom delays (default: 3-6 seconds)
set_delay_config(min_delay=1.0, max_delay=3.0, enabled=True)

# Disable for testing
disable_delays()
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
