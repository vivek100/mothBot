"""Tool registry for managing callable tools."""

from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field
import inspect


@dataclass
class ToolInfo:
    """Information about a registered tool."""
    
    name: str
    func: Callable
    description: str = ""
    is_async: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_callable(cls, name: str, func: Callable) -> "ToolInfo":
        """Create ToolInfo from a callable."""
        import asyncio
        
        # Get description from docstring
        description = func.__doc__ or ""
        if description:
            description = description.strip().split("\n")[0]  # First line only
        
        # Check if async
        is_async = asyncio.iscoroutinefunction(func)
        
        # Get parameters from signature
        sig = inspect.signature(func)
        parameters = {}
        for param_name, param in sig.parameters.items():
            param_info = {"name": param_name}
            
            if param.annotation != inspect.Parameter.empty:
                param_info["type"] = str(param.annotation)
            
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
            
            parameters[param_name] = param_info
        
        return cls(
            name=name,
            func=func,
            description=description,
            is_async=is_async,
            parameters=parameters
        )


class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self):
        self._tools: Dict[str, ToolInfo] = {}
    
    def register(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Callable:
        """
        Decorator to register a tool.
        
        Usage:
            @registry.register()
            def my_tool(arg: str) -> dict:
                return {"result": arg}
            
            @registry.register(name="custom_name", description="Custom description")
            def another_tool():
                pass
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            info = ToolInfo.from_callable(tool_name, func)
            
            if description:
                info.description = description
            
            self._tools[tool_name] = info
            return func
        
        return decorator
    
    def add(self, name: str, func: Callable, description: str = "") -> None:
        """
        Add a tool to the registry.
        
        Args:
            name: Tool name
            func: Callable to register
            description: Optional description
        """
        info = ToolInfo.from_callable(name, func)
        if description:
            info.description = description
        self._tools[name] = info
    
    def add_many(self, tools: Dict[str, Callable]) -> None:
        """
        Add multiple tools at once.
        
        Args:
            tools: Dictionary mapping names to callables
        """
        for name, func in tools.items():
            self.add(name, func)
    
    def get(self, name: str) -> Optional[Callable]:
        """Get a tool by name."""
        info = self._tools.get(name)
        return info.func if info else None
    
    def get_info(self, name: str) -> Optional[ToolInfo]:
        """Get tool info by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def list_info(self) -> List[ToolInfo]:
        """List all tool info objects."""
        return list(self._tools.values())
    
    def to_dict(self) -> Dict[str, Callable]:
        """
        Convert registry to a simple dict for executor.
        
        Returns:
            Dictionary mapping tool names to callables
        """
        return {name: info.func for name, info in self._tools.items()}
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools
    
    def __getitem__(self, name: str) -> Callable:
        info = self._tools.get(name)
        if info is None:
            raise KeyError(f"Tool '{name}' not found")
        return info.func
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __iter__(self):
        return iter(self._tools)


def create_registry(*tools: Callable, **named_tools: Callable) -> ToolRegistry:
    """
    Create a registry from tools.
    
    Args:
        *tools: Callables (uses function name as tool name)
        **named_tools: Named callables
        
    Returns:
        ToolRegistry with all tools registered
        
    Example:
        registry = create_registry(
            scan_hull,
            check_oxygen,
            custom_name=my_custom_tool
        )
    """
    registry = ToolRegistry()
    
    for func in tools:
        registry.add(func.__name__, func)
    
    for name, func in named_tools.items():
        registry.add(name, func)
    
    return registry
