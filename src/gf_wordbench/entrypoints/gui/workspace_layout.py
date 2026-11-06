"""Resolve companion GF tools from the *actual* WordBench Git checkout.

The Windows canonical layout places ``.git`` in
``<workspace>/GF_Wordbench/GF_Wordbench``.  The containing outer folder is
not another repository or a second Python package.  A standalone checkout at
``<workspace>/GF_Wordbench`` is also supported for portability.  This module
never looks inside the outer wrapper for a competing implementation.
"""
from __future__ import annotations

from pathlib import Path


def workspace_from_repository(repository_root: Path) -> Path:
    """Return the directory containing the compiler and RGL siblings."""
    if not isinstance(repository_root, Path):
        raise TypeError("repository_root must be a pathlib.Path")
    root = repository_root.expanduser().resolve(strict=False)
    if (
        root.name.casefold() == "gf_wordbench"
        and root.parent.name.casefold() == "gf_wordbench"
    ):
        return root.parent.parent
    return root.parent


def sibling_from_repository(repository_root: Path, name: str) -> Path:
    """Find a toolchain sibling without accepting path fragments or traversal."""
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError("name must be one repository/workspace directory")
    return workspace_from_repository(repository_root) / name
