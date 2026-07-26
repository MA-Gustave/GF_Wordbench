"""User-facing CLI, GUI, and automation adapters for GF Wordbench.

Entrypoints collect external intent, convert it to shared application requests,
invoke the owning use cases, and render completed results. Validation semantics,
project resolution, process execution, orchestration, and report generation
remain in their owning packages. This initializer performs no eager imports and
exposes no convenience API.
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
