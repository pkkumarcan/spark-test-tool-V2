"""Search tools: regex search and semantic search via RAG."""

import glob as glob_module
import os
import re

from packages.schemas.models import SandboxPolicy
from packages.tool_registry import tool
from packages.tool_registry.paths import is_within_root, resolve_in_root

_MAX_SEARCH_RESULTS = 50
_WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", "/workspace")


def _safe_path(path: str) -> bool:
    return is_within_root(path, _WORKSPACE_ROOT)


def _abs(path: str) -> str:
    return resolve_in_root(path, _WORKSPACE_ROOT)


@tool(
    "search_files",
    "Search file contents using regex. Returns matching lines with file:line format.",
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=10),
)
def search_files(pattern: str, path: str = ".", include: str = "*") -> str:
    if not pattern:
        return "Error: pattern is required."
    if not _safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = _abs(path)
    if not os.path.exists(abs_path):
        return f"Error: Path '{path}' does not exist."

    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"Error: Invalid regex pattern: {e}"

    results = []
    for root, dirs, files in os.walk(abs_path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            if not glob_module.fnmatch.fnmatch(fname, include):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if regex.search(line):
                            rel = os.path.relpath(fpath, _WORKSPACE_ROOT)
                            results.append(f"{rel}:{i}: {line.rstrip()}")
                            if len(results) >= _MAX_SEARCH_RESULTS:
                                results.append(
                                    f"\n[Truncated at {_MAX_SEARCH_RESULTS} results. Refine your search pattern.]"
                                )
                                return "\n".join(results)
            except Exception:
                continue

    if not results:
        return f"No matches found for pattern '{pattern}' in '{path}'."
    return "\n".join(results)


@tool(
    "semantic_search",
    "Search files by meaning using embeddings. Requires RAG to be configured.",
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=15),
)
def semantic_search(query: str, limit: int = 10) -> str:
    if not query:
        return "Error: query is required."

    try:
        import asyncio

        from apps.agent_runtime.rag import query as rag_query

        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(rag_query(query, limit=limit))
        finally:
            loop.close()

        if not results:
            return "No semantic matches found."
        output = []
        for r in results:
            path = r.get("path", "?")
            line = r.get("line", "?")
            content = r.get("content", "")[:100]
            score = r.get("score", 0)
            output.append(f"{path}:{line} (score: {score:.2f}): {content}")
        return "\n".join(output)
    except ImportError:
        return "Error: RAG module not configured. Semantic search requires embeddings infrastructure."
    except Exception as e:
        return f"Semantic search error: {e}"
