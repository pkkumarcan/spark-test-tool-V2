from __future__ import annotations

import os


def is_within_root(path: str, root: str) -> bool:
    """True if `path` resolves to `root` or somewhere strictly inside it."""
    root = os.path.realpath(root)
    resolved = (
        os.path.realpath(path)
        if os.path.isabs(path)
        else os.path.realpath(os.path.join(root, path))
    )
    return resolved == root or resolved.startswith(root + os.sep)


def resolve_in_root(path: str, root: str) -> str:
    """Resolve a path (absolute or relative) against root."""
    root = os.path.realpath(root)
    return (
        os.path.realpath(path)
        if os.path.isabs(path)
        else os.path.realpath(os.path.join(root, path))
    )
