"""Plan schemas and examples.

Terminology:
- Tool Chain: A sequence of tools executed in order
- Skill: A saved tool chain with usage guidance
- Plan: Alias for tool chain (backward compatibility)
"""

from .schema import (
    Step,
    Plan,
    ToolChain,
    Skill,
    SkillTrigger,
    validate_plan,
    validate_tool_chain,
    plan_to_dict,
    create_tool_chain,
)
from .examples import (
    get_test_plan,
    get_example_plans,
    get_builtin_plans,
    get_saved_skills,
    get_plan_by_id,
    get_skill_by_id,
    get_skills_summary,
    # Dynamic skill management
    save_skill,
    delete_skill,
    get_dynamic_skills,
    reload_dynamic_skills,
)

__all__ = [
    # Schema
    "Step",
    "Plan",
    "ToolChain",
    "Skill",
    "SkillTrigger",
    "validate_plan",
    "validate_tool_chain",
    "plan_to_dict",
    "create_tool_chain",
    # Examples
    "get_test_plan",
    "get_example_plans",
    "get_builtin_plans",
    "get_saved_skills",
    "get_plan_by_id",
    "get_skill_by_id",
    "get_skills_summary",
    # Dynamic skill management
    "save_skill",
    "delete_skill",
    "get_dynamic_skills",
    "reload_dynamic_skills",
]
