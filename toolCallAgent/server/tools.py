"""
Tool definitions and handlers for the Pipecat Diagnostic Agent.

This module provides:
1. Tool definitions for OpenAI function calling
2. Tool handler functions that execute the actual tools
3. Integration with marimo_engine for plan execution
"""

import json
import sys
from pathlib import Path
from typing import Any

# Add marimo_engine to path for imports
# tools.py is at: toolCallAgent/server/tools.py
# marimo_engine is at: marimo_engine/
# So we need to go up 3 levels to toolChainEngine, then the marimo_engine folder is there
toolchain_path = Path(__file__).parent.parent.parent.parent  # toolChainEngine folder
sys.path.insert(0, str(toolchain_path))

from marimo_engine import execute_plan, execute_plan_sync
from marimo_engine.tools import get_example_tools
from marimo_engine.plans import get_test_plan, get_example_plans

# Get the marimo_engine tools
_marimo_tools = get_example_tools()


# =============================================================================
# Tool Definitions for OpenAI Function Calling
# =============================================================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "scan_hull",
            "description": "Scan the hull for structural integrity and detect any breaches. Returns integrity percentage and breach detection status.",
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
            "description": "Check oxygen levels in the atmosphere. Returns current oxygen level percentage, status (NORMAL/CRITICAL_LOW), and safe threshold.",
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
            "description": "Analyze the atmosphere based on a given oxygen level. Returns recommendation (MONITOR/ALERT/EVACUATE) and severity level.",
            "parameters": {
                "type": "object",
                "properties": {
                    "o2_level": {
                        "type": "number",
                        "description": "The oxygen level percentage to analyze"
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
            "description": "Check temperature in a specific zone of the facility. Available zones: main, engine, cargo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone": {
                        "type": "string",
                        "description": "The zone to check temperature in",
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
            "name": "scan_systems",
            "description": "Perform a comprehensive scan of all systems including power, navigation, life support, and communications.",
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
            "name": "execute_diagnostic_plan",
            "description": "Execute a multi-step diagnostic plan. Use this for comprehensive diagnostics that require multiple tools to be run in sequence with dependencies between steps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_name": {
                        "type": "string",
                        "description": "Name of the predefined plan to execute",
                        "enum": ["diagnostic_sequence", "conditional_plan", "intervention_plan", "async_plan", "complex_plan"]
                    },
                    "custom_plan": {
                        "type": "string",
                        "description": "Optional: JSON string of a custom plan. If provided, this overrides plan_name. Format: {\"steps\": [{\"id\": \"s1\", \"tool\": \"scan_hull\"}, ...]}"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_plans",
            "description": "List all available predefined diagnostic plans with their descriptions.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


# =============================================================================
# Tool Handler Functions
# =============================================================================

async def handle_scan_hull() -> str:
    """Execute hull scan and return formatted results."""
    result = _marimo_tools["scan_hull"]()
    return json.dumps({
        "tool": "scan_hull",
        "status": "success",
        "result": result,
        "summary": f"Hull integrity at {result['integrity_percent']}. Breach detected: {result['breach_detected']}"
    }, indent=2)


async def handle_check_oxygen() -> str:
    """Execute oxygen check and return formatted results."""
    result = _marimo_tools["check_oxygen"]()
    return json.dumps({
        "tool": "check_oxygen",
        "status": "success",
        "result": result,
        "summary": f"Oxygen level: {result['level']}% ({result['status']}). Safe threshold: {result['threshold']}%"
    }, indent=2)


async def handle_analyze_atmosphere(o2_level: float) -> str:
    """Analyze atmosphere based on oxygen level."""
    result = _marimo_tools["analyze_atmosphere"](o2_level)
    return json.dumps({
        "tool": "analyze_atmosphere",
        "status": "success",
        "result": result,
        "summary": f"Recommendation: {result['recommendation']} (Severity: {result['severity']}). {result['reason']}"
    }, indent=2)


async def handle_check_temperature(zone: str = "main") -> str:
    """Check temperature in specified zone."""
    result = _marimo_tools["check_temperature"](zone)
    return json.dumps({
        "tool": "check_temperature",
        "status": "success",
        "result": result,
        "summary": f"Temperature in {result['zone']}: {result['temperature']}°{result['unit'].upper()} ({result['status']})"
    }, indent=2)


async def handle_scan_systems() -> str:
    """Perform comprehensive system scan."""
    # This is an async tool in marimo_engine
    import asyncio
    result = await _marimo_tools["async_scan_systems"]()
    return json.dumps({
        "tool": "scan_systems",
        "status": "success",
        "result": result,
        "summary": f"Systems status - Power: {result['power']}, Navigation: {result['navigation']}, Life Support: {result['life_support']}, Comms: {result['communications']}"
    }, indent=2)


async def handle_execute_diagnostic_plan(plan_name: str = None, custom_plan: str = None) -> str:
    """Execute a diagnostic plan using the marimo_engine."""
    tools = get_example_tools()
    
    # Determine which plan to use
    if custom_plan:
        try:
            plan = json.loads(custom_plan)
        except json.JSONDecodeError as e:
            return json.dumps({
                "tool": "execute_diagnostic_plan",
                "status": "error",
                "error": f"Invalid custom plan JSON: {str(e)}"
            }, indent=2)
    elif plan_name:
        # Get predefined plan
        plans = {p["id"]: p for p in get_example_plans()}
        if plan_name not in plans:
            return json.dumps({
                "tool": "execute_diagnostic_plan",
                "status": "error",
                "error": f"Plan '{plan_name}' not found. Available: {list(plans.keys())}"
            }, indent=2)
        plan = plans[plan_name]
    else:
        # Default to diagnostic_sequence
        plan = get_test_plan()
    
    # Execute the plan and collect events
    events = []
    outputs = {}
    verdict = None
    
    async for event in execute_plan(plan, tools):
        event_data = {
            "type": event.type.value,
            "msg": event.msg
        }
        
        if hasattr(event, 'step_id') and event.step_id:
            event_data["step_id"] = event.step_id
        if hasattr(event, 'output') and event.output:
            event_data["output"] = event.output
            if hasattr(event, 'step_id') and event.step_id:
                outputs[event.step_id] = event.output
        if hasattr(event, 'verdict') and event.verdict:
            verdict = event.verdict.value
        if hasattr(event, 'error') and event.error:
            event_data["error"] = event.error
        if hasattr(event, 'intervention_reason') and event.intervention_reason:
            event_data["intervention_reason"] = event.intervention_reason
            
        events.append(event_data)
    
    return json.dumps({
        "tool": "execute_diagnostic_plan",
        "status": "success",
        "plan_id": plan.get("id", "custom"),
        "plan_name": plan.get("name", "Custom Plan"),
        "verdict": verdict,
        "events": events,
        "outputs": outputs,
        "summary": f"Plan '{plan.get('name', plan.get('id', 'custom'))}' completed with verdict: {verdict}"
    }, indent=2)


async def handle_list_available_plans() -> str:
    """List all available predefined plans."""
    plans = get_example_plans()
    plan_info = []
    
    for plan in plans:
        plan_info.append({
            "id": plan.get("id"),
            "name": plan.get("name"),
            "description": plan.get("description"),
            "steps_count": len(plan.get("steps", []))
        })
    
    return json.dumps({
        "tool": "list_available_plans",
        "status": "success",
        "plans": plan_info,
        "summary": f"Found {len(plan_info)} available diagnostic plans"
    }, indent=2)


# =============================================================================
# Tool Handler Registry
# =============================================================================

TOOL_HANDLERS = {
    "scan_hull": handle_scan_hull,
    "check_oxygen": handle_check_oxygen,
    "analyze_atmosphere": handle_analyze_atmosphere,
    "check_temperature": handle_check_temperature,
    "scan_systems": handle_scan_systems,
    "execute_diagnostic_plan": handle_execute_diagnostic_plan,
    "list_available_plans": handle_list_available_plans,
}


async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """
    Execute a tool by name with the given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments to pass to the tool
        
    Returns:
        JSON string with the tool result
    """
    if tool_name not in TOOL_HANDLERS:
        return json.dumps({
            "tool": tool_name,
            "status": "error",
            "error": f"Unknown tool: {tool_name}. Available tools: {list(TOOL_HANDLERS.keys())}"
        }, indent=2)
    
    handler = TOOL_HANDLERS[tool_name]
    
    try:
        result = await handler(**arguments)
        return result
    except Exception as e:
        return json.dumps({
            "tool": tool_name,
            "status": "error",
            "error": str(e)
        }, indent=2)


# =============================================================================
# System Prompt
# =============================================================================

SYSTEM_PROMPT = """You are a Diagnostic Agent for a space station or facility monitoring system. Your role is to help users monitor and diagnose system health using various diagnostic tools.

## Available Tools

You have access to the following diagnostic tools:

### Individual Tools
1. **scan_hull** - Scan hull for structural integrity and breaches
2. **check_oxygen** - Check atmospheric oxygen levels
3. **analyze_atmosphere** - Analyze atmosphere based on oxygen level (requires o2_level parameter)
4. **check_temperature** - Check temperature in a zone (main, engine, or cargo)
5. **scan_systems** - Comprehensive scan of all systems (power, navigation, life support, communications)

### Plan Execution Tools
6. **execute_diagnostic_plan** - Execute a multi-step diagnostic plan with dependencies
7. **list_available_plans** - List all available predefined diagnostic plans

## Guidelines

1. **Use individual tools** for quick, targeted checks when the user asks about specific systems
2. **Use execute_diagnostic_plan** for comprehensive diagnostics or when multiple related checks are needed
3. **Always explain your findings** in clear, concise language
4. **Highlight critical issues** immediately (e.g., low oxygen, hull breaches)
5. **Suggest follow-up actions** when problems are detected
6. **Be proactive** - if one check reveals an issue, suggest related checks

## Response Style

- Be professional but conversational
- Summarize key findings first, then provide details if asked
- Use clear status indicators: OK, WARNING, CRITICAL
- When intervention is needed, clearly explain why and what actions to take

## Example Interactions

User: "Check the oxygen levels"
→ Use check_oxygen tool, then explain the results

User: "Run a full diagnostic"
→ Use execute_diagnostic_plan with the complex_plan or diagnostic_sequence

User: "Is everything okay?"
→ Use scan_systems for a quick overview, suggest specific checks if issues found

Remember: Safety is the top priority. Always flag critical issues immediately."""
