"""Execute plans using Marimo as the engine."""

import time
import asyncio
from typing import Dict, Any, Callable, Iterator, AsyncIterator, Optional, Union

from .events import (
    Event, EventType, Verdict, ExecutionResult,
    start_event, step_start_event, step_complete_event,
    step_skipped_event, error_event, intervention_event, finish_event
)
from .expressions import evaluate_condition, resolve_args


async def execute_plan(
    plan: Dict[str, Any],
    tools: Dict[str, Callable],
    context: Optional[Dict[str, Any]] = None
) -> AsyncIterator[Event]:
    """
    Execute a plan using Marimo-style cell execution.
    
    This is the main entry point for async/streaming execution.
    Yields events as execution progresses.
    
    Args:
        plan: Plan dictionary with steps
        tools: Tool registry mapping names to callables
        context: Optional initial context (will be mutated)
        
    Yields:
        Events as execution progresses
    """
    if context is None:
        context = {}
    
    start_time = time.time()
    steps_completed = 0
    critical_findings = {}
    final_verdict = Verdict.UNKNOWN
    final_error = None
    intervention_reason = None
    
    # Yield START event
    yield start_event(plan.get("id"))
    
    steps = plan.get("steps", [])
    
    for i, step in enumerate(steps):
        step_id = step.get("id")
        tool_name = step.get("tool")
        description = step.get("description", "")
        
        # Validate step
        if not step_id or not tool_name:
            final_verdict = Verdict.FAILURE
            final_error = f"Invalid step at index {i}: missing id or tool"
            yield error_event(f"step_{i}", final_error, f"Step: {step}")
            break
        
        # Yield STEP_START
        yield step_start_event(i, step_id, tool_name, description)
        
        # Check run_if condition
        run_if = step.get("run_if")
        if run_if:
            try:
                should_run = evaluate_condition(run_if, context)
                if not should_run:
                    yield step_skipped_event(step_id, f"Condition not met: {run_if}")
                    continue
            except Exception as e:
                yield step_skipped_event(step_id, f"Condition evaluation error: {e}")
                continue
        
        # Check tool exists
        if tool_name not in tools:
            final_verdict = Verdict.FAILURE
            final_error = f"Tool '{tool_name}' not found in registry"
            yield error_event(step_id, final_error)
            break
        
        try:
            # Resolve arguments
            args = step.get("args", {})
            resolved_args = resolve_args(args, context)
            
            # Execute tool (handle sync/async)
            tool_func = tools[tool_name]
            
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**resolved_args)
            else:
                # Run sync function in executor to not block
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: tool_func(**resolved_args))
            
            # Store result in context
            context[step_id] = result
            steps_completed += 1
            
            # Check for key findings
            if step.get("key_finding"):
                critical_findings[step_id] = result
            
            # Check intervention condition
            intervention_if = step.get("intervention_if")
            if intervention_if:
                try:
                    needs_intervention = evaluate_condition(intervention_if, context)
                    if needs_intervention:
                        final_verdict = Verdict.INTERVENTION_NEEDED
                        intervention_reason = f"Condition met: {intervention_if}"
                        yield intervention_event(step_id, intervention_reason, result)
                        # Continue execution but mark for intervention
                except Exception as e:
                    # Log but don't fail on intervention check error
                    pass
            
            # Yield STEP_COMPLETE
            yield step_complete_event(step_id, result, context)
            
        except Exception as e:
            final_verdict = Verdict.FAILURE
            final_error = str(e)
            yield error_event(step_id, final_error, f"Tool: {tool_name}, Args: {resolved_args}")
            break
    
    # Determine final verdict if not already set
    if final_verdict == Verdict.UNKNOWN:
        final_verdict = Verdict.SUCCESS
    
    duration = round(time.time() - start_time, 3)
    
    # Yield FINISH event
    yield finish_event(
        verdict=final_verdict,
        context=context,
        duration=duration,
        steps_completed=steps_completed,
        critical_findings=critical_findings,
        error=final_error,
        intervention_reason=intervention_reason
    )


def execute_plan_sync(
    plan: Dict[str, Any],
    tools: Dict[str, Callable],
    context: Optional[Dict[str, Any]] = None
) -> ExecutionResult:
    """
    Execute a plan synchronously.
    
    Convenience wrapper that collects all events and returns final result.
    
    Args:
        plan: Plan dictionary with steps
        tools: Tool registry
        context: Optional initial context
        
    Returns:
        ExecutionResult with verdict, outputs, and all events
    """
    if context is None:
        context = {}
    
    events = []
    
    async def collect_events():
        async for event in execute_plan(plan, tools, context):
            events.append(event)
    
    # Run the async generator
    asyncio.run(collect_events())
    
    # Extract final result from FINISH event
    finish = events[-1] if events else None
    
    if finish and finish.type == EventType.FINISH:
        return ExecutionResult(
            verdict=finish.verdict or Verdict.UNKNOWN,
            outputs=finish.final_context or {},
            events=events,
            duration=finish.duration or 0.0,
            steps_completed=finish.steps_completed or 0,
            critical_findings=finish.critical_findings or {},
            error=finish.error,
            intervention_reason=finish.intervention_reason
        )
    
    # Fallback if no finish event
    return ExecutionResult(
        verdict=Verdict.FAILURE,
        outputs=context,
        events=events,
        duration=0.0,
        steps_completed=0,
        critical_findings={},
        error="No FINISH event received"
    )


def stream_execution(
    plan: Dict[str, Any],
    tools: Dict[str, Callable],
    context: Optional[Dict[str, Any]] = None
) -> Iterator[Dict[str, Any]]:
    """
    Execute a plan with synchronous iteration (generator).
    
    Compatibility wrapper for code that expects a sync generator.
    Yields event dictionaries.
    
    Args:
        plan: Plan dictionary
        tools: Tool registry
        context: Optional initial context
        
    Yields:
        Event dictionaries
    """
    if context is None:
        context = {}
    
    events_queue = []
    
    async def collect():
        async for event in execute_plan(plan, tools, context):
            events_queue.append(event)
    
    # Run async and collect
    asyncio.run(collect())
    
    # Yield collected events
    for event in events_queue:
        yield event.model_dump()
