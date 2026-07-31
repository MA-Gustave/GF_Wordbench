"""Public deterministic source-selection contracts for GF Wordbench.

The package facade exposes only the stable models and operations required by
cross-module application adapters, including path-resolved language startup.
Filtering, ordering, and target-resolution implementation details remain in
their owning modules.

Importing this package performs no filesystem access and starts no validation
or external-process work.
"""

from __future__ import annotations

from .models import (
    ExcludedFileEntry,
    FileSelection,
    SelectionCounts,
    SelectionOrigin,
    SelectionReason,
)
from .service import SelectionFilesystem, SelectionService, select_files
from .targets import extract_module_name

__all__ = (
    "ExcludedFileEntry",
    "FileSelection",
    "SelectionCounts",
    "SelectionFilesystem",
    "SelectionOrigin",
    "SelectionReason",
    "SelectionService",
    "extract_module_name",
    "select_files",
)
