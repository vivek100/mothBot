"""
Skills API - FastAPI endpoints for serving skills data to the frontend.

This module provides HTTP endpoints to:
1. List all available skills
2. Get detailed information about a specific skill

Run alongside the bot using:
    uvicorn skills_api:app --host 0.0.0.0 --port 7861
"""

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add marimo_engine to path for imports
toolchain_path = Path(__file__).parent.parent.parent.parent  # toolChainEngine folder
sys.path.insert(0, str(toolchain_path))

from marimo_engine.plans import (
    get_example_plans,
    get_plan_by_id,
    get_skills_summary,
    get_dynamic_skills,
)
from marimo_engine.tools import get_example_tools

app = FastAPI(
    title="Skills API",
    description="API for accessing available skills and tool chains",
    version="1.0.0",
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "skills-api"}


@app.get("/skills")
async def list_skills() -> dict[str, Any]:
    """
    List all available skills with summary information.
    
    Returns a list of skills with:
    - id: Unique skill identifier
    - name: Human-readable name
    - description: What the skill does
    - when_to_use: Guidance on when to use
    - steps_count: Number of steps in the skill
    - has_intervention: Whether skill can trigger interventions
    - keywords: Keywords that suggest this skill
    - is_dynamic: Whether this is a dynamically saved skill
    """
    summaries = get_skills_summary()
    
    return {
        "status": "success",
        "count": len(summaries),
        "skills": summaries,
    }


@app.get("/skills/{skill_id}")
async def get_skill_details(skill_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific skill.
    
    Args:
        skill_id: The skill identifier
        
    Returns:
        Full skill details including:
        - All summary fields
        - steps: Full step definitions
        - expected_outcome: What to expect after running
        - debug_tips: Tips for debugging
        - fallback_tools: Individual tools to try if skill fails
        - triggers: Keywords and intents that suggest this skill
    """
    try:
        skill = get_plan_by_id(skill_id)
        
        # Build detailed response
        return {
            "status": "success",
            "skill": {
                "id": skill.get("id"),
                "name": skill.get("name"),
                "description": skill.get("description"),
                "when_to_use": skill.get("when_to_use", ""),
                "expected_outcome": skill.get("expected_outcome", ""),
                "debug_tips": skill.get("debug_tips", []),
                "fallback_tools": skill.get("fallback_tools", []),
                "triggers": skill.get("triggers", {}),
                "is_dynamic": skill.get("_dynamic", False),
                "steps": [
                    {
                        "id": step.get("id"),
                        "tool": step.get("tool"),
                        "description": step.get("description", ""),
                        "args": step.get("args"),
                        "run_if": step.get("run_if"),
                        "key_finding": step.get("key_finding", False),
                        "intervention_if": step.get("intervention_if"),
                    }
                    for step in skill.get("steps", [])
                ],
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/tools")
async def list_tools() -> dict[str, Any]:
    """
    List all available individual tools.
    
    Returns tool names that can be used in skills.
    """
    tools = get_example_tools()
    tool_info = []
    
    for name, func in tools.items():
        tool_info.append({
            "name": name,
            "is_async": name.startswith("async_"),
        })
    
    return {
        "status": "success",
        "count": len(tool_info),
        "tools": tool_info,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7861)
