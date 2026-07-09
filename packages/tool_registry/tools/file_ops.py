"""File operation tools: read, create, write, edit, multi_replace, delete, list, mkdir."""

import os
import shutil

from packages.schemas.models import SandboxPolicy
from packages.tool_registry import tool
from packages.tool_registry.paths import is_within_root, resolve_in_root

MAX_READ_LINES = 500

_WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", "/workspace")


def _safe_path(path: str) -> bool:
    return is_within_root(path, _WORKSPACE_ROOT)


def _abs(path: str) -> str:
    return resolve_in_root(path, _WORKSPACE_ROOT)


@tool(
    "read_file",
    "Read contents of a file. Supports optional line range.",
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=5),
)
def read_file(path: str, start_line: int | None = None, end_line: int | None = None) -> str:
    if not _safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = _abs(path)
    if not os.path.exists(abs_path):
        return f"Error: File '{path}' does not exist."
    if os.path.isdir(abs_path):
        return f"Error: '{path}' is a directory, not a file."

    with open(abs_path, encoding="utf-8") as f:
        lines = f.readlines()

    total = len(lines)
    truncated = False

    if start_line is not None or end_line is not None:
        s = (start_line or 1) - 1
        e = end_line or total
        lines = lines[s:e]

    if len(lines) > MAX_READ_LINES:
        lines = lines[:MAX_READ_LINES]
        truncated = True

    output = "".join(lines)
    if truncated:
        output += f"\n\n[Truncated at {MAX_READ_LINES} lines. Total: {total} lines. Use start_line/end_line to read specific ranges.]"
    return output


@tool(
    "create_file",
    "Create a new file. Fails if file already exists. Creates parent directories.",
    requires_approval=True,
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=5),
)
def create_file(path: str, content: str) -> str:
    if not _safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = _abs(path)
    if os.path.exists(abs_path):
        return f"Error: File '{path}' already exists. Use write_file to overwrite."

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully created file '{path}'."


@tool(
    "write_file",
    "Write or overwrite content in a file. Creates file if it doesn't exist.",
    requires_approval=True,
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=5),
)
def write_file(path: str, content: str) -> str:
    if not _safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = _abs(path)

    backup = None
    if os.path.exists(abs_path):
        backup = abs_path + ".bak"
        try:
            shutil.copy2(abs_path, backup)
        except Exception:
            backup = None

    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        if backup and os.path.exists(backup):
            os.remove(backup)
        return f"Successfully wrote contents to file '{path}'."
    except Exception as e:
        if backup and os.path.exists(backup):
            shutil.move(backup, abs_path)
        return f"Error writing file: {e} (rolled back)"


@tool(
    "edit_file",
    "Surgical text replacement in a file. Replaces exact old_text with new_text.",
    requires_approval=True,
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=5),
)
def edit_file(path: str, old_text: str, new_text: str) -> str:
    if not old_text:
        return "Error: old_text cannot be empty."
    if not _safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = _abs(path)
    if not os.path.exists(abs_path):
        return f"Error: File '{path}' does not exist."

    with open(abs_path, encoding="utf-8") as f:
        content = f.read()

    count = content.count(old_text)
    if count == 0:
        return f"Error: old_text not found in '{path}'."
    if count > 1:
        return f"Error: old_text found {count} times in '{path}'. Provide more context to make it unique."

    new_content = content.replace(old_text, new_text, 1)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return f"Successfully edited file '{path}'."


@tool(
    "multi_replace",
    "Apply multiple non-contiguous text replacements to a file in one operation.",
    requires_approval=True,
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=5),
)
def multi_replace(path: str, replacements: list[dict]) -> str:
    if not _safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = _abs(path)
    if not os.path.exists(abs_path):
        return f"Error: File '{path}' does not exist."
    if not replacements:
        return "Error: No replacements provided."

    with open(abs_path, encoding="utf-8") as f:
        content = f.read()

    applied = 0
    errors = []
    for i, repl in enumerate(replacements):
        old_text = repl.get("old_text", "")
        new_text = repl.get("new_text", "")
        if not old_text:
            errors.append(f"Replacement {i + 1}: empty old_text")
            continue
        count = content.count(old_text)
        if count == 0:
            errors.append(f"Replacement {i + 1}: old_text not found")
            continue
        if count > 1:
            errors.append(f"Replacement {i + 1}: old_text found {count} times (not unique)")
            continue
        content = content.replace(old_text, new_text, 1)
        applied += 1

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

    result = f"Applied {applied}/{len(replacements)} replacements to '{path}'."
    if errors:
        result += " Errors: " + "; ".join(errors)
    return result


@tool(
    "delete_file",
    "Delete a file. Does not delete directories.",
    requires_approval=True,
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=5),
)
def delete_file(path: str) -> str:
    if not _safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = _abs(path)
    if not os.path.exists(abs_path):
        return f"Error: File '{path}' does not exist."
    if os.path.isdir(abs_path):
        return f"Error: '{path}' is a directory. Cannot delete directories with this tool."

    os.remove(abs_path)
    return f"Successfully deleted file '{path}'."


@tool(
    "list_directory",
    "List contents of a directory with type and size info.",
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=5),
)
def list_directory(path: str = ".") -> str:
    if not _safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = _abs(path)
    if not os.path.exists(abs_path):
        return f"Error: Path '{path}' does not exist."
    if not os.path.isdir(abs_path):
        return f"Error: '{path}' is not a directory."

    items = sorted(os.listdir(abs_path))
    if not items:
        return f"Directory '{path}' is empty."
    result = []
    for item in items:
        item_path = os.path.join(abs_path, item)
        is_dir = os.path.isdir(item_path)
        if is_dir:
            result.append(f"[DIR]  {item}/")
        else:
            size = os.path.getsize(item_path)
            result.append(f"[FILE] {item} ({size} bytes)")
    return "\n".join(result)


@tool(
    "make_directory",
    "Create a new directory (and any missing parent directories).",
    requires_approval=True,
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=5),
)
def make_directory(path: str) -> str:
    if not path:
        return "Error: path is required."
    if not _safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = _abs(path)

    if os.path.exists(abs_path):
        if os.path.isdir(abs_path):
            return f"Directory '{path}' already exists."
        return f"Error: '{path}' already exists and is a file."

    os.makedirs(abs_path, exist_ok=True)
    return f"Successfully created directory '{path}'."
