"""Public artifact-manifest declaration and model contracts.

Concrete construction, hashing, media-type, requiredness, persistence, and
verification implementations remain in their owning modules. Import manifest
construction from :mod:`gf_wordbench.reporting.manifest.builder` or from the
broad :mod:`gf_wordbench.reporting.public` façade.

This package initializer re-exports only stable, side-effect-free contracts.
"""

from __future__ import annotations

from .declarations import ArtifactDeclaration
from .models import (
    ArtifactManifest,
    ArtifactManifestEntry,
    ManifestVerificationMode,
    ManifestVerificationResult,
    ManifestWriteResult,
)

__all__ = (
    "ArtifactDeclaration",
    "ArtifactManifest",
    "ArtifactManifestEntry",
    "ManifestVerificationMode",
    "ManifestVerificationResult",
    "ManifestWriteResult",
)
