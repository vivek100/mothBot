"""Safe expression evaluation for run_if and intervention_if conditions."""

import re
import operator
from typing import Any, Dict, Optional


# Allowed operators for safe evaluation
OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
}

# Pattern to match $references like $s1.value or $s2.data.nested
REFERENCE_PATTERN = re.compile(r'\$([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)')


def resolve_reference(ref: str, context: Dict[str, Any]) -> Any:
    """
    Resolve a $reference to its value in context.
    
    Examples:
        - "$s1" -> context["s1"]
        - "$s2.level" -> context["s2"]["level"]
        - "$s3.data.nested.value" -> context["s3"]["data"]["nested"]["value"]
    
    Args:
        ref: Reference string starting with $
        context: Execution context with step outputs
        
    Returns:
        Resolved value, or None if not found
    """
    if not ref.startswith("$"):
        return ref
    
    # Remove $ and split path
    path = ref[1:].split(".")
    
    # Get base value
    data = context.get(path[0])
    if data is None:
        return None
    
    # Traverse nested path
    for key in path[1:]:
        if isinstance(data, dict):
            data = data.get(key)
            if data is None:
                return None
        else:
            return None
    
    return data


def resolve_all_references(expr: str, context: Dict[str, Any]) -> str:
    """
    Replace all $references in an expression with their values.
    
    Args:
        expr: Expression string with $references
        context: Execution context
        
    Returns:
        Expression with references replaced by values
    """
    def replace_ref(match: re.Match) -> str:
        ref = "$" + match.group(1)
        value = resolve_reference(ref, context)
        
        if value is None:
            return "None"
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, bool):
            return str(value)
        else:
            return str(value)
    
    return REFERENCE_PATTERN.sub(replace_ref, expr)


def evaluate_simple_condition(expr: str, context: Dict[str, Any]) -> bool:
    """
    Evaluate a simple condition expression.
    
    Supports:
        - Simple reference (truthy check): "$s1.value"
        - Comparison: "$s1.value > 10"
        - Equality: "$s1.status == 'OK'"
        - Boolean: "$s1.flag == True"
    
    Args:
        expr: Condition expression
        context: Execution context
        
    Returns:
        Boolean result of evaluation
    """
    expr = expr.strip()
    
    # Simple reference - just check if truthy
    if expr.startswith("$") and not any(op in expr for op in OPERATORS.keys()):
        value = resolve_reference(expr, context)
        return bool(value)
    
    # Find operator
    op_found = None
    op_pos = -1
    
    for op in sorted(OPERATORS.keys(), key=len, reverse=True):
        pos = expr.find(op)
        if pos > 0:
            op_found = op
            op_pos = pos
            break
    
    if op_found is None:
        # No operator found, treat as truthy check
        resolved = resolve_all_references(expr, context)
        try:
            # Safe eval for simple values
            return bool(eval(resolved, {"__builtins__": {}}, {}))
        except Exception:
            return False
    
    # Split into left and right
    left_expr = expr[:op_pos].strip()
    right_expr = expr[op_pos + len(op_found):].strip()
    
    # Resolve references
    left_value = resolve_reference(left_expr, context) if left_expr.startswith("$") else parse_literal(left_expr)
    right_value = resolve_reference(right_expr, context) if right_expr.startswith("$") else parse_literal(right_expr)
    
    # Apply operator
    try:
        return OPERATORS[op_found](left_value, right_value)
    except Exception:
        return False


def parse_literal(value: str) -> Any:
    """
    Parse a literal value from string.
    
    Args:
        value: String representation of a value
        
    Returns:
        Parsed value (int, float, bool, str, or None)
    """
    value = value.strip()
    
    # None
    if value == "None":
        return None
    
    # Boolean
    if value == "True":
        return True
    if value == "False":
        return False
    
    # String (quoted)
    if (value.startswith("'") and value.endswith("'")) or \
       (value.startswith('"') and value.endswith('"')):
        return value[1:-1]
    
    # Number
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    
    # Return as string
    return value


def evaluate_condition(expr: str, context: Dict[str, Any]) -> bool:
    """
    Evaluate a condition expression with support for 'and' / 'or'.
    
    Args:
        expr: Condition expression (may contain 'and' / 'or')
        context: Execution context
        
    Returns:
        Boolean result
    """
    expr = expr.strip()
    
    # Handle 'or' (lowest precedence)
    if " or " in expr:
        parts = expr.split(" or ")
        return any(evaluate_condition(part, context) for part in parts)
    
    # Handle 'and'
    if " and " in expr:
        parts = expr.split(" and ")
        return all(evaluate_condition(part, context) for part in parts)
    
    # Handle 'not'
    if expr.startswith("not "):
        return not evaluate_condition(expr[4:], context)
    
    # Simple condition
    return evaluate_simple_condition(expr, context)


def resolve_args(args: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve all $references in a dictionary of arguments.
    
    Args:
        args: Dictionary with potential $references
        context: Execution context
        
    Returns:
        Dictionary with resolved values
    """
    resolved = {}
    for key, value in args.items():
        if isinstance(value, str) and value.startswith("$"):
            resolved[key] = resolve_reference(value, context)
        elif isinstance(value, dict):
            resolved[key] = resolve_args(value, context)
        elif isinstance(value, list):
            resolved[key] = [
                resolve_reference(v, context) if isinstance(v, str) and v.startswith("$") else v
                for v in value
            ]
        else:
            resolved[key] = value
    return resolved
