"""Mechanism-neutral ports owned by the reporting module.

Reporting consumes finalized structured results and stable run artifacts.  These
interfaces isolate artifact transport, canonical schema serialization, and
manifest hashing from report builders and publication coordination.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol, TypeAlias, runtime_checkable

JsonDocument: TypeAlias = Mapping[str, object]

__all__ = (
    "ArtifactReader",
    "ArtifactWriter",
    "JsonDocument",
    "ManifestHasher",
    "SchemaSerializer",
)


@runtime_checkable
class ArtifactWriter(Protocol):
    """Persist one reporting-owned artifact beneath an approved run root."""

    def write(
        self,
        destination: Path,
        content: bytes,
        *,
        overwrite: bool = False,
    ) -> None:
        """Publish exact artifact bytes atomically.

        Implementations must not expose a complete-looking partial destination.
        They must flush and close staged bytes before replacement, reject unsafe
        destinations, and leave an existing destination intact when publication
        fails.
        """
        ...


@runtime_checkable
class ArtifactReader(Protocol):
    """Read stable artifact bytes without changing the artifact or its owner."""

    def read(self, source: Path) -> bytes:
        """Return the exact bytes stored at ``source``."""
        ...

    def exists(self, source: Path) -> bool:
        """Return whether ``source`` exists, without following it outside policy."""
        ...

    def is_file(self, source: Path) -> bool:
        """Return whether ``source`` is an approved regular artifact file."""
        ...

    def size_bytes(self, source: Path) -> int:
        """Return the final byte count of a stable artifact file."""
        ...


@runtime_checkable
class SchemaSerializer(Protocol):
    """Encode and decode one explicitly versioned reporting schema."""

    def serialize(self, document: JsonDocument) -> bytes:
        """Return deterministic UTF-8 bytes for a validated schema document."""
        ...

    def deserialize(self, payload: bytes) -> JsonDocument:
        """Decode bytes into a schema document without applying migrations."""
        ...


@runtime_checkable
class ManifestHasher(Protocol):
    """Compute integrity facts from final immutable artifact bytes."""

    def sha256(self, source: Path) -> str:
        """Return the lowercase 64-character SHA-256 digest of ``source``."""
        ...
