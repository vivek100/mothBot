"""
Weave Tracing Integration for the Pipecat Diagnostic Agent.

Simple initialization module for Weave tracing.
The actual tracing is done via @weave.op() decorators on functions.

Usage:
    from weave_tracing import init_weave

    # Initialize at startup
    init_weave()
    
    # Then use @weave.op() on functions you want to trace
    @weave.op()
    async def my_function():
        ...
"""

import os
from typing import Optional

import weave
from loguru import logger


def init_weave(project_name: Optional[str] = None) -> bool:
    """
    Initialize Weave tracing.
    
    Args:
        project_name: Optional project name. If not provided, uses WEAVE_PROJECT_NAME env var.
        
    Returns:
        True if initialization successful, False otherwise.
    """
    # Check if tracing is disabled
    if os.getenv("WEAVE_DISABLED", "false").lower() == "true":
        logger.info("Weave tracing is disabled via WEAVE_DISABLED env var")
        return False
    
    # Check for W&B API key
    wandb_key = os.getenv("WANDB_API_KEY")
    if not wandb_key:
        logger.warning("WANDB_API_KEY not set - Weave tracing will not be available")
        return False
    
    # Get project name
    project = project_name or os.getenv("WEAVE_PROJECT_NAME", "toolCallAgent")
    
    try:
        weave.init(project)
        logger.info(f"✅ Weave tracing initialized for project: {project}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Weave: {e}")
        return False
