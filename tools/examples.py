"""Example tools for testing and demonstration."""

import time
import asyncio
from typing import Dict, Any

from .registry import ToolRegistry, create_registry


def scan_hull() -> Dict[str, Any]:
    """
    Scan the hull for integrity and breaches.
    
    Returns:
        Dictionary with integrity percentage and breach status
    """
    time.sleep(0.3)  # Simulate work
    return {
        "integrity": 98,
        "integrity_percent": "98%",
        "breach_detected": False,
        "scan_time": time.time()
    }


def check_oxygen() -> Dict[str, Any]:
    """
    Check oxygen levels in the atmosphere.
    
    Returns:
        Dictionary with oxygen level and status
    """
    time.sleep(0.3)  # Simulate work
    return {
        "level": 14.5,
        "unit": "percent",
        "status": "CRITICAL_LOW",
        "threshold": 18.0,
        "check_time": time.time()
    }


def analyze_atmosphere(o2_level: float) -> Dict[str, Any]:
    """
    Analyze atmosphere based on oxygen level.
    
    Args:
        o2_level: Oxygen level percentage
        
    Returns:
        Dictionary with recommendation and severity
    """
    time.sleep(0.3)  # Simulate work
    
    if o2_level is None:
        return {
            "recommendation": "ERROR",
            "severity": "UNKNOWN",
            "reason": "No oxygen level provided"
        }
    
    if o2_level < 15:
        return {
            "recommendation": "EVACUATE",
            "severity": "HIGH",
            "reason": f"Oxygen level {o2_level}% is below safe threshold (15%)",
            "analysis_time": time.time()
        }
    elif o2_level < 18:
        return {
            "recommendation": "ALERT",
            "severity": "MEDIUM",
            "reason": f"Oxygen level {o2_level}% is below optimal (18%)",
            "analysis_time": time.time()
        }
    else:
        return {
            "recommendation": "MONITOR",
            "severity": "LOW",
            "reason": f"Oxygen level {o2_level}% is within acceptable range",
            "analysis_time": time.time()
        }


async def async_scan_systems() -> Dict[str, Any]:
    """
    Async system scan (demonstrates async tool support).
    
    Returns:
        Dictionary with system status
    """
    await asyncio.sleep(0.2)  # Simulate async work
    return {
        "power": "NOMINAL",
        "navigation": "ONLINE",
        "life_support": "DEGRADED",
        "communications": "ONLINE",
        "scan_time": time.time()
    }


def check_temperature(zone: str = "main") -> Dict[str, Any]:
    """
    Check temperature in a specific zone.
    
    Args:
        zone: Zone to check (main, engine, cargo)
        
    Returns:
        Dictionary with temperature data
    """
    time.sleep(0.2)
    
    temps = {
        "main": 22.5,
        "engine": 45.0,
        "cargo": 18.0
    }
    
    temp = temps.get(zone, 20.0)
    
    return {
        "zone": zone,
        "temperature": temp,
        "unit": "celsius",
        "status": "NORMAL" if 15 < temp < 35 else "WARNING"
    }


def generate_report(findings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a summary report from findings.
    
    Args:
        findings: Dictionary of findings to summarize
        
    Returns:
        Summary report
    """
    time.sleep(0.2)
    
    # Count severity levels
    severities = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    
    if isinstance(findings, dict):
        for key, value in findings.items():
            if isinstance(value, dict) and "severity" in value:
                sev = value.get("severity", "LOW")
                if sev in severities:
                    severities[sev] += 1
    
    overall = "CRITICAL" if severities["HIGH"] > 0 else \
              "WARNING" if severities["MEDIUM"] > 0 else "OK"
    
    return {
        "overall_status": overall,
        "severity_counts": severities,
        "total_findings": sum(severities.values()),
        "report_time": time.time()
    }


def get_example_tools() -> Dict[str, Any]:
    """
    Get a dictionary of example tools.
    
    Returns:
        Dictionary mapping tool names to callables
    """
    return {
        "scan_hull": scan_hull,
        "check_oxygen": check_oxygen,
        "analyze_atmosphere": analyze_atmosphere,
        "async_scan_systems": async_scan_systems,
        "check_temperature": check_temperature,
        "generate_report": generate_report,
    }


def get_example_registry() -> ToolRegistry:
    """
    Get a ToolRegistry with example tools.
    
    Returns:
        ToolRegistry with all example tools registered
    """
    return create_registry(
        scan_hull,
        check_oxygen,
        analyze_atmosphere,
        async_scan_systems,
        check_temperature,
        generate_report,
    )
