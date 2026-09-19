"""Mechanism-neutral ports for path-resolved language startup."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = (
    "LanguageGFPathResolutionPort",
    "LanguageProbeClockPort",
    "LanguageSourceSelectionPort",
    "LanguageStructuralPreflightPort",
    "LanguageVerificationPort",
)


@runtime_checkable
class LanguageSourceSelectionPort(Protocol):
    """Select eligible GF sources below one approved language directory."""

    def __call__(self, *args: object, **kwargs: object) -> object: ...


@runtime_checkable
class LanguageGFPathResolutionPort(Protocol):
    """Resolve an ordered effective GF search path."""

    def __call__(self, *args: object, **kwargs: object) -> object: ...


@runtime_checkable
class LanguageStructuralPreflightPort(Protocol):
    """Check structural readiness without creating a validation run."""

    def __call__(self, *args: object, **kwargs: object) -> object: ...


@runtime_checkable
class LanguageVerificationPort(Protocol):
    """Optionally verify a resolved language through an approved boundary."""

    def __call__(self, *args: object, **kwargs: object) -> object: ...


@runtime_checkable
class LanguageProbeClockPort(Protocol):
    """Supply monotonic timestamps to bounded probe implementations."""

    def __call__(self) -> float: ...


# Non-exported compatibility names retained for callers migrating from the
# earlier over-specialized port vocabulary.
LanguageSourceInventoryPort = LanguageSourceSelectionPort
LanguageGfPathResolverPort = LanguageGFPathResolutionPort
LanguagePreflightPort = LanguageStructuralPreflightPort
LanguageCompileVerifierPort = LanguageVerificationPort
LanguageProbePort = LanguageVerificationPort
LanguageFilesystemPort = LanguageSourceSelectionPort
ExactModuleSearchPort = LanguageSourceSelectionPort
ModuleNameExtractor = object
