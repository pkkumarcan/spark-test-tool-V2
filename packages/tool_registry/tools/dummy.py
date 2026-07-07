from packages.schemas.models import SandboxPolicy
from packages.tool_registry import tool


@tool(
    "hello_world",
    "Returns a greeting message. Used for testing the tool registry.",
    sandbox_policy=SandboxPolicy(timeout_seconds=5),
)
def hello_world(name: str = "World") -> str:
    return f"Hello, {name}!"


@tool(
    "add_numbers",
    "Adds two numbers together.",
    sandbox_policy=SandboxPolicy(timeout_seconds=5),
)
def add_numbers(a: float, b: float) -> str:
    return str(a + b)


@tool(
    "echo_input",
    "Echoes back the input string. Useful for verifying tool-calling works end-to-end.",
    sandbox_policy=SandboxPolicy(timeout_seconds=5),
)
def echo_input(message: str) -> str:
    return f"Echo: {message}"
