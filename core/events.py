"""Event types and schemas for the Marimo Chain Engine."""

from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class EventType(str, Enum):
    """Event types emitted during plan execution."""
    START = "START"
    STEP_START = "STEP_START"
    STEP_COMPLETE = "STEP_COMPLETE"
    STEP_SKIPPED = "STEP_SKIPPED"
    TOOL_LOG = "TOOL_LOG"
    ERROR = "ERROR"
    INTERVENTION_NEEDED = "INTERVENTION_NEEDED"
    FINISH = "FINISH"


class Verdict(str, Enum):
    """Final execution verdicts."""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    INTERVENTION_NEEDED = "INTERVENTION_NEEDED"
    UNKNOWN = "UNKNOWN"


class Event(BaseModel):
    """Base event emitted during execution."""
    
    model_config = ConfigDict(extra="forbid")
    
    type: EventType = Field(..., description="Event type")
    msg: Optional[str] = Field(None, description="Human-readable message")
    
    # START event fields
    plan_id: Optional[str] = Field(None, description="Plan identifier")
    
    # STEP_START fields
    step_index: Optional[int] = Field(None, description="Step index (0-based)")
    step_id: Optional[str] = Field(None, description="Step identifier")
    tool: Optional[str] = Field(None, description="Tool being executed")
    
    # STEP_COMPLETE fields
    output: Optional[Dict[str, Any]] = Field(None, description="Step output")
    context_snapshot: Optional[Dict[str, Any]] = Field(None, description="Current context")
    
    # ERROR fields
    error: Optional[str] = Field(None, description="Error message")
    details: Optional[str] = Field(None, description="Error details")
    
    # INTERVENTION_NEEDED fields
    intervention_reason: Optional[str] = Field(None, description="Why intervention is needed")
    
    # FINISH fields
    verdict: Optional[Verdict] = Field(None, description="Final verdict")
    final_context: Optional[Dict[str, Any]] = Field(None, description="Final execution context")
    duration: Optional[float] = Field(None, description="Execution duration in seconds")
    steps_completed: Optional[int] = Field(None, description="Number of steps completed")
    critical_findings: Optional[Dict[str, Any]] = Field(None, description="Key findings from execution")


class ExecutionResult(BaseModel):
    """Final result of plan execution."""
    
    model_config = ConfigDict(extra="forbid")
    
    verdict: Verdict = Field(..., description="Final verdict")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="All step outputs")
    events: List[Event] = Field(default_factory=list, description="All events that occurred")
    duration: float = Field(..., description="Total execution time in seconds")
    steps_completed: int = Field(default=0, description="Number of steps completed")
    critical_findings: Dict[str, Any] = Field(default_factory=dict, description="Key findings")
    error: Optional[str] = Field(None, description="Error message if failed")
    intervention_reason: Optional[str] = Field(None, description="Intervention reason if needed")


# Factory functions for creating events
def start_event(plan_id: Optional[str] = None) -> Event:
    """Create a START event."""
    return Event(
        type=EventType.START,
        msg="Initializing execution...",
        plan_id=plan_id
    )


def step_start_event(step_index: int, step_id: str, tool: str, description: str = "") -> Event:
    """Create a STEP_START event."""
    return Event(
        type=EventType.STEP_START,
        msg=f"Running {tool}... {description}".strip(),
        step_index=step_index,
        step_id=step_id,
        tool=tool
    )


def step_complete_event(step_id: str, output: Dict[str, Any], context: Dict[str, Any]) -> Event:
    """Create a STEP_COMPLETE event."""
    return Event(
        type=EventType.STEP_COMPLETE,
        msg=f"Completed {step_id}",
        step_id=step_id,
        output=output,
        context_snapshot=context.copy()
    )


def step_skipped_event(step_id: str, reason: str) -> Event:
    """Create a STEP_SKIPPED event."""
    return Event(
        type=EventType.STEP_SKIPPED,
        msg=f"Skipped {step_id}: {reason}",
        step_id=step_id
    )


def error_event(step_id: str, error: str, details: Optional[str] = None) -> Event:
    """Create an ERROR event."""
    return Event(
        type=EventType.ERROR,
        msg=f"Error at {step_id}: {error}",
        step_id=step_id,
        error=error,
        details=details
    )


def intervention_event(step_id: str, reason: str, output: Dict[str, Any]) -> Event:
    """Create an INTERVENTION_NEEDED event."""
    return Event(
        type=EventType.INTERVENTION_NEEDED,
        msg=f"Intervention needed at {step_id}: {reason}",
        step_id=step_id,
        intervention_reason=reason,
        output=output
    )


def finish_event(
    verdict: Verdict,
    context: Dict[str, Any],
    duration: float,
    steps_completed: int,
    critical_findings: Dict[str, Any],
    error: Optional[str] = None,
    intervention_reason: Optional[str] = None
) -> Event:
    """Create a FINISH event."""
    msg = {
        Verdict.SUCCESS: "Execution completed successfully",
        Verdict.FAILURE: f"Execution failed: {error}",
        Verdict.INTERVENTION_NEEDED: f"Intervention required: {intervention_reason}",
        Verdict.UNKNOWN: "Execution ended with unknown status"
    }.get(verdict, "Execution ended")
    
    return Event(
        type=EventType.FINISH,
        msg=msg,
        verdict=verdict,
        final_context=context.copy(),
        duration=duration,
        steps_completed=steps_completed,
        critical_findings=critical_findings,
        error=error,
        intervention_reason=intervention_reason
    )
