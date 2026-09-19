"""Path-resolved GF language startup package.

GF Wordbench remains monolingual after startup. This package owns the bounded
loader-side contracts and services that resolve one explicitly selected GF
language before the main application runtime is composed.

Stable consumers import from :mod:`gf_wordbench.projects.languages.public` or
from the aggregate :mod:`gf_wordbench.projects.public`. This initializer
intentionally performs no eager imports, filesystem access, probing, state
mutation, or runtime composition.
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
