from __future__ import annotations

import importlib
import pkgutil
import sys
from collections.abc import Callable
from typing import Any

from packages.schemas.models import SandboxPolicy, ToolDefinition

_REGISTRY: dict[str, ToolDefinition] = {}


def tool(
    name: str,
    description: str,
    requires_approval: bool = False,
    sandbox_policy: SandboxPolicy | None = None,
) -> Callable:
    """Decorator that registers a function as a tool."""

    def decorator(fn: Callable) -> Callable:
        # Build JSON schema from type hints
        import inspect
        sig = inspect.signature(fn)
        properties: dict[str, Any] = {}
        required: list[str] = []
        for param_name, param in sig.parameters.items():
            hint = param.annotation
            prop: dict[str, Any] = {}
            # Resolve stringified annotations from __future__ import annotations
            resolved = hint
            if isinstance(hint, str):
                resolved = {"str": str, "int": int, "float": float, "bool": bool}.get(hint, hint)
            # Unwrap Optional[X] / X | None → X
            origin = getattr(resolved, "__origin__", None)
            if origin is not None:
                args = getattr(resolved, "__args__", ())
                if args:
                    resolved = args[0]
            if resolved is str:
                prop["type"] = "string"
            elif resolved is int:
                prop["type"] = "integer"
            elif resolved is float:
                prop["type"] = "number"
            elif resolved is bool:
                prop["type"] = "boolean"
            else:
                prop["type"] = "string"
            if param.default is inspect.Parameter.empty:
                required.append(param_name)
            properties[param_name] = prop

        input_schema = {
            "type": "object",
            "properties": properties,
            "required": required,
        }

        definition = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            requires_approval=requires_approval,
            sandbox_policy=sandbox_policy or SandboxPolicy(),
            handler=fn,
        )
        _REGISTRY[name] = definition
        return fn

    return decorator


def get_all_tools() -> dict[str, ToolDefinition]:
    """Return all registered tools."""
    auto_discover()
    return dict(_REGISTRY)


def get_tool(name: str) -> ToolDefinition | None:
    """Get a single tool by name."""
    auto_discover()
    return _REGISTRY.get(name)


def get_schemas() -> list[dict[str, Any]]:
    """Return tool schemas in the format expected by native tool-calling APIs."""
    auto_discover()
    schemas = []
    for tool_def in _REGISTRY.values():
        schemas.append({
            "type": "function",
            "function": {
                "name": tool_def.name,
                "description": tool_def.description,
                "parameters": tool_def.input_schema,
            },
        })
    return schemas


def auto_discover(force: bool = False) -> None:
    """Import all modules under packages.tool_registry.tools to trigger @tool decorators."""
    if _REGISTRY and not force:
        return
    try:
        package = importlib.import_module("packages.tool_registry.tools")
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            full_name = f"packages.tool_registry.tools.{module_name}"
            if force and full_name in sys.modules:
                del sys.modules[full_name]
            importlib.import_module(full_name)
    except Exception:
        pass
