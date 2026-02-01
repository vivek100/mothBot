"""
Marimo app for Streaming Chain Engine.

A clean, simple implementation using Marimo's reactive model.
"""

import marimo

__generated_with = "0.19.7"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    """Import engine components."""
    from core.executor import execute_plan
    from tools.examples import get_example_tools
    from plans.examples import get_example_plans

    # Initialize
    registry = get_example_tools()
    plans = get_example_plans()
    plan_names = {p["name"]: p for p in plans}

    return plan_names, registry, execute_plan, get_example_plans, get_example_tools, plans


@app.cell
def _(mo, plan_names):
    """Create the configuration form."""

    # Plan selector
    plan_dropdown = mo.ui.dropdown(
        options=list(plan_names.keys()),
        value=list(plan_names.keys())[0],
        label="Select Plan"
    )

    # Options
    verbose_checkbox = mo.ui.checkbox(label="Verbose output")

    # Run button
    run_button = mo.ui.run_button(label="🚀 Run Plan")

    # Display form
    mo.vstack([
        mo.md("## 🚀 Plan Configuration"),
        plan_dropdown,
        verbose_checkbox,
        run_button
    ])

    return plan_dropdown, run_button, verbose_checkbox


@app.cell
async def _(
    mo,
    run_button,
    plan_dropdown,
    plan_names,
    registry,
    execute_plan,
    verbose_checkbox,
):
    """Execute the plan and stream output when button is clicked."""
    
    # Gate execution - stop if button not clicked
    mo.stop(not run_button.value, mo.md("👆 **Click 'Run Plan' to start execution**"))

    # Get selected plan
    selected_plan = plan_names[plan_dropdown.value]
    verbose = verbose_checkbox.value

    # Execute and collect results
    context = {}
    events = []
    final_report = None

    mo.output.append(mo.md("### 📟 Live Terminal"))
    mo.output.append(mo.md("---"))

    # Use async execute_plan directly
    async for event in execute_plan(selected_plan, registry, context):
        # Convert event to dict if it's a Pydantic model
        if hasattr(event, "model_dump"):
            event_dict = event.model_dump()
        else:
            event_dict = event
        
        events.append(event_dict)
        event_type = str(event_dict.get("type", "UNKNOWN"))

        # Remove enum prefix if present
        if "." in event_type:
            event_type = event_type.split(".")[-1]

        msg = event_dict.get("msg", "")

        if event_type == "START":
            mo.output.append(mo.md(f"**{msg}**"))
        elif event_type == "STEP_START":
            step_idx = event_dict.get("step_index", 0) + 1
            mo.output.append(mo.md(f"**Step {step_idx}:** {msg}"))
        elif event_type == "STEP_COMPLETE":
            step_id = event_dict.get("step_id", "")
            mo.output.append(mo.md(f"  ✅ `{step_id}` completed"))
            if verbose:
                mo.output.append(mo.json(event_dict.get("output", {})))
            context = event_dict.get("context_snapshot", context)
        elif event_type == "ERROR":
            mo.output.append(mo.callout(mo.md(f"**Error:** {msg}"), kind="danger"))
        elif event_type == "FINISH":
            mo.output.append(mo.md(f"**{msg}**"))
            # Extract report data from FINISH event
            final_report = {
                "verdict": event_dict.get("verdict", "UNKNOWN"),
                "duration": event_dict.get("duration", 0),
                "steps_completed": event_dict.get("steps_completed", 0),
                "critical_findings": event_dict.get("critical_findings", {}),
                "error": event_dict.get("error"),
                "intervention_reason": event_dict.get("intervention_reason")
            }
            context = event_dict.get("final_context", context)

    mo.output.append(mo.md("---"))
    
    # Display report inline
    if final_report:
        verdict = final_report.get("verdict", "UNKNOWN")
        # Convert enum to string if needed
        if hasattr(verdict, "value"):
            verdict = verdict.value
        verdict_str = str(verdict)
        
        duration = final_report.get("duration", 0)
        steps = final_report.get("steps_completed", 0)
        findings = final_report.get("critical_findings", {})

        if verdict_str == "SUCCESS":
            verdict_display = mo.md(f"### 🟢 {verdict_str}")
        elif verdict_str == "INTERVENTION_NEEDED":
            verdict_display = mo.md(f"### 🟡 {verdict_str}")
        else:
            verdict_display = mo.md(f"### 🔴 {verdict_str}")

        mo.output.append(mo.md("## 📋 Mission Report"))
        mo.output.append(verdict_display)
        mo.output.append(mo.md(f"**Duration:** {duration:.2f}s | **Steps:** {steps}"))
        mo.output.append(mo.md("### Critical Findings:"))
        mo.output.append(mo.json(findings) if findings else mo.md("_No critical findings_"))
        mo.output.append(mo.md("### Final Context:"))
        mo.output.append(mo.json(context))

    return context, final_report


if __name__ == "__main__":
    app.run()
