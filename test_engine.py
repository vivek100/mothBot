"""Tests for the Marimo Chain Engine."""

import asyncio
from marimo_engine import (
    execute_plan,
    execute_plan_sync,
    EventType,
    Verdict,
)
from marimo_engine.tools import get_example_tools
from marimo_engine.plans import get_test_plan, get_example_plans, validate_plan
from marimo_engine.core.expressions import (
    resolve_reference,
    evaluate_condition,
    resolve_args,
)


def test_resolve_reference():
    """Test reference resolution."""
    print("Testing reference resolution...")
    
    context = {
        "s1": {"value": 10, "status": "OK"},
        "s2": {"level": 14.5, "data": {"nested": 42}},
    }
    
    # Simple reference
    assert resolve_reference("$s1", context) == {"value": 10, "status": "OK"}
    
    # Nested reference
    assert resolve_reference("$s1.value", context) == 10
    assert resolve_reference("$s2.level", context) == 14.5
    assert resolve_reference("$s2.data.nested", context) == 42
    
    # Missing reference
    assert resolve_reference("$missing", context) is None
    assert resolve_reference("$s1.missing", context) is None
    
    # Non-reference
    assert resolve_reference("plain", context) == "plain"
    
    print("  Reference resolution tests passed")


def test_evaluate_condition():
    """Test condition evaluation."""
    print("\nTesting condition evaluation...")
    
    context = {
        "s1": {"value": 10, "flag": True, "status": "OK"},
        "s2": {"level": 14.5, "severity": "HIGH"},
    }
    
    # Simple truthy check
    assert evaluate_condition("$s1.flag", context) is True
    assert evaluate_condition("$s1.missing", context) is False
    
    # Comparisons
    assert evaluate_condition("$s1.value > 5", context) is True
    assert evaluate_condition("$s1.value < 5", context) is False
    assert evaluate_condition("$s2.level < 15", context) is True
    
    # Equality
    assert evaluate_condition("$s1.status == 'OK'", context) is True
    assert evaluate_condition("$s2.severity == 'HIGH'", context) is True
    assert evaluate_condition("$s1.flag == True", context) is True
    
    # Boolean operators
    assert evaluate_condition("$s1.value > 5 and $s2.level < 15", context) is True
    assert evaluate_condition("$s1.value > 20 or $s2.level < 15", context) is True
    assert evaluate_condition("$s1.value > 20 and $s2.level < 15", context) is False
    
    print("  Condition evaluation tests passed")


def test_resolve_args():
    """Test argument resolution."""
    print("\nTesting argument resolution...")
    
    context = {
        "s1": {"value": 10},
        "s2": {"level": 14.5},
    }
    
    args = {
        "plain": "hello",
        "ref": "$s1.value",
        "nested_ref": "$s2.level",
    }
    
    resolved = resolve_args(args, context)
    
    assert resolved["plain"] == "hello"
    assert resolved["ref"] == 10
    assert resolved["nested_ref"] == 14.5
    
    print("  Argument resolution tests passed")


def test_plan_validation():
    """Test plan validation."""
    print("\nTesting plan validation...")
    
    # Valid plan
    plan = get_test_plan()
    validated = validate_plan(plan)
    assert validated.id == "diagnostic_sequence"
    assert len(validated.steps) == 3
    
    # Invalid plan (no steps)
    try:
        validate_plan({"steps": []})
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    # Invalid plan (duplicate IDs)
    try:
        validate_plan({
            "steps": [
                {"id": "s1", "tool": "test"},
                {"id": "s1", "tool": "test2"},
            ]
        })
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    print("  Plan validation tests passed")


def test_sync_execution():
    """Test synchronous execution."""
    print("\nTesting sync execution...")
    
    plan = get_test_plan()
    tools = get_example_tools()
    
    result = execute_plan_sync(plan, tools)
    
    # Check verdict
    # Note: May be INTERVENTION_NEEDED due to low oxygen
    assert result.verdict in [Verdict.SUCCESS, Verdict.INTERVENTION_NEEDED]
    
    # Check outputs
    assert "s1" in result.outputs
    assert "s2" in result.outputs
    assert "s3" in result.outputs
    
    # Check s3 used s2's oxygen level
    assert result.outputs["s3"]["recommendation"] == "EVACUATE"  # Because o2 < 15
    
    # Check events
    assert len(result.events) > 0
    assert result.events[0].type == EventType.START
    assert result.events[-1].type == EventType.FINISH
    
    print(f"  Verdict: {result.verdict}")
    print(f"  Steps completed: {result.steps_completed}")
    print(f"  Duration: {result.duration:.3f}s")
    print("  Sync execution tests passed")


async def test_async_execution():
    """Test async streaming execution."""
    print("\nTesting async execution...")
    
    plan = get_test_plan()
    tools = get_example_tools()
    
    events = []
    async for event in execute_plan(plan, tools):
        events.append(event)
        print(f"    [{event.type.value}] {event.msg}")
    
    # Verify event sequence
    assert events[0].type == EventType.START
    assert events[-1].type == EventType.FINISH
    
    # Count step events
    step_starts = [e for e in events if e.type == EventType.STEP_START]
    step_completes = [e for e in events if e.type == EventType.STEP_COMPLETE]
    
    assert len(step_starts) == 3
    assert len(step_completes) == 3
    
    print("  Async execution tests passed")


def test_conditional_execution():
    """Test conditional step execution."""
    print("\nTesting conditional execution...")
    
    plan = {
        "id": "conditional_test",
        "steps": [
            {"id": "s1", "tool": "scan_hull"},
            {
                "id": "s2",
                "tool": "check_oxygen",
                "run_if": "$s1.breach_detected == True"  # Will be False
            },
            {"id": "s3", "tool": "check_oxygen"}  # Always runs
        ]
    }
    
    tools = get_example_tools()
    result = execute_plan_sync(plan, tools)
    
    # s2 should be skipped (breach_detected is False)
    assert "s1" in result.outputs
    assert "s2" not in result.outputs  # Skipped
    assert "s3" in result.outputs
    
    # Check for skip event
    skip_events = [e for e in result.events if e.type == EventType.STEP_SKIPPED]
    assert len(skip_events) == 1
    assert skip_events[0].step_id == "s2"
    
    print("  Conditional execution tests passed")


def test_intervention():
    """Test intervention triggering."""
    print("\nTesting intervention...")
    
    plan = {
        "id": "intervention_test",
        "steps": [
            {
                "id": "s1",
                "tool": "check_oxygen",
                "intervention_if": "$s1.level < 15"  # Will trigger
            }
        ]
    }
    
    tools = get_example_tools()
    result = execute_plan_sync(plan, tools)
    
    # Should trigger intervention
    assert result.verdict == Verdict.INTERVENTION_NEEDED
    assert result.intervention_reason is not None
    
    # Check for intervention event
    intervention_events = [e for e in result.events if e.type == EventType.INTERVENTION_NEEDED]
    assert len(intervention_events) == 1
    
    print(f"  Intervention reason: {result.intervention_reason}")
    print("  Intervention tests passed")


def test_all_example_plans():
    """Test all example plans execute."""
    print("\nTesting all example plans...")
    
    plans = get_example_plans()
    tools = get_example_tools()
    
    for plan in plans:
        plan_name = plan.get("name", plan.get("id", "unknown"))
        print(f"  Running: {plan_name}")
        
        result = execute_plan_sync(plan, tools)
        
        # Should complete (SUCCESS or INTERVENTION_NEEDED)
        assert result.verdict in [Verdict.SUCCESS, Verdict.INTERVENTION_NEEDED], \
            f"Plan {plan_name} failed: {result.error}"
        
        print(f"    Verdict: {result.verdict.value}, Steps: {result.steps_completed}")
    
    print("  All example plans passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Marimo Chain Engine Tests")
    print("=" * 60)
    
    test_resolve_reference()
    test_evaluate_condition()
    test_resolve_args()
    test_plan_validation()
    test_sync_execution()
    asyncio.run(test_async_execution())
    test_conditional_execution()
    test_intervention()
    test_all_example_plans()
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
