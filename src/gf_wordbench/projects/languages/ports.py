"""Ports for path-resolved GF language startup.

The language-probe application service coordinates these mechanism-neutral
interfaces.  Concrete adapters must reuse the public Wordbench selection,
filesystem, GF-path, preflight, compilation, and diagnostic boundaries rather
than introducing parallel implementations.

The ports intentionally model only the information required to turn one
explicitly selected GF file or language directory into a validated language
candidate and, eventually, one immutable ``ResolvedLanguageContext``.

Normal implementations must remain read-only with respect to the selected RGL
source tree.  They must not generate catalogs, create language bundles, rewrite
project configuration, update gold files, or invoke external processes outside
the approved GF execution boundary.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypeAlias, runtime_checkable

if TYPE_CHECKING:
    from gf_wordbench.projects.languages.models import (
        ExactModuleSearchRequest,
        ExactModuleSearchResult,
        LanguageCompileVerificationRequest,
        LanguageCompileVerificationResult,
        LanguageGfPathResolutionRequest,
        LanguageGfPathResolutionResult,
        LanguagePreflightRequest,
        LanguagePreflightResult,
        LanguageProbeRequest,
        LanguageProbeResult,
        LanguageSourceInventoryRequest,
        LanguageSourceInventoryResult,
    )

__all__ = (
    "ExactModuleSearchPort",
    "LanguageCompileVerifierPort",
    "LanguageFilesystemPort",
    "LanguageGfPathResolverPort",
    "LanguagePreflightPort",
    "LanguageProbePort",
    "LanguageSourceInventoryPort",
    "ModuleNameExtractor",
)


# The production dependency should normally be
# ``validation.selection.targets.extract_module_name``.  The alias lets the
# probe receive that public operation without wrapping it in another service.
ModuleNameExtractor: TypeAlias = Callable[[Path], str]


@runtime_checkable
class LanguageProbePort(Protocol):
    """Resolve one explicit file or directory selection.

    Implementations return a typed result rather than displaying dialogs,
    writing application state, composing the main GUI runtime, or allocating a
    validation run directory.
    """

    def probe(
        self,
        request: LanguageProbeRequest,
    ) -> LanguageProbeResult:
        """Return a resolved, ambiguous, invalid, or unavailable probe result."""
        ...


@runtime_checkable
class LanguageFilesystemPort(Protocol):
    """Provide bounded, link-aware filesystem observations for the probe.

    Source enumeration is deliberately absent from this port.  Enumeration,
    filtering, deduplication, and deterministic ordering belong to
    ``LanguageSourceInventoryPort`` and its adapter over the existing selection
    service.
    """

    def resolve(
        self,
        path: Path,
        *,
        strict: bool,
    ) -> Path:
        """Return a normalized absolute path using the approved link policy."""
        ...

    def exists(
        self,
        path: Path,
    ) -> bool:
        """Return whether ``path`` exists according to the filesystem adapter."""
        ...

    def is_file(
        self,
        path: Path,
    ) -> bool:
        """Return whether ``path`` is a regular file."""
        ...

    def is_directory(
        self,
        path: Path,
    ) -> bool:
        """Return whether ``path`` is a directory."""
        ...

    def is_readable(
        self,
        path: Path,
    ) -> bool:
        """Return whether the current process can read ``path``."""
        ...

    def require_contained(
        self,
        path: Path,
        *,
        root: Path,
        allow_root: bool = False,
    ) -> Path:
        """Return the resolved path or raise when it escapes ``root``."""
        ...


@runtime_checkable
class LanguageSourceInventoryPort(Protocol):
    """Enumerate eligible GF sources through the existing selection boundary.

    A concrete adapter is expected to translate the language-specific request
    into the public selection-service contract.  It owns no independent glob,
    regex, ordering, readability, containment, or deduplication rules.
    """

    def inventory(
        self,
        request: LanguageSourceInventoryRequest,
    ) -> LanguageSourceInventoryResult:
        """Return deterministic selected sources and structured exclusions."""
        ...


@runtime_checkable
class LanguageGfPathResolverPort(Protocol):
    """Resolve one ordered effective GF module-search path.

    The concrete adapter must delegate normalization, containment, ordering,
    deduplication, required/optional treatment, and native serialization to the
    centralized GF-path resolver used by compilation, scenarios, and PGF work.
    """

    def resolve(
        self,
        request: LanguageGfPathResolutionRequest,
    ) -> LanguageGfPathResolutionResult:
        """Return the effective GF path and provenance or structured issues."""
        ...


@runtime_checkable
class LanguagePreflightPort(Protocol):
    """Validate structural or capability-specific language prerequisites.

    The adapter should reuse the existing preflight service.  A structural
    language probe may establish source readiness without requiring GF, while a
    compile-capability preflight may require a resolved executable and effective
    GF path.
    """

    def check(
        self,
        request: LanguagePreflightRequest,
    ) -> LanguagePreflightResult:
        """Return preflight findings without launching validation stages."""
        ...


@runtime_checkable
class LanguageCompileVerifierPort(Protocol):
    """Optionally verify one explicit GF target through the normal compiler.

    This port is not required for source-only resolution.  Implementations must
    use the approved GF operation and process boundaries and must preserve raw
    execution evidence and canonical diagnostics.
    """

    def verify(
        self,
        request: LanguageCompileVerificationRequest,
    ) -> LanguageCompileVerificationResult:
        """Compile or load the requested target and return structured evidence."""
        ...


@runtime_checkable
class ExactModuleSearchPort(Protocol):
    """Perform bounded exact-name assistance beneath an approved RGL source root.

    A concrete adapter should reuse the existing source inventory and filename
    extraction contracts.  It must not perform fuzzy matching, search outside
    the approved root, choose among multiple matches, or add paths to the GF
    search path by itself.
    """

    def find_exact(
        self,
        request: ExactModuleSearchRequest,
    ) -> ExactModuleSearchResult:
        """Return zero, one, or several exact source-file matches."""
        ...
