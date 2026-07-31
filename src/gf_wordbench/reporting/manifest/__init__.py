"""Public artifact-manifest construction and model contracts.

Concrete hashing, media-type, requiredness, persistence, and verification
implementations remain in their owning modules. This initializer re-exports
only implemented, stable symbols.
"""

from __future__ import annotations

from .builder import build_manifest
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
    "build_manifest",
)