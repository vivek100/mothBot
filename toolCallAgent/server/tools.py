"""
Tool definitions and handlers for the Pipecat Diagnostic Agent.

This module provides:
1. Tool definitions for OpenAI function calling
2. Tool handler functions that execute the actual tools
3. Integration with marimo_engine for plan execution
4. Weave tracing for all tool executions
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

import weave

# Add marimo_engine to path for imports
# tools.py is at: toolCallAgent/server/tools.py
# marimo_engine is at: marimo_engine/
# So we need to go up 3 levels to toolChainEngine, then the marimo_engine folder is there
toolchain_path = Path(__file__).parent.parent.parent.parent  # toolChainEngine folder
sys.path.insert(0, str(toolchain_path))

from marimo_engine import execute_plan, execute_plan_sync
from marimo_engine.tools import get_example_tools
from marimo_engine.tools.examples import set_delay_config, disable_delays
from marimo_engine.plans import get_test_plan, get_example_plans, save_skill, delete_skill, get_dynamic_skills

# Configure tool delays based on environment
# Set TOOL_DELAYS_DISABLED=true to disable delays for faster testing
if os.getenv("TOOL_DELAYS_DISABLED", "false").lower() == "true":
    disable_delays()
    print("⚡ Tool delays disabled for fast testing")
else:
    # Use shorter delays (1-3 seconds) instead of default (3-6 seconds)
    # to avoid LLM function call timeouts
    delay_min = float(os.getenv("TOOL_DELAY_MIN", "1.0"))
    delay_max = float(os.getenv("TOOL_DELAY_MAX", "3.0"))
    set_delay_config(min_delay=delay_min, max_delay=delay_max, enabled=True)
    print(f"⏱️ Tool delays configured: {delay_min}-{delay_max} seconds")

# Get the marimo_engine tools
_marimo_tools = get_example_tools()


# =============================================================================
# Tool Definitions for OpenAI Function Calling
# =============================================================================

TOOL_DEFINITIONS = [
    # Individual Diagnostic Tools
    {
        "type": "function",
        "function": {
            "name": "scan_hull",
            "description": "Scan the hull for structural integrity and detect any breaches. Returns integrity percentage and breach detection status. Takes 3-6 seconds.",
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
            "description": "Check oxygen levels in the atmosphere. Returns current oxygen level percentage, status (NORMAL/CRITICAL_LOW), and safe threshold. Takes 3-6 seconds.",
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
            "description": "Analyze the atmosphere based on a given oxygen level. Returns recommendation (MONITOR/ALERT/EVACUATE) and severity level. Use after check_oxygen and pass $step_id.level as o2_level in tool chains.",
            "parameters": {
                "type": "object",
                "properties": {
                    "o2_level": {
                        "type": "number",
                        "description": "The oxygen level percentage to analyze (get this from check_oxygen result)"
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
            "description": "Check temperature in a specific zone of the facility. Available zones: main, engine, cargo. Takes 3-6 seconds.",
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
            "description": "Perform a comprehensive scan of all systems including power, navigation, life support, and communications. Takes 3-6 seconds.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    
    # Skill & Tool Chain Management Tools
    {
        "type": "function",
        "function": {
            "name": "list_skills",
            "description": "List all saved skills (predefined tool chains) with their descriptions and usage guidance. Use this to discover what skills are available before executing one.",
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
            "name": "get_skill_details",
            "description": "Get detailed information about a specific skill including: when to use it, expected outcomes, debug tips, and fallback tools. Use this before executing an unfamiliar skill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_id": {
                        "type": "string",
                        "description": "The skill ID to get details for (e.g., 'diagnostic_sequence', 'complex_plan')"
                    }
                },
                "required": ["skill_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_skill",
            "description": "Execute a saved skill (predefined tool chain) by its ID. The skill will run all steps in sequence, passing data between steps as configured.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_id": {
                        "type": "string",
                        "description": "ID of the skill to execute",
                        "enum": ["diagnostic_sequence", "conditional_plan", "intervention_plan", "async_plan", "complex_plan"]
                    }
                },
                "required": ["skill_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_and_run_tool_chain",
            "description": "Create a custom tool chain at runtime and execute it. Use this when no existing skill matches your needs or you need a custom combination of tools. Steps can reference previous step outputs using $step_id.field syntax.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name for this custom tool chain"
                    },
                    "description": {
                        "type": "string",
                        "description": "What this tool chain does"
                    },
                    "steps": {
                        "type": "array",
                        "description": "Array of steps to execute. Each step needs 'id' and 'tool', optionally 'args', 'run_if', 'key_finding'",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Unique step identifier (e.g., 's1', 's2')"
                                },
                                "tool": {
                                    "type": "string",
                                    "description": "Tool name to execute"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "What this step does"
                                },
                                "args": {
                                    "type": "object",
                                    "description": "Arguments for the tool. Use $step_id.field to reference previous outputs"
                                },
                                "run_if": {
                                    "type": "string",
                                    "description": "Condition for running this step (e.g., '$s1.status == OK')"
                                },
                                "key_finding": {
                                    "type": "boolean",
                                    "description": "Mark this step's output as a key finding"
                                }
                            },
                            "required": ["id", "tool"]
                        }
                    }
                },
                "required": ["name", "steps"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_tool_chain_as_skill",
            "description": "Save a tool chain as a reusable skill. Use this when the user asks to save a successful tool chain for future use. The skill will be persisted and available in list_skills.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_id": {
                        "type": "string",
                        "description": "Unique identifier for the skill (e.g., 'oxygen_safety_check'). Will be converted to lowercase with underscores."
                    },
                    "name": {
                        "type": "string",
                        "description": "Human-readable name for the skill (e.g., 'Oxygen Safety Check')"
                    },
                    "description": {
                        "type": "string",
                        "description": "What this skill does"
                    },
                    "steps": {
                        "type": "array",
                        "description": "Array of steps (same format as create_and_run_tool_chain)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "tool": {"type": "string"},
                                "description": {"type": "string"},
                                "args": {"type": "object"},
                                "run_if": {"type": "string"},
                                "key_finding": {"type": "boolean"}
                            },
                            "required": ["id", "tool"]
                        }
                    },
                    "when_to_use": {
                        "type": "string",
                        "description": "Guidance on when to use this skill (helps agent decide when to use it)"
                    },
                    "expected_outcome": {
                        "type": "string",
                        "description": "What to expect after running this skill"
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords that suggest this skill (e.g., ['oxygen', 'safety', 'atmosphere'])"
                    }
                },
                "required": ["skill_id", "name", "description", "steps"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_saved_skill",
            "description": "Delete a dynamically saved skill. Only works for skills that were saved using save_tool_chain_as_skill, not built-in skills.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_id": {
                        "type": "string",
                        "description": "ID of the skill to delete"
                    }
                },
                "required": ["skill_id"]
            }
        }
    }
]


# =============================================================================
# Tool Handler Functions
# =============================================================================

import asyncio


@weave.op()
async def handle_scan_hull() -> str:
    """Execute hull scan and return formatted results."""
    # Run blocking tool in thread pool to not block event loop
    result = await asyncio.to_thread(_marimo_tools["scan_hull"])
    return json.dumps({
        "tool": "scan_hull",
        "status": "success",
        "result": result,
        "summary": f"Hull integrity at {result['integrity_percent']}. Breach detected: {result['breach_detected']}"
    }, indent=2)


@weave.op()
async def handle_check_oxygen() -> str:
    """Execute oxygen check and return formatted results."""
    # Run blocking tool in thread pool to not block event loop
    result = await asyncio.to_thread(_marimo_tools["check_oxygen"])
    return json.dumps({
        "tool": "check_oxygen",
        "status": "success",
        "result": result,
        "summary": f"Oxygen level: {result['level']}% ({result['status']}). Safe threshold: {result['threshold']}%"
    }, indent=2)


@weave.op()
async def handle_analyze_atmosphere(o2_level: float) -> str:
    """Analyze atmosphere based on oxygen level."""
    # Run blocking tool in thread pool to not block event loop
    result = await asyncio.to_thread(_marimo_tools["analyze_atmosphere"], o2_level)
    return json.dumps({
        "tool": "analyze_atmosphere",
        "status": "success",
        "result": result,
        "summary": f"Recommendation: {result['recommendation']} (Severity: {result['severity']}). {result['reason']}"
    }, indent=2)


@weave.op()
async def handle_check_temperature(zone: str = "main") -> str:
    """Check temperature in specified zone."""
    # Run blocking tool in thread pool to not block event loop
    result = await asyncio.to_thread(_marimo_tools["check_temperature"], zone)
    return json.dumps({
        "tool": "check_temperature",
        "status": "success",
        "result": result,
        "summary": f"Temperature in {result['zone']}: {result['temperature']}°{result['unit'].upper()} ({result['status']})"
    }, indent=2)


@weave.op()
async def handle_scan_systems() -> str:
    """Perform comprehensive system scan."""
    # This is an async tool in marimo_engine - already uses asyncio.sleep
    result = await _marimo_tools["async_scan_systems"]()
    return json.dumps({
        "tool": "scan_systems",
        "status": "success",
        "result": result,
        "summary": f"Systems status - Power: {result['power']}, Navigation: {result['navigation']}, Life Support: {result['life_support']}, Comms: {result['communications']}"
    }, indent=2)


@weave.op()
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


@weave.op()
async def handle_list_available_plans() -> str:
    """List all available predefined plans (legacy - use list_skills instead)."""
    return await handle_list_skills()


@weave.op()
async def handle_list_skills() -> str:
    """List all saved skills with usage guidance."""
    plans = get_example_plans()
    skills_info = []
    
    for plan in plans:
        skills_info.append({
            "id": plan.get("id"),
            "name": plan.get("name"),
            "description": plan.get("description"),
            "when_to_use": plan.get("when_to_use", "")[:200] + "..." if len(plan.get("when_to_use", "")) > 200 else plan.get("when_to_use", ""),
            "steps_count": len(plan.get("steps", [])),
            "has_intervention": any(s.get("intervention_if") for s in plan.get("steps", [])),
            "keywords": plan.get("triggers", {}).get("keywords", []) if plan.get("triggers") else []
        })
    
    return json.dumps({
        "tool": "list_skills",
        "status": "success",
        "skills": skills_info,
        "summary": f"Found {len(skills_info)} saved skills. Use get_skill_details for full info on any skill."
    }, indent=2)


@weave.op()
async def handle_get_skill_details(skill_id: str) -> str:
    """Get detailed information about a specific skill."""
    plans = {p["id"]: p for p in get_example_plans()}
    
    if skill_id not in plans:
        available = list(plans.keys())
        return json.dumps({
            "tool": "get_skill_details",
            "status": "error",
            "error": f"Skill '{skill_id}' not found",
            "available_skills": available,
            "suggestion": "Use list_skills to see all available skills"
        }, indent=2)
    
    skill = plans[skill_id]
    
    # Extract step summaries
    steps_summary = []
    for step in skill.get("steps", []):
        step_info = {
            "id": step.get("id"),
            "tool": step.get("tool"),
            "description": step.get("description", "")
        }
        if step.get("args"):
            step_info["args"] = step.get("args")
        if step.get("run_if"):
            step_info["conditional"] = step.get("run_if")
        if step.get("key_finding"):
            step_info["key_finding"] = True
        if step.get("intervention_if"):
            step_info["intervention_trigger"] = step.get("intervention_if")
        steps_summary.append(step_info)
    
    return json.dumps({
        "tool": "get_skill_details",
        "status": "success",
        "skill": {
            "id": skill.get("id"),
            "name": skill.get("name"),
            "description": skill.get("description"),
            "when_to_use": skill.get("when_to_use", "Not specified"),
            "expected_outcome": skill.get("expected_outcome", "Not specified"),
            "debug_tips": skill.get("debug_tips", []),
            "fallback_tools": skill.get("fallback_tools", []),
            "steps": steps_summary
        }
    }, indent=2)


@weave.op()
async def handle_execute_skill(skill_id: str) -> str:
    """Execute a saved skill by ID."""
    plans = {p["id"]: p for p in get_example_plans()}
    
    if skill_id not in plans:
        available = list(plans.keys())
        return json.dumps({
            "tool": "execute_skill",
            "status": "error",
            "error": f"Skill '{skill_id}' not found",
            "available_skills": available
        }, indent=2)
    
    plan = plans[skill_id]
    tools = get_example_tools()
    
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
        "tool": "execute_skill",
        "status": "success",
        "skill_id": skill_id,
        "skill_name": plan.get("name", skill_id),
        "verdict": verdict,
        "events": events,
        "outputs": outputs,
        "summary": f"Skill '{plan.get('name', skill_id)}' completed with verdict: {verdict}"
    }, indent=2)


@weave.op()
async def handle_create_and_run_tool_chain(name: str, steps: list, description: str = "") -> str:
    """Create a custom tool chain at runtime and execute it."""
    import time as time_module
    
    tools = get_example_tools()
    available_tools = list(tools.keys())
    
    # Validate steps reference valid tools
    for step in steps:
        tool_name = step.get("tool")
        if tool_name not in available_tools:
            return json.dumps({
                "tool": "create_and_run_tool_chain",
                "status": "error",
                "error": f"Unknown tool '{tool_name}' in step '{step.get('id')}'",
                "available_tools": available_tools,
                "suggestion": "Check tool name spelling or use list_skills to see available tools"
            }, indent=2)
    
    # Build the custom tool chain
    custom_chain = {
        "id": f"custom_{int(time_module.time())}",
        "name": name,
        "description": description or f"Custom tool chain: {name}",
        "steps": steps
    }
    
    # Execute using existing plan executor
    events = []
    outputs = {}
    verdict = None
    error_info = None
    
    async for event in execute_plan(custom_chain, tools):
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
            error_info = event.error
        if hasattr(event, 'intervention_reason') and event.intervention_reason:
            event_data["intervention_reason"] = event.intervention_reason
            
        events.append(event_data)
    
    result = {
        "tool": "create_and_run_tool_chain",
        "status": "success" if verdict != "FAILURE" else "error",
        "chain_name": name,
        "verdict": verdict,
        "events": events,
        "outputs": outputs,
        "summary": f"Tool chain '{name}' completed with verdict: {verdict}"
    }
    
    if error_info:
        result["error"] = error_info
        result["debug_suggestion"] = "Try running the failing tool individually to isolate the issue"
    
    return json.dumps(result, indent=2)


@weave.op()
async def handle_save_tool_chain_as_skill(
    skill_id: str,
    name: str,
    description: str,
    steps: list,
    when_to_use: str = None,
    expected_outcome: str = None,
    keywords: list = None
) -> str:
    """Save a tool chain as a reusable skill."""
    tools = get_example_tools()
    available_tools = list(tools.keys())
    
    # Validate steps reference valid tools
    for step in steps:
        tool_name = step.get("tool")
        if tool_name not in available_tools:
            return json.dumps({
                "tool": "save_tool_chain_as_skill",
                "status": "error",
                "error": f"Unknown tool '{tool_name}' in step '{step.get('id')}'",
                "available_tools": available_tools
            }, indent=2)
    
    # Extract fallback tools from steps
    fallback_tools = list(set(s.get("tool") for s in steps if s.get("tool")))
    
    # Generate debug tips based on steps
    debug_tips = []
    for i, step in enumerate(steps):
        if step.get("args"):
            # Check for references to previous steps
            for arg_key, arg_val in step.get("args", {}).items():
                if isinstance(arg_val, str) and arg_val.startswith("$"):
                    ref_step = arg_val.split(".")[0].replace("$", "")
                    debug_tips.append(f"Step '{step.get('id')}' depends on '{ref_step}' - ensure it completes successfully")
    
    if not debug_tips:
        debug_tips = ["Run individual tools to isolate issues if the skill fails"]
    
    try:
        saved_skill = save_skill(
            skill_id=skill_id,
            name=name,
            description=description,
            steps=steps,
            when_to_use=when_to_use,
            expected_outcome=expected_outcome,
            debug_tips=debug_tips,
            fallback_tools=fallback_tools,
            keywords=keywords
        )
        
        return json.dumps({
            "tool": "save_tool_chain_as_skill",
            "status": "success",
            "skill_id": saved_skill["id"],
            "skill_name": saved_skill["name"],
            "steps_count": len(saved_skill["steps"]),
            "summary": f"Skill '{saved_skill['name']}' saved successfully with ID '{saved_skill['id']}'. It will now appear in list_skills and can be executed with execute_skill."
        }, indent=2)
        
    except ValueError as e:
        return json.dumps({
            "tool": "save_tool_chain_as_skill",
            "status": "error",
            "error": str(e)
        }, indent=2)
    except IOError as e:
        return json.dumps({
            "tool": "save_tool_chain_as_skill",
            "status": "error",
            "error": f"Failed to save skill to file: {str(e)}"
        }, indent=2)


@weave.op()
async def handle_delete_saved_skill(skill_id: str) -> str:
    """Delete a dynamically saved skill."""
    try:
        deleted = delete_skill(skill_id)
        
        if deleted:
            return json.dumps({
                "tool": "delete_saved_skill",
                "status": "success",
                "skill_id": skill_id,
                "summary": f"Skill '{skill_id}' has been deleted successfully."
            }, indent=2)
        else:
            # Get list of dynamic skills for suggestion
            dynamic = get_dynamic_skills()
            dynamic_ids = [s["id"] for s in dynamic]
            
            return json.dumps({
                "tool": "delete_saved_skill",
                "status": "error",
                "error": f"Skill '{skill_id}' not found in saved skills",
                "available_dynamic_skills": dynamic_ids if dynamic_ids else "No dynamically saved skills exist",
                "suggestion": "Only dynamically saved skills can be deleted. Use list_skills to see all skills."
            }, indent=2)
            
    except ValueError as e:
        return json.dumps({
            "tool": "delete_saved_skill",
            "status": "error",
            "error": str(e)
        }, indent=2)


# =============================================================================
# Tool Handler Registry
# =============================================================================

TOOL_HANDLERS = {
    # Individual diagnostic tools
    "scan_hull": handle_scan_hull,
    "check_oxygen": handle_check_oxygen,
    "analyze_atmosphere": handle_analyze_atmosphere,
    "check_temperature": handle_check_temperature,
    "scan_systems": handle_scan_systems,
    
    # Skill & tool chain management
    "list_skills": handle_list_skills,
    "get_skill_details": handle_get_skill_details,
    "execute_skill": handle_execute_skill,
    "create_and_run_tool_chain": handle_create_and_run_tool_chain,
    "save_tool_chain_as_skill": handle_save_tool_chain_as_skill,
    "delete_saved_skill": handle_delete_saved_skill,
    
    # Legacy aliases (backward compatibility)
    "execute_diagnostic_plan": handle_execute_diagnostic_plan,
    "list_available_plans": handle_list_available_plans,
}


@weave.op()
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

SYSTEM_PROMPT = """You are a Diagnostic Agent for a space station monitoring system. You can use individual tools OR create/execute tool chains for complex diagnostics.

## Core Concepts

### Individual Tools
Single-purpose diagnostic functions that return immediate results.

### Tool Chains
Sequences of tools that run in order, where output from one step can feed into the next. Tool chains support:
- **Data passing**: Use `$step_id.field` to reference previous outputs (e.g., `$s1.level`)
- **Conditional execution**: Steps can be skipped based on conditions (`run_if`)
- **Key findings**: Important results are highlighted
- **Intervention triggers**: Automatic alerts for critical conditions

### Skills (Saved Tool Chains)
Pre-defined tool chains with usage guidance. Each skill includes:
- When to use it
- Expected outcomes
- Debug tips if something fails
- Fallback tools to try individually

## Available Tools

### Individual Diagnostic Tools
| Tool | Description | Parameters |
|------|-------------|------------|
| `scan_hull` | Scan hull for integrity and breaches | None |
| `check_oxygen` | Check atmospheric oxygen levels | None |
| `analyze_atmosphere` | Analyze atmosphere based on O2 level | `o2_level` (float, required) |
| `check_temperature` | Check temperature in a zone | `zone` (main/engine/cargo) |
| `scan_systems` | Comprehensive scan of all systems | None |

### Skill & Tool Chain Management
| Tool | Description |
|------|-------------|
| `list_skills` | List all saved skills with usage guidance |
| `get_skill_details` | Get detailed info about a specific skill |
| `execute_skill` | Execute a saved skill by ID |
| `create_and_run_tool_chain` | Create a custom tool chain at runtime and execute it |
| `save_tool_chain_as_skill` | Save a tool chain as a reusable skill for future use |
| `delete_saved_skill` | Delete a dynamically saved skill |

## Saving Tool Chains as Skills

When a user asks to save a tool chain they've created, use `save_tool_chain_as_skill`. This persists the tool chain so it can be reused later.

### When to Save a Skill:
- User explicitly asks to "save this", "remember this", or "save as skill"
- A custom tool chain was successful and user wants to reuse it
- User wants to create a reusable procedure

### What to Include When Saving:
- **skill_id**: A unique identifier (e.g., "oxygen_safety_check")
- **name**: Human-readable name
- **description**: What the skill does
- **steps**: The tool chain steps
- **when_to_use**: Guidance for when to use this skill (helps you decide later)
- **keywords**: Words that suggest this skill

## When to Use What

### Use Individual Tools When:
- User asks about ONE specific thing ("check oxygen")
- Need quick, targeted information
- Debugging a failed tool chain step
- Testing if a specific tool works

### Use Saved Skills When:
- User wants comprehensive diagnostics ("run full diagnostic")
- Multiple related checks are needed
- Data from one check feeds into another
- You want consistent, repeatable procedures

### Create Custom Tool Chains When:
- No existing skill matches the need
- User requests a specific combination of checks
- You need to adapt a procedure for special circumstances

## Creating Tool Chains at Runtime

Use `create_and_run_tool_chain` to build custom sequences:

```json
{
  "name": "Custom Safety Check",
  "steps": [
    {"id": "s1", "tool": "check_oxygen"},
    {"id": "s2", "tool": "check_temperature", "args": {"zone": "main"}},
    {"id": "s3", "tool": "analyze_atmosphere", "args": {"o2_level": "$s1.level"}}
  ]
}
```

### Step Reference Syntax
- `$step_id` - Reference entire output of a step
- `$step_id.field` - Reference specific field (e.g., `$s1.level`)
- `$step_id.nested.field` - Reference nested fields

## Debugging Failed Tool Chains

If a tool chain fails:

1. **Check the error message** - It tells you which step failed and why
2. **Run the failing tool individually** - Isolate the problem
3. **Check dependencies** - Did a previous step provide required data?
4. **Use `get_skill_details`** - Read the debug_tips for that skill
5. **Try fallback tools** - Each skill lists individual tools you can try
6. **Re-run with modifications** - Create a new chain fixing the issue

### Example Debug Flow
```
User: "Run a full diagnostic"
→ Execute diagnostic_sequence skill
→ Step s3 (analyze_atmosphere) fails: "No oxygen level provided"
→ Run check_oxygen individually to verify it works
→ Check if s2 completed and has 'level' field
→ Re-run the skill or create modified chain
```

## Response Guidelines

1. **Explain your approach** - Tell user if using skill or individual tools
2. **Report findings clearly** - Summarize key results, highlight critical issues
3. **Suggest next steps** - If issues found, recommend follow-up actions
4. **Be transparent about failures** - Explain what you're doing to debug
5. **Flag interventions immediately** - Critical conditions need immediate attention

## Safety Priority

- ALWAYS flag critical issues immediately (low oxygen, hull breaches)
- INTERVENTION_NEEDED verdict means human action required
- When in doubt, run additional checks rather than assuming OK

Remember: Each tool takes 3-6 seconds to execute (simulated sensor delays). Tool chains with multiple steps will take proportionally longer."""
