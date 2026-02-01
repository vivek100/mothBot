"""Example tools for testing and demonstration.

These are mock diagnostic tools with configurable delays to simulate
realistic execution times. The delay system can be configured globally
or disabled for testing.
"""

import time
import asyncio
import random
from typing import Dict, Any
from dataclasses import dataclass

from .registry import ToolRegistry, create_registry


# =============================================================================
# Delay Configuration System
# =============================================================================

@dataclass
class DelayConfig:
    """
    Configuration for tool execution delays.
    
    Simulates realistic tool execution times for demo/testing purposes.
    Can be disabled for fast unit tests.
    """
    min_delay: float = 3.0   # Minimum delay in seconds
    max_delay: float = 6.0   # Maximum delay in seconds
    enabled: bool = True     # Set to False for fast tests
    
    def get_delay(self) -> float:
        """Get a random delay within the configured range."""
        if not self.enabled:
            return 0.0
        return random.uniform(self.min_delay, self.max_delay)


# Global delay configuration - modify this to change all tool delays
DELAY_CONFIG = DelayConfig()


def simulate_work(operation_name: str = "operation") -> float:
    """
    Simulate realistic work with configurable delay.
    
    Args:
        operation_name: Name of the operation (for logging)
        
    Returns:
        The actual delay applied in seconds
    """
    delay = DELAY_CONFIG.get_delay()
    if delay > 0:
        print(f"[DELAY] {operation_name}: sleeping for {delay:.2f}s (enabled={DELAY_CONFIG.enabled})")
        time.sleep(delay)
        print(f"[DELAY] {operation_name}: done sleeping")
    else:
        print(f"[DELAY] {operation_name}: no delay (enabled={DELAY_CONFIG.enabled})")
    return delay


async def simulate_work_async(operation_name: str = "operation") -> float:
    """
    Async version of simulate_work.
    
    Args:
        operation_name: Name of the operation (for logging)
        
    Returns:
        The actual delay applied in seconds
    """
    delay = DELAY_CONFIG.get_delay()
    if delay > 0:
        print(f"[DELAY ASYNC] {operation_name}: sleeping for {delay:.2f}s (enabled={DELAY_CONFIG.enabled})")
        await asyncio.sleep(delay)
        print(f"[DELAY ASYNC] {operation_name}: done sleeping")
    else:
        print(f"[DELAY ASYNC] {operation_name}: no delay (enabled={DELAY_CONFIG.enabled})")
    return delay


def set_delay_config(min_delay: float = 1.0, max_delay: float = 3.0, enabled: bool = True):
    """
    Configure the global delay settings.
    
    Args:
        min_delay: Minimum delay in seconds
        max_delay: Maximum delay in seconds
        enabled: Whether delays are enabled
    """
    global DELAY_CONFIG
    DELAY_CONFIG = DelayConfig(min_delay=min_delay, max_delay=max_delay, enabled=enabled)


def disable_delays():
    """Disable all delays (useful for testing)."""
    global DELAY_CONFIG
    DELAY_CONFIG.enabled = False


def enable_delays():
    """Enable delays with current settings."""
    global DELAY_CONFIG
    DELAY_CONFIG.enabled = True


# =============================================================================
# Diagnostic Tools
# =============================================================================

def scan_hull() -> Dict[str, Any]:
    """
    Scan the hull for integrity and breaches.
    
    Returns:
        Dictionary with integrity percentage and breach status
    """
    delay = simulate_work("hull_scan")
    return {
        "integrity": 98,
        "integrity_percent": "98%",
        "breach_detected": False,
        "scan_time": time.time(),
        "execution_delay_ms": int(delay * 1000)
    }


def check_oxygen() -> Dict[str, Any]:
    """
    Check oxygen levels in the atmosphere.
    
    Returns:
        Dictionary with oxygen level and status
    """
    delay = simulate_work("oxygen_check")
    return {
        "level": 14.5,
        "unit": "percent",
        "status": "CRITICAL_LOW",
        "threshold": 18.0,
        "check_time": time.time(),
        "execution_delay_ms": int(delay * 1000)
    }


def analyze_atmosphere(o2_level: float) -> Dict[str, Any]:
    """
    Analyze atmosphere based on oxygen level.
    
    Args:
        o2_level: Oxygen level percentage
        
    Returns:
        Dictionary with recommendation and severity
    """
    delay = simulate_work("atmosphere_analysis")
    
    if o2_level is None:
        return {
            "recommendation": "ERROR",
            "severity": "UNKNOWN",
            "reason": "No oxygen level provided",
            "execution_delay_ms": int(delay * 1000)
        }
    
    if o2_level < 15:
        return {
            "recommendation": "EVACUATE",
            "severity": "HIGH",
            "reason": f"Oxygen level {o2_level}% is below safe threshold (15%)",
            "analysis_time": time.time(),
            "execution_delay_ms": int(delay * 1000)
        }
    elif o2_level < 18:
        return {
            "recommendation": "ALERT",
            "severity": "MEDIUM",
            "reason": f"Oxygen level {o2_level}% is below optimal (18%)",
            "analysis_time": time.time(),
            "execution_delay_ms": int(delay * 1000)
        }
    else:
        return {
            "recommendation": "MONITOR",
            "severity": "LOW",
            "reason": f"Oxygen level {o2_level}% is within acceptable range",
            "analysis_time": time.time(),
            "execution_delay_ms": int(delay * 1000)
        }


async def async_scan_systems() -> Dict[str, Any]:
    """
    Async system scan (demonstrates async tool support).
    
    Returns:
        Dictionary with system status
    """
    delay = await simulate_work_async("systems_scan")
    return {
        "power": "NOMINAL",
        "navigation": "ONLINE",
        "life_support": "DEGRADED",
        "communications": "ONLINE",
        "scan_time": time.time(),
        "execution_delay_ms": int(delay * 1000)
    }


def check_temperature(zone: str = "main") -> Dict[str, Any]:
    """
    Check temperature in a specific zone.
    
    Args:
        zone: Zone to check (main, engine, cargo)
        
    Returns:
        Dictionary with temperature data
    """
    delay = simulate_work("temperature_check")
    
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
        "status": "NORMAL" if 15 < temp < 35 else "WARNING",
        "execution_delay_ms": int(delay * 1000)
    }


def generate_report(findings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a summary report from findings.
    
    Args:
        findings: Dictionary of findings to summarize
        
    Returns:
        Summary report
    """
    delay = simulate_work("report_generation")
    
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
        "report_time": time.time(),
        "execution_delay_ms": int(delay * 1000)
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


# =============================================================================
# Tool Metadata for Agent
# =============================================================================

def get_tool_descriptions() -> Dict[str, Dict[str, Any]]:
    """
    Get detailed descriptions of all tools for agent guidance.
    
    Returns:
        Dictionary mapping tool names to their metadata
    """
    return {
        "scan_hull": {
            "name": "scan_hull",
            "description": "Scan the hull for structural integrity and detect breaches",
            "parameters": [],
            "returns": "integrity percentage, breach status",
            "use_when": "Need to check structural integrity or suspect hull damage",
            "typical_delay": "3-6 seconds"
        },
        "check_oxygen": {
            "name": "check_oxygen",
            "description": "Check atmospheric oxygen levels",
            "parameters": [],
            "returns": "oxygen level %, status (NORMAL/CRITICAL_LOW), threshold",
            "use_when": "Need to verify life support or air quality",
            "typical_delay": "3-6 seconds"
        },
        "analyze_atmosphere": {
            "name": "analyze_atmosphere",
            "description": "Analyze atmosphere and provide recommendations based on oxygen level",
            "parameters": [{"name": "o2_level", "type": "float", "required": True}],
            "returns": "recommendation (MONITOR/ALERT/EVACUATE), severity, reason",
            "use_when": "After checking oxygen, need actionable recommendations",
            "depends_on": "check_oxygen (use $step_id.level as o2_level)",
            "typical_delay": "3-6 seconds"
        },
        "check_temperature": {
            "name": "check_temperature",
            "description": "Check temperature in a specific zone",
            "parameters": [{"name": "zone", "type": "string", "options": ["main", "engine", "cargo"]}],
            "returns": "temperature in celsius, status",
            "use_when": "Need to check environmental conditions in specific areas",
            "typical_delay": "3-6 seconds"
        },
        "async_scan_systems": {
            "name": "async_scan_systems",
            "description": "Comprehensive scan of all major systems",
            "parameters": [],
            "returns": "status of power, navigation, life_support, communications",
            "use_when": "Need quick overview of all systems",
            "typical_delay": "3-6 seconds"
        },
        "generate_report": {
            "name": "generate_report",
            "description": "Generate summary report from collected findings",
            "parameters": [{"name": "findings", "type": "dict", "required": True}],
            "returns": "overall status, severity counts, total findings",
            "use_when": "After running multiple checks, need consolidated summary",
            "typical_delay": "3-6 seconds"
        }
    }
