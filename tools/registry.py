"""
Tool Registry

Manages the registration and discovery of tools for the Block Police agent.
"""
from typing import Dict, Any, Callable, List

# Registry to store all registered tools
_TOOL_REGISTRY = {}

def register_tool(name: str, description: str):
    """
    Decorator to register a tool function in the global registry

    Args:
        name: The unique name of the tool
        description: A description of what the tool does

    Returns:
        Decorator function
    """
    def decorator(func):
        if name in _TOOL_REGISTRY:
            raise ValueError(f"Tool with name '{name}' already registered")

        _TOOL_REGISTRY[name] = {
            "function": func,
            "description": description,
            "name": name
        }
        return func
    return decorator

def get_registered_tools() -> Dict[str, Dict[str, Any]]:
    """
    Get all registered tools

    Returns:
        Dictionary of registered tools
    """
    return _TOOL_REGISTRY

def get_tool_functions() -> Dict[str, Callable]:
    """
    Get all tool functions

    Returns:
        Dictionary mapping tool names to their functions
    """
    return {name: details["function"] for name, details in _TOOL_REGISTRY.items()}

def get_tool_descriptions() -> List[Dict[str, str]]:
    """
    Get tool descriptions for documentation

    Returns:
        List of tool descriptions
    """
    return [
        {"name": details["name"], "description": details["description"]}
        for name, details in _TOOL_REGISTRY.items()
    ]