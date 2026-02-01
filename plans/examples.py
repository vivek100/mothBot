"""Example tool chains and saved skills for testing.

Terminology:
- Tool Chain: A sequence of tools executed in order
- Skill: A saved tool chain with usage guidance (when_to_use, debug_tips, etc.)

All examples here are "skills" - saved tool chains with rich metadata
to help the agent understand when and how to use them.

Skills can be saved dynamically at runtime using save_skill().
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

# File to store dynamically saved skills
_SAVED_SKILLS_FILE = Path(__file__).parent / "saved_skills.json"

# In-memory cache of dynamically saved skills
_dynamic_skills: List[Dict[str, Any]] = []


def _load_dynamic_skills() -> List[Dict[str, Any]]:
    """Load dynamically saved skills from file."""
    global _dynamic_skills
    
    if _SAVED_SKILLS_FILE.exists():
        try:
            with open(_SAVED_SKILLS_FILE, "r", encoding="utf-8") as f:
                _dynamic_skills = json.load(f)
        except (json.JSONDecodeError, IOError):
            _dynamic_skills = []
    
    return _dynamic_skills


def _save_dynamic_skills() -> None:
    """Save dynamically saved skills to file."""
    global _dynamic_skills
    
    try:
        with open(_SAVED_SKILLS_FILE, "w", encoding="utf-8") as f:
            json.dump(_dynamic_skills, f, indent=2)
    except IOError as e:
        raise IOError(f"Failed to save skills: {e}")


# Load skills on module import
_load_dynamic_skills()


def get_test_plan() -> Dict[str, Any]:
    """
    Get the main diagnostic sequence skill.
    
    This is the primary skill demonstrating:
    - Sequential execution
    - Argument passing between steps ($s2.level)
    - Key findings marking
    - Intervention conditions
    
    Returns:
        Skill dictionary
    """
    return {
        "id": "diagnostic_sequence",
        "name": "System Diagnostic Sequence",
        "description": "Standard diagnostic sequence checking hull, oxygen, and atmosphere in order",
        
        # Skill guidance for the agent
        "when_to_use": """Use this skill when:
- User asks for a 'diagnostic', 'health check', or 'system check'
- Multiple systems need checking in a logical sequence
- You need to correlate data (oxygen level feeds into atmosphere analysis)
- User reports general concerns without specifying which system
- Starting a shift or after an incident""",
        
        "expected_outcome": """After running this skill you will have:
- Hull integrity status (percentage, breach detection)
- Oxygen levels with status (NORMAL/CRITICAL_LOW)
- Atmosphere analysis with actionable recommendation (MONITOR/ALERT/EVACUATE)
- If oxygen is critical (<15%), verdict will be INTERVENTION_NEEDED
- Total execution time: ~10-20 seconds""",
        
        "triggers": {
            "keywords": ["diagnostic", "health check", "system check", "full scan", "check everything", "status report"],
            "user_intents": ["check_all_systems", "general_status", "safety_check", "routine_check"],
            "avoid_when": ["user asks about ONE specific system only", "need immediate quick answer"]
        },
        
        "debug_tips": [
            "If step s3 (analyze_atmosphere) fails with 'No oxygen level', check that s2 completed successfully",
            "Intervention at s3 is EXPECTED when oxygen < 15% - this is correct behavior, not an error",
            "If hull scan hangs, the tool may be simulating a slow sensor - wait for timeout",
            "Each step takes 3-6 seconds due to simulated sensor delays"
        ],
        
        "fallback_tools": ["scan_hull", "check_oxygen", "analyze_atmosphere"],
        
        "steps": [
            {
                "id": "s1",
                "tool": "scan_hull",
                "description": "External hull integrity scan"
            },
            {
                "id": "s2",
                "tool": "check_oxygen",
                "description": "Life support oxygen check",
                "key_finding": True
            },
            {
                "id": "s3",
                "tool": "analyze_atmosphere",
                "description": "Analyze atmosphere based on oxygen level",
                "args": {"o2_level": "$s2.level"},
                "intervention_if": "$s3.severity == 'HIGH'"
            }
        ]
    }


def get_conditional_plan() -> Dict[str, Any]:
    """
    Get the conditional execution skill.
    
    Demonstrates run_if conditions - steps that only run based on previous results.
    
    Returns:
        Skill dictionary
    """
    return {
        "id": "conditional_plan",
        "name": "Safe Engine Check",
        "description": "Check engine temperature only if hull is intact (conditional execution)",
        
        "when_to_use": """Use this skill when:
- Need to check engine but want to ensure hull safety first
- Demonstrating conditional tool chain execution
- Engine check should be skipped if there's a hull breach (safety protocol)""",
        
        "expected_outcome": """After running:
- Hull status will be checked first
- Engine temperature check ONLY runs if no hull breach detected
- Oxygen check always runs regardless of hull status
- If hull has breach, engine check is safely skipped""",
        
        "triggers": {
            "keywords": ["engine check", "safe check", "conditional", "if hull ok"],
            "user_intents": ["check_engine_safely", "conditional_diagnostic"],
            "prerequisites": ["No active emergency"],
            "avoid_when": ["need engine status regardless of hull", "emergency situation"]
        },
        
        "debug_tips": [
            "Step s2 being skipped is CORRECT behavior when hull breach is detected",
            "Check the STEP_SKIPPED event to see why a step was skipped",
            "The run_if condition '$s1.breach_detected == False' controls s2 execution"
        ],
        
        "fallback_tools": ["scan_hull", "check_temperature", "check_oxygen"],
        
        "steps": [
            {
                "id": "s1",
                "tool": "scan_hull",
                "description": "Initial hull scan"
            },
            {
                "id": "s2",
                "tool": "check_temperature",
                "description": "Check engine temperature (only if hull OK)",
                "args": {"zone": "engine"},
                "run_if": "$s1.breach_detected == False"
            },
            {
                "id": "s3",
                "tool": "check_oxygen",
                "description": "Check oxygen levels",
                "key_finding": True
            }
        ]
    }


def get_intervention_plan() -> Dict[str, Any]:
    """
    Get the intervention trigger skill.
    
    Demonstrates INTERVENTION_NEEDED verdict when critical conditions are met.
    
    Returns:
        Skill dictionary
    """
    return {
        "id": "intervention_plan",
        "name": "Critical Oxygen Alert",
        "description": "Check oxygen and trigger intervention if critical - demonstrates alert system",
        
        "when_to_use": """Use this skill when:
- Testing the intervention/alert system
- Need to demonstrate how critical conditions trigger human intervention
- Simulating emergency response scenarios
- Training on intervention handling""",
        
        "expected_outcome": """After running:
- Oxygen will be checked (mock returns 14.5% which is CRITICAL)
- INTERVENTION_NEEDED verdict will be triggered (oxygen < 15%)
- Atmosphere analysis still runs to provide full context
- Agent should acknowledge intervention and suggest actions""",
        
        "triggers": {
            "keywords": ["intervention test", "alert test", "critical check", "emergency drill"],
            "user_intents": ["test_alerts", "simulate_emergency"],
            "avoid_when": ["normal operations", "user wants quiet check"]
        },
        
        "debug_tips": [
            "INTERVENTION_NEEDED is the EXPECTED outcome - not an error",
            "The intervention triggers because mock oxygen returns 14.5% (< 15% threshold)",
            "After intervention, explain to user what actions would be taken in real scenario"
        ],
        
        "fallback_tools": ["check_oxygen", "analyze_atmosphere"],
        
        "steps": [
            {
                "id": "s1",
                "tool": "check_oxygen",
                "description": "Check oxygen (will be critical)",
                "key_finding": True,
                "intervention_if": "$s1.level < 15"
            },
            {
                "id": "s2",
                "tool": "analyze_atmosphere",
                "description": "Analyze (runs even after intervention flag)",
                "args": {"o2_level": "$s1.level"}
            }
        ]
    }


def get_async_plan() -> Dict[str, Any]:
    """
    Get the async tools skill.
    
    Demonstrates mixing async and sync tools in a chain.
    
    Returns:
        Skill dictionary
    """
    return {
        "id": "async_plan",
        "name": "Quick Systems Overview",
        "description": "Fast overview using async system scan followed by oxygen check",
        
        "when_to_use": """Use this skill when:
- Need a quick status overview
- Want to demonstrate async tool execution
- Checking if major systems are online before detailed diagnostics""",
        
        "expected_outcome": """After running:
- Systems scan provides status of: power, navigation, life_support, communications
- Oxygen check provides current atmospheric levels
- Quick overview without deep analysis""",
        
        "triggers": {
            "keywords": ["quick check", "systems overview", "fast status", "are systems online"],
            "user_intents": ["quick_status", "systems_overview"],
            "avoid_when": ["need detailed analysis", "specific system investigation"]
        },
        
        "debug_tips": [
            "async_scan_systems runs asynchronously but results are awaited before next step",
            "If systems scan shows DEGRADED, consider running full diagnostic"
        ],
        
        "fallback_tools": ["async_scan_systems", "check_oxygen"],
        
        "steps": [
            {
                "id": "s1",
                "tool": "async_scan_systems",
                "description": "Async system scan"
            },
            {
                "id": "s2",
                "tool": "check_oxygen",
                "description": "Sync oxygen check"
            }
        ]
    }


def get_complex_plan() -> Dict[str, Any]:
    """
    Get the comprehensive diagnostic skill.
    
    Full system diagnostic with all features:
    - Multiple steps with dependencies
    - Conditional execution
    - Key findings
    - Report generation
    
    Returns:
        Skill dictionary
    """
    return {
        "id": "complex_plan",
        "name": "Full System Diagnostic",
        "description": "Comprehensive diagnostic checking all systems with final report generation",
        
        "when_to_use": """Use this skill when:
- User requests 'full diagnostic', 'complete check', or 'everything'
- Starting a new shift or after major incident
- Need comprehensive documentation of system state
- Regulatory or safety compliance check required
- Preparing a status report for handoff""",
        
        "expected_outcome": """After running (takes ~25-45 seconds):
- Hull integrity status
- Oxygen levels (marked as key finding)
- Temperature in main area and engine room (engine only if hull OK)
- Atmosphere analysis with recommendations
- Full systems scan (power, nav, life support, comms)
- Generated summary report with severity counts
- If any HIGH severity findings, verdict is INTERVENTION_NEEDED""",
        
        "triggers": {
            "keywords": ["full diagnostic", "complete check", "comprehensive", "everything", "full report", "all systems"],
            "user_intents": ["complete_diagnostic", "shift_handoff", "compliance_check", "incident_review"],
            "prerequisites": ["Have time for full check (~30-45 seconds)", "No active emergency requiring immediate action"],
            "avoid_when": ["need quick answer", "emergency in progress", "checking single specific system"]
        },
        
        "debug_tips": [
            "This skill takes longest (~25-45 seconds) due to multiple tools",
            "temp_engine step is skipped if hull breach detected - this is correct",
            "Report generation at the end consolidates all findings",
            "If report shows HIGH severity, intervention was likely triggered earlier",
            "Check individual step outputs if report seems incomplete"
        ],
        
        "fallback_tools": ["scan_hull", "check_oxygen", "check_temperature", "analyze_atmosphere", "async_scan_systems", "generate_report"],
        
        "steps": [
            {
                "id": "hull",
                "tool": "scan_hull",
                "description": "Hull integrity scan",
                "key_finding": True
            },
            {
                "id": "oxygen",
                "tool": "check_oxygen",
                "description": "Oxygen level check",
                "key_finding": True
            },
            {
                "id": "temp_main",
                "tool": "check_temperature",
                "description": "Main area temperature",
                "args": {"zone": "main"}
            },
            {
                "id": "temp_engine",
                "tool": "check_temperature",
                "description": "Engine temperature",
                "args": {"zone": "engine"},
                "run_if": "$hull.breach_detected == False"
            },
            {
                "id": "atmosphere",
                "tool": "analyze_atmosphere",
                "description": "Atmosphere analysis",
                "args": {"o2_level": "$oxygen.level"},
                "key_finding": True,
                "intervention_if": "$atmosphere.severity == 'HIGH'"
            },
            {
                "id": "systems",
                "tool": "async_scan_systems",
                "description": "Full systems scan"
            },
            {
                "id": "report",
                "tool": "generate_report",
                "description": "Generate summary report",
                "args": {
                    "findings": {
                        "hull": "$hull",
                        "oxygen": "$oxygen",
                        "atmosphere": "$atmosphere"
                    }
                }
            }
        ]
    }


def get_builtin_plans() -> List[Dict[str, Any]]:
    """
    Get built-in example plans/skills (not dynamically saved).
    
    Returns:
        List of built-in skill dictionaries
    """
    return [
        get_test_plan(),
        get_conditional_plan(),
        get_intervention_plan(),
        get_async_plan(),
        get_complex_plan(),
    ]


def get_example_plans() -> List[Dict[str, Any]]:
    """
    Get all plans/skills (built-in + dynamically saved).
    
    Returns:
        List of skill dictionaries
    """
    # Combine built-in and dynamic skills
    return get_builtin_plans() + _dynamic_skills


# Alias for clarity
def get_saved_skills() -> List[Dict[str, Any]]:
    """Get all saved skills (built-in + dynamically saved)."""
    return get_example_plans()


def get_plan_by_id(plan_id: str) -> Dict[str, Any]:
    """
    Get a plan/skill by its ID.
    
    Args:
        plan_id: Plan identifier
        
    Returns:
        Plan/skill dictionary
        
    Raises:
        ValueError: If plan not found
    """
    plans = {p["id"]: p for p in get_example_plans()}
    
    if plan_id not in plans:
        available = ", ".join(plans.keys())
        raise ValueError(f"Plan '{plan_id}' not found. Available: {available}")
    
    return plans[plan_id]


# Alias for clarity
def get_skill_by_id(skill_id: str) -> Dict[str, Any]:
    """Get a saved skill by its ID."""
    return get_plan_by_id(skill_id)


def get_skills_summary() -> List[Dict[str, Any]]:
    """
    Get a summary of all skills for agent reference.
    
    Returns:
        List of skill summaries with key info for decision making
    """
    skills = get_saved_skills()
    summaries = []
    
    for skill in skills:
        summaries.append({
            "id": skill.get("id"),
            "name": skill.get("name"),
            "description": skill.get("description"),
            "when_to_use": skill.get("when_to_use", ""),
            "steps_count": len(skill.get("steps", [])),
            "has_intervention": any(
                s.get("intervention_if") for s in skill.get("steps", [])
            ),
            "keywords": skill.get("triggers", {}).get("keywords", []) if skill.get("triggers") else [],
            "is_dynamic": skill.get("_dynamic", False)
        })
    
    return summaries


# =============================================================================
# Dynamic Skill Management
# =============================================================================

def save_skill(
    skill_id: str,
    name: str,
    description: str,
    steps: List[Dict[str, Any]],
    when_to_use: Optional[str] = None,
    expected_outcome: Optional[str] = None,
    debug_tips: Optional[List[str]] = None,
    fallback_tools: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Save a tool chain as a reusable skill.
    
    Args:
        skill_id: Unique identifier for the skill (will be sanitized)
        name: Human-readable name
        description: What this skill does
        steps: List of step dictionaries
        when_to_use: Guidance on when to use this skill
        expected_outcome: What to expect after running
        debug_tips: Tips for debugging if skill fails
        fallback_tools: Individual tools to try if skill fails
        keywords: Keywords that suggest this skill
        
    Returns:
        The saved skill dictionary
        
    Raises:
        ValueError: If skill_id already exists or steps are invalid
    """
    global _dynamic_skills
    
    # Sanitize skill_id (lowercase, underscores)
    skill_id = skill_id.lower().replace(" ", "_").replace("-", "_")
    
    # Check if ID already exists (in built-in or dynamic skills)
    all_skills = get_saved_skills()
    existing_ids = [s["id"] for s in all_skills]
    
    if skill_id in existing_ids:
        raise ValueError(f"Skill with ID '{skill_id}' already exists. Use a different ID or delete the existing skill first.")
    
    # Validate steps
    if not steps or len(steps) == 0:
        raise ValueError("Skill must have at least one step")
    
    for i, step in enumerate(steps):
        if not step.get("id"):
            raise ValueError(f"Step {i} is missing 'id' field")
        if not step.get("tool"):
            raise ValueError(f"Step {i} is missing 'tool' field")
    
    # Extract fallback tools from steps if not provided
    if fallback_tools is None:
        fallback_tools = list(set(s.get("tool") for s in steps if s.get("tool")))
    
    # Build the skill
    skill = {
        "id": skill_id,
        "name": name,
        "description": description,
        "steps": steps,
        "_dynamic": True,  # Mark as dynamically created
    }
    
    # Add optional fields
    if when_to_use:
        skill["when_to_use"] = when_to_use
    
    if expected_outcome:
        skill["expected_outcome"] = expected_outcome
    
    if debug_tips:
        skill["debug_tips"] = debug_tips
    
    if fallback_tools:
        skill["fallback_tools"] = fallback_tools
    
    if keywords:
        skill["triggers"] = {
            "keywords": keywords,
            "user_intents": [],
        }
    
    # Add to dynamic skills and save
    _dynamic_skills.append(skill)
    _save_dynamic_skills()
    
    return skill


def delete_skill(skill_id: str) -> bool:
    """
    Delete a dynamically saved skill.
    
    Args:
        skill_id: ID of the skill to delete
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        ValueError: If trying to delete a built-in skill
    """
    global _dynamic_skills
    
    # Check if it's a built-in skill
    builtin_ids = [
        "diagnostic_sequence", "conditional_plan", "intervention_plan",
        "async_plan", "complex_plan"
    ]
    
    if skill_id in builtin_ids:
        raise ValueError(f"Cannot delete built-in skill '{skill_id}'. Only dynamically saved skills can be deleted.")
    
    # Find and remove from dynamic skills
    for i, skill in enumerate(_dynamic_skills):
        if skill.get("id") == skill_id:
            _dynamic_skills.pop(i)
            _save_dynamic_skills()
            return True
    
    return False


def get_dynamic_skills() -> List[Dict[str, Any]]:
    """Get only dynamically saved skills."""
    return _dynamic_skills.copy()


def reload_dynamic_skills() -> List[Dict[str, Any]]:
    """Reload dynamic skills from file (useful after external changes)."""
    return _load_dynamic_skills()
