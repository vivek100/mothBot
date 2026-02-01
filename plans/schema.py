"""Plan and Skill schema definitions using Pydantic.

Terminology:
- Tool Chain: A sequence of tools executed in order with data passing between steps
- Skill: A saved/named tool chain with usage guidance for the agent
- Plan: Alias for tool chain (backward compatibility)
"""

from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class Step(BaseModel):
    """A single step in a tool chain."""
    
    model_config = ConfigDict(extra="forbid", exclude_none=True)
    
    id: str = Field(..., description="Unique step identifier")
    tool: str = Field(..., description="Tool name to execute")
    description: Optional[str] = Field(None, description="Human-readable description")
    args: Optional[Dict[str, Any]] = Field(None, description="Tool arguments (supports $references like $s1.level)")
    run_if: Optional[str] = Field(None, description="Conditional execution expression (e.g., '$s1.status == OK')")
    key_finding: Optional[bool] = Field(None, description="Mark output as critical finding")
    intervention_if: Optional[str] = Field(None, description="Trigger INTERVENTION_NEEDED if condition met")
    on_error: Optional[Literal["stop", "skip", "retry"]] = Field(None, description="Error handling strategy")
    
    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Step id cannot be empty")
        return v.strip()
    
    @field_validator("tool")
    @classmethod
    def validate_tool(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Tool name cannot be empty")
        return v.strip()


class SkillTrigger(BaseModel):
    """Defines when an agent should consider using this skill."""
    
    model_config = ConfigDict(extra="forbid", exclude_none=True)
    
    keywords: List[str] = Field(default_factory=list, description="Keywords that suggest this skill")
    user_intents: List[str] = Field(default_factory=list, description="User intents this skill addresses")
    prerequisites: Optional[List[str]] = Field(None, description="Required context before using")
    avoid_when: Optional[List[str]] = Field(None, description="Situations to avoid this skill")


class Plan(BaseModel):
    """
    Tool chain definition - can be a simple chain or a saved skill.
    
    A Plan becomes a Skill when it has usage guidance (when_to_use, expected_outcome, etc.)
    """
    
    model_config = ConfigDict(extra="forbid", exclude_none=True)
    
    # Basic identification
    id: Optional[str] = Field(None, description="Unique identifier")
    name: Optional[str] = Field(None, description="Human-readable name")
    description: Optional[str] = Field(None, description="What this tool chain does")
    
    # Execution steps
    steps: List[Step] = Field(..., description="List of execution steps")
    
    # Skill metadata (makes this a "saved skill" when populated)
    when_to_use: Optional[str] = Field(None, description="Detailed guidance on when to use this skill")
    expected_outcome: Optional[str] = Field(None, description="What to expect after running")
    triggers: Optional[SkillTrigger] = Field(None, description="Automatic trigger conditions")
    
    # Debugging support
    debug_tips: Optional[List[str]] = Field(None, description="Tips for debugging if skill fails")
    fallback_tools: Optional[List[str]] = Field(None, description="Individual tools to try if skill fails")
    
    @field_validator("steps")
    @classmethod
    def validate_steps(cls, v: List[Step]) -> List[Step]:
        if not v:
            raise ValueError("Plan must have at least one step")
        
        # Check for duplicate step IDs
        ids = [step.id for step in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Step IDs must be unique")
        
        return v
    
    def is_skill(self) -> bool:
        """Check if this plan has skill metadata (is a saved skill)."""
        return bool(self.when_to_use or self.expected_outcome or self.triggers)


# Alias for backward compatibility
ToolChain = Plan
Skill = Plan


def validate_plan(plan_data: Dict[str, Any]) -> Plan:
    """
    Validate a plan/tool chain dictionary and return a Plan model.
    
    Args:
        plan_data: Dictionary containing plan data
        
    Returns:
        Validated Plan model
        
    Raises:
        ValueError: If plan is invalid
    """
    try:
        return Plan(**plan_data)
    except Exception as e:
        raise ValueError(f"Invalid plan: {str(e)}")


def validate_tool_chain(chain_data: Dict[str, Any]) -> Plan:
    """Alias for validate_plan - validates a tool chain."""
    return validate_plan(chain_data)


def plan_to_dict(plan: Plan) -> Dict[str, Any]:
    """
    Convert a Plan model to a dictionary.
    
    Args:
        plan: Plan model
        
    Returns:
        Dictionary representation
    """
    return plan.model_dump(exclude_none=True)


def create_tool_chain(
    steps: List[Dict[str, Any]],
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Helper to create a tool chain dictionary.
    
    Args:
        steps: List of step dictionaries
        name: Optional name for the chain
        description: Optional description
        
    Returns:
        Tool chain dictionary ready for execution
        
    Example:
        chain = create_tool_chain(
            steps=[
                {"id": "s1", "tool": "check_oxygen"},
                {"id": "s2", "tool": "analyze_atmosphere", "args": {"o2_level": "$s1.level"}}
            ],
            name="Oxygen Analysis Chain"
        )
    """
    chain = {"steps": steps}
    if name:
        chain["name"] = name
    if description:
        chain["description"] = description
    return chain
