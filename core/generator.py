"""Generate Marimo notebook cells from JSON plan."""

import textwrap
from typing import Dict, Any, List, Callable, Optional, Set
from dataclasses import dataclass, field

from .expressions import resolve_reference


@dataclass
class CellDefinition:
    """Definition of a Marimo cell to be generated."""
    
    name: str  # Cell function name (step_id)
    code: str  # Python code to execute
    dependencies: Set[str] = field(default_factory=set)  # Other cell names this depends on
    returns: List[str] = field(default_factory=list)  # Variables to return
    
    def to_function_code(self) -> str:
        """Generate the cell function code."""
        # Build function signature with dependencies
        deps = sorted(self.dependencies)
        args = ", ".join(deps) if deps else ""
        
        # Indent the code
        indented_code = textwrap.indent(self.code, "    ")
        
        # Build return statement
        if self.returns:
            return_stmt = f"    return ({', '.join(self.returns)},)"
        else:
            return_stmt = "    return ()"
        
        return f"""def {self.name}({args}):
{indented_code}
{return_stmt}
"""


def extract_dependencies(args: Dict[str, Any]) -> Set[str]:
    """
    Extract step dependencies from arguments.
    
    Args:
        args: Dictionary of arguments with potential $references
        
    Returns:
        Set of step IDs that are referenced
    """
    deps = set()
    
    def find_refs(value: Any):
        if isinstance(value, str) and value.startswith("$"):
            # Extract step ID from reference like "$s2.level"
            step_id = value[1:].split(".")[0]
            deps.add(step_id)
        elif isinstance(value, dict):
            for v in value.values():
                find_refs(v)
        elif isinstance(value, list):
            for v in value:
                find_refs(v)
    
    find_refs(args)
    return deps


def extract_condition_dependencies(condition: str) -> Set[str]:
    """
    Extract step dependencies from a condition expression.
    
    Args:
        condition: Condition string like "$s1.value > 10"
        
    Returns:
        Set of step IDs referenced in the condition
    """
    import re
    deps = set()
    
    # Find all $references
    pattern = r'\$([a-zA-Z_][a-zA-Z0-9_]*)'
    matches = re.findall(pattern, condition)
    deps.update(matches)
    
    return deps


def generate_step_code(
    step: Dict[str, Any],
    tool_var: str = "_tools"
) -> str:
    """
    Generate Python code for a single step.
    
    Args:
        step: Step definition
        tool_var: Variable name for tools dict
        
    Returns:
        Python code string
    """
    step_id = step["id"]
    tool_name = step["tool"]
    args = step.get("args", {})
    run_if = step.get("run_if")
    intervention_if = step.get("intervention_if")
    
    lines = []
    
    # Add condition check if run_if specified
    if run_if:
        lines.append(f"# Conditional execution")
        lines.append(f"_condition = evaluate_condition({repr(run_if)}, _context)")
        lines.append(f"if not _condition:")
        lines.append(f"    _result = {{'_skipped': True, '_reason': 'Condition not met: {run_if}'}}")
        lines.append(f"else:")
        # Indent the rest
        indent = "    "
    else:
        indent = ""
    
    # Resolve arguments
    if args:
        lines.append(f"{indent}# Resolve arguments")
        lines.append(f"{indent}_args = resolve_args({repr(args)}, _context)")
    else:
        lines.append(f"{indent}_args = {{}}")
    
    # Execute tool
    lines.append(f"{indent}# Execute tool")
    lines.append(f"{indent}_tool = {tool_var}[{repr(tool_name)}]")
    lines.append(f"{indent}")
    lines.append(f"{indent}# Handle sync/async tools")
    lines.append(f"{indent}import asyncio")
    lines.append(f"{indent}if asyncio.iscoroutinefunction(_tool):")
    lines.append(f"{indent}    _result = asyncio.get_event_loop().run_until_complete(_tool(**_args))")
    lines.append(f"{indent}else:")
    lines.append(f"{indent}    _result = _tool(**_args)")
    
    # Check intervention condition
    if intervention_if:
        lines.append(f"")
        lines.append(f"# Check intervention condition")
        lines.append(f"_context[{repr(step_id)}] = _result  # Update context for condition check")
        lines.append(f"if evaluate_condition({repr(intervention_if)}, _context):")
        lines.append(f"    _result['_intervention_needed'] = True")
        lines.append(f"    _result['_intervention_reason'] = {repr(intervention_if)}")
    
    # Store result
    lines.append(f"")
    lines.append(f"# Store in context")
    lines.append(f"_context[{repr(step_id)}] = _result")
    lines.append(f"{step_id} = _result")
    
    return "\n".join(lines)


def generate_cells(
    plan: Dict[str, Any],
    tools: Dict[str, Callable]
) -> List[CellDefinition]:
    """
    Generate Marimo cell definitions from a plan.
    
    Args:
        plan: Plan dictionary with steps
        tools: Tool registry
        
    Returns:
        List of CellDefinition objects
    """
    cells = []
    steps = plan.get("steps", [])
    
    # Create setup cell
    setup_code = """# Setup
from marimo_engine.core.expressions import evaluate_condition, resolve_args

_context = {}
"""
    cells.append(CellDefinition(
        name="_setup",
        code=setup_code,
        dependencies=set(),
        returns=["_context"]
    ))
    
    # Create cell for each step
    for i, step in enumerate(steps):
        step_id = step["id"]
        
        # Find dependencies
        deps = {"_context"}  # Always depends on context
        
        # Add dependencies from args
        if "args" in step:
            arg_deps = extract_dependencies(step["args"])
            deps.update(arg_deps)
        
        # Add dependencies from conditions
        if "run_if" in step:
            cond_deps = extract_condition_dependencies(step["run_if"])
            deps.update(cond_deps)
        
        if "intervention_if" in step:
            cond_deps = extract_condition_dependencies(step["intervention_if"])
            deps.update(cond_deps)
        
        # Generate code
        code = generate_step_code(step)
        
        cells.append(CellDefinition(
            name=step_id,
            code=code,
            dependencies=deps,
            returns=[step_id]
        ))
    
    # Create final results cell
    step_ids = [s["id"] for s in steps]
    final_code = f"""# Collect results
_outputs = {{}}
for _sid in {repr(step_ids)}:
    if _sid in _context:
        _outputs[_sid] = _context[_sid]

_final_result = {{
    "outputs": _outputs,
    "context": _context
}}
"""
    cells.append(CellDefinition(
        name="_final",
        code=final_code,
        dependencies={"_context"} | set(step_ids),
        returns=["_final_result"]
    ))
    
    return cells


def generate_notebook_code(
    plan: Dict[str, Any],
    tools: Dict[str, Callable]
) -> str:
    """
    Generate complete Marimo notebook code from a plan.
    
    Args:
        plan: Plan dictionary
        tools: Tool registry
        
    Returns:
        Complete Python code for a Marimo notebook
    """
    cells = generate_cells(plan, tools)
    
    # Build notebook code
    lines = [
        '"""Generated Marimo notebook for plan execution."""',
        "",
        "import marimo",
        "",
        '__generated_with = "0.19.7"',
        "app = marimo.App()",
        "",
    ]
    
    # Add each cell
    for cell in cells:
        lines.append("@app.cell")
        lines.append(cell.to_function_code())
        lines.append("")
    
    # Add main block
    lines.append('if __name__ == "__main__":')
    lines.append("    app.run()")
    
    return "\n".join(lines)
