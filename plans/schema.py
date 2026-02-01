"""Plan schema definitions using Pydantic."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class Step(BaseModel):
    """A single step in an execution plan."""
    
    model_config = ConfigDict(extra="forbid", exclude_none=True)
    
    id: str = Field(..., description="Unique step identifier")
    tool: str = Field(..., description="Tool name to execute")
    description: Optional[str] = Field(None, description="Human-readable description")
    args: Optional[Dict[str, Any]] = Field(None, description="Tool arguments (supports $references)")
    run_if: Optional[str] = Field(None, description="Conditional execution expression")
    key_finding: Optional[bool] = Field(None, description="Mark output as critical finding")
    intervention_if: Optional[str] = Field(None, description="Trigger INTERVENTION_NEEDED if condition met")
    
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


class Plan(BaseModel):
    """Execution plan containing multiple steps."""
    
    model_config = ConfigDict(extra="forbid", exclude_none=True)
    
    id: Optional[str] = Field(None, description="Plan identifier")
    name: Optional[str] = Field(None, description="Plan name")
    description: Optional[str] = Field(None, description="Plan description")
    steps: List[Step] = Field(..., description="List of execution steps")
    
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


def validate_plan(plan_data: Dict[str, Any]) -> Plan:
    """
    Validate a plan dictionary and return a Plan model.
    
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


def plan_to_dict(plan: Plan) -> Dict[str, Any]:
    """
    Convert a Plan model to a dictionary.
    
    Args:
        plan: Plan model
        
    Returns:
        Dictionary representation
    """
    return plan.model_dump(exclude_none=True)
