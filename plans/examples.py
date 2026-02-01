"""Example execution plans for testing."""

from typing import Dict, Any, List


def get_test_plan() -> Dict[str, Any]:
    """
    Get the main test plan (diagnostic sequence).
    
    This plan demonstrates:
    - Sequential execution
    - Argument passing between steps ($s2.level)
    - Key findings marking
    - Intervention conditions
    
    Returns:
        Plan dictionary
    """
    return {
        "id": "diagnostic_sequence",
        "name": "Diagnostic Sequence",
        "description": "Standard diagnostic sequence for system health check",
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
    Get a plan with conditional execution.
    
    Demonstrates run_if conditions.
    
    Returns:
        Plan dictionary
    """
    return {
        "id": "conditional_plan",
        "name": "Conditional Execution",
        "description": "Plan with conditional step execution",
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
    Get a plan that triggers intervention.
    
    Demonstrates INTERVENTION_NEEDED verdict.
    
    Returns:
        Plan dictionary
    """
    return {
        "id": "intervention_plan",
        "name": "Intervention Test",
        "description": "Plan that triggers human intervention",
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
    Get a plan with async tools.
    
    Demonstrates async tool execution.
    
    Returns:
        Plan dictionary
    """
    return {
        "id": "async_plan",
        "name": "Async Tools Test",
        "description": "Plan using async tools",
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
    Get a complex plan with multiple features.
    
    Demonstrates:
    - Multiple steps
    - Dependencies
    - Conditions
    - Key findings
    - Report generation
    
    Returns:
        Plan dictionary
    """
    return {
        "id": "complex_plan",
        "name": "Full System Diagnostic",
        "description": "Comprehensive system diagnostic with report",
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


def get_example_plans() -> List[Dict[str, Any]]:
    """
    Get all example plans.
    
    Returns:
        List of plan dictionaries
    """
    return [
        get_test_plan(),
        get_conditional_plan(),
        get_intervention_plan(),
        get_async_plan(),
        get_complex_plan(),
    ]


def get_plan_by_id(plan_id: str) -> Dict[str, Any]:
    """
    Get a plan by its ID.
    
    Args:
        plan_id: Plan identifier
        
    Returns:
        Plan dictionary
        
    Raises:
        ValueError: If plan not found
    """
    plans = {p["id"]: p for p in get_example_plans()}
    
    if plan_id not in plans:
        available = ", ".join(plans.keys())
        raise ValueError(f"Plan '{plan_id}' not found. Available: {available}")
    
    return plans[plan_id]
