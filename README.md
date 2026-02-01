# 🦋 MothBot

**A Self-Learning AI Agent that Evolves Through Tool Chains**

MothBot is an intelligent voice agent that doesn't just call tools—it learns from every interaction. By analyzing conversation threads, MothBot automatically extracts successful tool sequences as reusable "skills" and uses evaluations to continuously improve its prompts and tool designs.

> Built with **Pipecat** for voice AI, **Marimo** for tool chain execution, and **Weave** for tracing & evaluation.

---

## 🎯 The Problem

Traditional AI agents have a fundamental limitation: they forget. Every conversation starts from scratch, and successful tool combinations are lost. Developers must manually:
- Define every possible tool chain upfront
- Update prompts based on guesswork
- Hope their tool descriptions are clear enough

**MothBot solves this** by creating a feedback loop where the agent learns from its own traces.

---

## ✨ Three Key Innovations

### 1. 🔗 Tool Chains (Not Just Tools)

Instead of calling tools one at a time, MothBot executes **intelligent sequences** where data flows between steps.

#### ❌ Traditional Agent - No Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant A as Agent
    participant T1 as check_oxygen
    participant T2 as analyze_atmosphere
    participant T3 as scan_hull

    U->>A: "Check if it's safe"
    
    A->>T1: call()
    T1-->>A: {level: 14.5%}
    
    A->>T2: call()
    Note right of T2: ❌ ERROR!<br/>Missing o2_level param
    T2-->>A: Error: missing required param
    
    A->>T3: call()
    T3-->>A: {integrity: 98%}
    
    A->>U: "Oxygen is 14.5%, hull is 98%"
    Note over A: ⚠️ Missed the atmosphere<br/>analysis entirely!
```

#### ✅ MothBot Tool Chain - Intelligent Data Passing

```mermaid
sequenceDiagram
    participant U as User
    participant A as Agent
    participant E as Marimo Engine
    participant T1 as check_oxygen
    participant T2 as analyze_atmosphere
    participant T3 as scan_hull

    U->>A: "Check if it's safe"
    A->>E: execute_skill("safety_check")
    
    rect rgb(20, 80, 60)
        Note over E: Step s1
        E->>T1: call()
        T1-->>E: {level: 14.5, status: "CRITICAL"}
        E->>E: context[s1] = result
    end
    
    rect rgb(80, 40, 80)
        Note over E: Step s2 - Auto data passing!
        E->>E: resolve $s1.level → 14.5
        E->>T2: call(o2_level=14.5)
        T2-->>E: {severity: "HIGH", action: "EVACUATE"}
        E->>E: context[s2] = result
    end
    
    rect rgb(20, 60, 80)
        Note over E: Step s3 - Conditional!
        E->>E: eval run_if: $s2.severity == "HIGH"
        Note right of E: ✓ Condition TRUE
        E->>T3: call()
        T3-->>E: {integrity: 98%}
        E->>E: eval intervention_if: $s3.integrity < 50
        Note right of E: ✗ No intervention needed
    end
    
    E-->>A: Verdict: SUCCESS<br/>Key findings: O2 critical
    A->>U: "Safety check complete:<br/>⚠️ O2 at 14.5% - EVACUATE<br/>✓ Hull integrity 98%"
```

**Key Features:**
| Feature | Syntax | Example |
|---------|--------|---------|
| **Data Passing** | `$step_id.field` | `$s1.level` → passes oxygen level to next step |
| **Conditional Execution** | `run_if` | `run_if: "$s1.status == 'OK'"` → skip if condition false |
| **Intervention Triggers** | `intervention_if` | `intervention_if: "$s2.severity == 'HIGH'"` → alert human |
| **Key Findings** | `key_finding: true` | Mark critical results for summary |

### 2. 🧠 Skills (Learned Tool Chains)

MothBot saves successful tool chains as **Skills**—not just text descriptions, but executable procedures with rich metadata.

```mermaid
flowchart TB
    subgraph Extraction["Skills Extraction Agent"]
        direction TB
        T1["📜 Conversation Traces"] --> A1["🔍 Pattern Analysis"]
        A1 --> A2["🎯 Identify Repeated Sequences"]
        A2 --> A3["📊 Calculate Confidence"]
        A3 --> SK["💾 Save as Skill"]
    end
    
    subgraph Skill["Saved Skill Structure"]
        direction TB
        SK --> M1["📝 name & description"]
        SK --> M2["🎯 when_to_use"]
        SK --> M3["🔧 steps[]"]
        SK --> M4["🐛 debug_tips"]
        SK --> M5["🏷️ trigger_keywords"]
    end
    
    subgraph Usage["Runtime Usage"]
        direction TB
        U1["👤 User: 'run safety check'"] --> U2["🔍 Match Keywords"]
        U2 --> U3["⚡ Execute Skill"]
        U3 --> U4["📊 Stream Results"]
    end
    
    Skill --> Usage
    
    style Extraction fill:#1a1a2e,stroke:#f59e0b,stroke-width:2px
    style Skill fill:#1a1a2e,stroke:#8b5cf6,stroke-width:2px
    style Usage fill:#1a1a2e,stroke:#10b981,stroke-width:2px
```

**What Makes Skills Different:**
| Traditional Skill | MothBot Skill |
|-------------------|---------------|
| Text description only | Executable tool chain |
| Static | Learned from traces |
| No context | Includes when_to_use, debug_tips |
| Manual creation | Auto-extracted by AI |

### 3. 📈 Dual Evaluation System

MothBot runs **two types of evaluations** on conversation threads:

```mermaid
flowchart TB
    subgraph Input["Conversation Thread"]
        I1["💬 Messages"]
        I2["🔧 Tool Calls"]
        I3["📊 Results"]
    end
    
    subgraph SkillsEval["Skills Extraction Eval"]
        direction TB
        SE1["Analyze tool call patterns"]
        SE2["Identify successful sequences"]
        SE3["Extract as new Skills"]
        SE1 --> SE2 --> SE3
    end
    
    subgraph CodingEval["Coding Agent Eval"]
        direction TB
        CE1["Review tool success rates"]
        CE2["Analyze response times"]
        CE3["Generate improvement suggestions"]
        CE1 --> CE2 --> CE3
    end
    
    Input --> SkillsEval
    Input --> CodingEval
    
    subgraph SkillsOutput["Skills Output"]
        SO1["🆕 New Skills"]
        SO2["📊 Confidence Scores"]
        SO3["🏷️ Suggested Triggers"]
    end
    
    subgraph CodingOutput["Coding Output"]
        CO1["📝 Prompt Updates"]
        CO2["🔧 Tool Description Changes"]
        CO3["⚙️ New Tool Suggestions"]
    end
    
    SkillsEval --> SkillsOutput
    CodingEval --> CodingOutput
    
    style SkillsEval fill:#1a1a2e,stroke:#f59e0b,stroke-width:2px
    style CodingEval fill:#1a1a2e,stroke:#8b5cf6,stroke-width:2px
    style SkillsOutput fill:#0d1117,stroke:#f59e0b,stroke-width:1px
    style CodingOutput fill:#0d1117,stroke:#8b5cf6,stroke-width:1px
```

#### Skills Extraction Eval
Analyzes threads to find **reusable tool sequences**:
- Identifies patterns across multiple conversations
- Calculates confidence scores for each pattern
- Saves high-confidence patterns as new Skills
- Suggests trigger keywords for activation

#### Coding Agent Eval
Analyzes threads to suggest **code improvements**:
- **Prompt Updates**: "Add emergency protocol instructions"
- **Tool Description Changes**: "Clarify parameter sources"
- **New Tool Suggestions**: "Create batch temperature check"

---

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Client["🖥️ Frontend - Pipecat React SDK"]
        direction TB
        UI["💬 Voice/Text Chat UI"]
        SK["📚 Skills Browser"]
        EV["📊 Evals Dashboard"]
        RTVI["🔌 RTVI Protocol"]
        UI --> RTVI
    end
    
    subgraph Pipecat["🤖 Pipecat Agent Orchestration"]
        direction TB
        
        subgraph Transport["WebRTC Transport Layer"]
            WR["SmallWebRTC / Daily"]
        end
        
        subgraph Pipeline["Voice AI Pipeline"]
            direction LR
            STT["🎤 STT\nGoogle"]
            LLM["🧠 LLM\nOpenAI"]
            TTS["🔊 TTS\nGoogle"]
            STT --> LLM --> TTS
        end
        
        subgraph FunctionCalling["Function Calling"]
            TH["Tool Handlers"]
        end
        
        WR --> Pipeline
        LLM -->|"tool calls"| FunctionCalling
    end
    
    subgraph Engine["⚙️ Marimo Tool Chain Engine"]
        direction TB
        EX["Executor"]
        EV2["Event Stream"]
        EXP["Expression Resolver\n($s1.level)"]
        EX --> EV2
        EX --> EXP
    end
    
    subgraph Skills["💾 Skills Storage"]
        BS["Built-in Skills"]
        DS["Dynamic Skills\n(learned)"]
    end
    
    subgraph Weave["📊 Weave Observability"]
        direction TB
        TH2["Thread Traces"]
        TC["Tool Call Logs"]
        ER["Eval Results"]
    end
    
    Client <-->|"WebRTC\nAudio + RTVI Messages"| Transport
    FunctionCalling --> Engine
    Engine <--> Skills
    
    Pipecat -->|"@weave.op()\ntraces"| Weave
    Engine -->|"execution\nevents"| Weave
    
    Weave -->|"eval data"| EV
    
    style Client fill:#0f172a,stroke:#0ea5e9,stroke-width:2px
    style Pipecat fill:#0f172a,stroke:#22c55e,stroke-width:2px
    style Engine fill:#0f172a,stroke:#a855f7,stroke-width:2px
    style Skills fill:#0f172a,stroke:#f59e0b,stroke-width:2px
    style Weave fill:#0f172a,stroke:#ef4444,stroke-width:2px
```

### Component Breakdown

| Layer | Technology | Role |
|-------|------------|------|
| **Frontend** | Next.js + Pipecat React SDK | Voice UI, Skills browser, Evals dashboard |
| **Transport** | Pipecat WebRTC (SmallWebRTC/Daily) | Real-time bidirectional audio + RTVI messages |
| **Agent Orchestration** | Pipecat Pipeline | STT → LLM → TTS with function calling |
| **Tool Execution** | Marimo Engine | Streaming tool chain execution with data passing |
| **Observability** | Weave (W&B) | Thread traces, tool logs, eval results |
| **Storage** | JSON Files | Built-in + dynamically learned skills |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API Key
- Google Cloud credentials (for STT/TTS)
- Weights & Biases account (for Weave tracing)

### Server Setup

```powershell
cd toolCallAgent/server

# Install dependencies
uv sync

# Configure environment
cp env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY
# - GOOGLE_APPLICATION_CREDENTIALS
# - WANDB_API_KEY

# Run the bot
uv run bot.py
```

### Client Setup

```powershell
cd toolCallAgent/client

# Install dependencies
npm install

# Configure environment
cp env.example .env.local

# Run development server
npm run dev
```

Open http://localhost:3000 to start chatting with MothBot!

---

## 💬 Example Interactions

### Using a Skill
```
User: "Run a full diagnostic"

MothBot: I'll execute the Full System Diagnostic skill.

[Executing skill: complex_plan]
├─ Step 1: scan_hull → Integrity: 98% ✓
├─ Step 2: check_oxygen → Level: 14.5% ⚠️ CRITICAL
├─ Step 3: analyze_atmosphere → Recommendation: EVACUATE
└─ Step 4: scan_systems → Life Support: DEGRADED

Verdict: INTERVENTION_NEEDED
Critical Finding: Oxygen at dangerous levels
```

### Creating a Custom Tool Chain
```
User: "Check oxygen and then analyze the atmosphere"

MothBot: Creating a custom tool chain...

{
  "name": "Oxygen Analysis Chain",
  "steps": [
    {"id": "s1", "tool": "check_oxygen"},
    {"id": "s2", "tool": "analyze_atmosphere", "args": {"o2_level": "$s1.level"}}
  ]
}

Results: O2 at 14.5%, Recommendation: EVACUATE
```

### Saving as a Skill
```
User: "Save that as a skill"

MothBot: Saved as skill 'oxygen_analysis'!
- ID: oxygen_analysis
- Triggers: ["oxygen", "atmosphere", "analysis"]
- Now available via execute_skill
```

---

## 📊 Eval Results Example

### Skills Extraction Output
```json
{
  "extracted_skills": [
    {
      "name": "Complete Safety Diagnostic",
      "confidence": 0.92,
      "steps": ["scan_hull", "check_oxygen", "analyze_atmosphere"],
      "suggested_triggers": ["full diagnostic", "safety check"]
    }
  ],
  "traces_analyzed": 20,
  "patterns_detected": 5
}
```

### Coding Agent Output
```json
{
  "overall_score": 78,
  "suggestions": [
    {
      "type": "system_prompt_update",
      "priority": "high",
      "title": "Add Emergency Protocol Instructions",
      "estimated_impact": "Reduce emergency response time by ~40%"
    },
    {
      "type": "tool_design_change",
      "priority": "high", 
      "title": "Add Batch Temperature Check Tool",
      "estimated_impact": "Reduce multi-zone check time by ~66%"
    }
  ]
}
```

---

## 🗂️ Project Structure

```
marimo_engine/
├── core/                    # Tool chain execution engine
│   ├── executor.py          # Main execution logic
│   ├── events.py            # Event types (START, STEP_COMPLETE, etc.)
│   └── expressions.py       # $reference syntax evaluation
├── tools/                   # Tool definitions
│   ├── registry.py          # Tool management
│   └── examples.py          # Example diagnostic tools
├── plans/                   # Skill/plan schemas
│   ├── schema.py            # Pydantic models
│   └── examples.py          # Built-in skills
├── toolCallAgent/           # Main application
│   ├── server/
│   │   ├── bot.py           # Pipecat voice agent
│   │   ├── tools.py         # Tool handlers + system prompt
│   │   ├── skills_api.py    # REST API for skills
│   │   └── weave_tracing.py # Weave integration
│   └── client/
│       └── src/app/
│           ├── page.tsx     # Chat interface
│           ├── skills/      # Skills browser
│           └── evals/       # Eval results dashboard
└── README.md                # This file
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `OPENAI_MODEL` | Model to use (default: gpt-4o-mini) | No |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google Cloud JSON | Yes |
| `GOOGLE_LOCATION` | Google Cloud region | No |
| `WANDB_API_KEY` | Weights & Biases API key | Yes |
| `WEAVE_PROJECT_NAME` | Project name for traces | No |
| `WEAVE_DISABLED` | Set "true" to disable tracing | No |
| `TOOL_DELAYS_DISABLED` | Set "true" for fast testing | No |

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Agent Framework** | [Pipecat](https://pipecat.ai) | Voice AI pipeline orchestration, WebRTC transport, RTVI protocol |
| **Frontend SDK** | Pipecat React SDK | Real-time voice UI components, client-agent connection |
| **Tool Chains** | Marimo Engine | Streaming execution with data passing & conditionals |
| **Observability** | [Weave](https://wandb.ai/site/weave) (W&B) | Thread traces, tool call logging, evaluations |
| **LLM** | OpenAI (gpt-4o-mini) | Function calling & reasoning |
| **Speech** | Google Cloud STT/TTS | Speech recognition & synthesis |
| **Frontend** | Next.js 14 + React | Chat UI, Skills browser, Evals dashboard |
| **Transport** | SmallWebRTC / Daily | Real-time bidirectional audio streaming |

---

## 🦋 Why "MothBot"?

Like a moth drawn to light, MothBot is drawn to **patterns**. It observes, learns, and evolves—turning scattered tool calls into elegant, reusable skills. Each conversation makes it smarter.

---

## 📚 Learn More

- [Pipecat Documentation](https://docs.pipecat.ai/)
- [Weave Documentation](https://wandb.ai/site/weave)
- [Marimo Documentation](https://marimo.io/)

---

## 🏆 Built for Weave Hackathon 2026

MothBot demonstrates how **Weave tracing** enables a new paradigm of self-improving AI agents. By capturing every tool call and conversation thread, we unlock:

1. **Automatic skill extraction** from successful interactions
2. **Data-driven prompt optimization** based on real usage
3. **Continuous improvement** without manual intervention

*The future of AI agents isn't just calling tools—it's learning from every call.*
