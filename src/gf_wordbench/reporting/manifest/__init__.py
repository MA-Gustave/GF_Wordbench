"""Artifact-manifest construction and verification contracts.

The manifest package exposes only the stable models and orchestration functions
needed by reporting and run finalization. Hashing, media-type resolution, and
requiredness helpers remain owned by their dedicated implementation modules.
"""

from __future__ import annotations

from .builder import build_manifest, write_manifest
from .declarations import ArtifactDeclaration
from .models import (
    ArtifactManifest,
    ArtifactManifestEntry,
    ManifestVerificationPolicy,
    ManifestVerificationResult,
    ManifestWriteResult,
)
from .verifier import verify_manifest

__all__ = (
    "ArtifactDeclaration",
    "ArtifactManifest",
    "ArtifactManifestEntry",
    "ManifestVerificationPolicy",
    "ManifestVerificationResult",
    "ManifestWriteResult",
    "build_manifest",
    "verify_manifest",
    "write_manifest",
)
