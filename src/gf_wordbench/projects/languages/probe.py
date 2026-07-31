"""Path-resolved language probing for GF Wordbench.

The probe starts from one explicit user-selected GF directory or ``.gf`` file.
It derives a bounded source context, delegates source enumeration to the
existing :mod:`gf_wordbench.validation.selection` service, classifies standard
RGL module roles, and publishes one immutable language context.

The probe does not invoke GF, parse GF source syntax, build subprocess commands,
write application state, load an implicit ``project.toml``, or generate reports.
Capability-specific environment and GF validation remain run-configuration and
preflight responsibilities.
"""

from __future__ import annotations

import os
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum, unique
from pathlib import Path
from typing import Final, Protocol, TypeAlias, runtime_checkable

from gf_wordbench.kernel.errors import GFWordbenchError
from gf_wordbench.validation.selection.service import (
    SelectionService,
    extract_module_name,
)

__all__ = (
    "BaseLanguageCapabilities",
    "LanguagePathKind",
    "LanguageProbeChoice",
    "LanguageProbeDiagnostic",
    "LanguageProbeFilesystem",
    "LanguageSourceSelector",
    "LanguageProbeRequest",
    "LanguageProbeResult",
    "LanguageProbeService",
    "LanguageProbeSeverity",
    "LanguageProbeStatus",
    "ResolvedLanguageContext",
    "probe_language_path",
)

PathInput: TypeAlias = str | os.PathLike[str]

_STANDARD_SOURCE_ROOT_NAME: Final[str] = "src"
_STANDARD_SOURCE_MARKERS: Final[tuple[str, ...]] = (
    "abstract",
    "api",
    "common",
    "prelude",
)
_ENTRYPOINT_ROLES: Final[tuple[str, ...]] = (
    "Lang",
    "Grammar",
    "All",
)
_STANDARD_MODULE_ROLES: Final[tuple[str, ...]] = (
    "Construction",
    "Structural",
    "Paradigms",
    "Adjective",
    "Sentence",
    "Grammar",
    "Lexicon",
    "Syntax",
    "Morpho",
    "Extend",
    "Noun",
    "Verb",
    "Lang",
    "All",
    "Res",
    "Cat",
)
_MODULE_ROLE_RE: Final[re.Pattern[str]] = re.compile(
    rf"^(?P<role>{'|'.join(_STANDARD_MODULE_ROLES)})"
    r"(?P<suffix>[A-Z][A-Za-z0-9_]*)$"
)
_GF_FILE_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z][A-Za-z0-9_]*\.gf$"
)


@unique
class LanguagePathKind(StrEnum):
    """Accepted kinds of explicit language selection."""

    DIRECTORY = "directory"
    GF_FILE = "gf_file"


@unique
class LanguageProbeStatus(StrEnum):
    """Terminal status of one language-probe request."""

    RESOLVED = "resolved"
    NEEDS_USER_INPUT = "needs_user_input"
    INVALID_SELECTION = "invalid_selection"
    UNSUPPORTED_LAYOUT = "unsupported_layout"
    INTERNAL_ERROR = "internal_error"


@unique
class LanguageProbeSeverity(StrEnum):
    """Severity of one probe diagnostic."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class LanguageProbeDiagnostic:
    """One structured language-resolution finding."""

    code: str
    severity: LanguageProbeSeverity
    stage: str
    subject: str
    message: str
    remediation: str
    detail: str = ""
    candidates: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "code",
            "stage",
            "subject",
            "message",
            "remediation",
        ):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")
            if not value.strip():
                raise ValueError(f"{name} must not be empty")
            if "\x00" in value:
                raise ValueError(f"{name} must not contain NUL")
        if not isinstance(self.severity, LanguageProbeSeverity):
            raise TypeError("severity must be a LanguageProbeSeverity")
        if not isinstance(self.detail, str):
            raise TypeError("detail must be a string")
        if "\x00" in self.detail:
            raise ValueError("detail must not contain NUL")
        if not isinstance(self.candidates, tuple):
            raise TypeError("candidates must be a tuple")
        for index, candidate in enumerate(self.candidates):
            if not isinstance(candidate, str) or not candidate:
                raise ValueError(
                    f"candidates[{index}] must be a non-empty string"
                )


@dataclass(frozen=True, slots=True)
class LanguageProbeChoice:
    """One explicit user choice required to resolve an ambiguity."""

    value: str
    label: str
    entrypoints: tuple[Path, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value:
            raise ValueError("value must be a non-empty string")
        if not isinstance(self.label, str) or not self.label:
            raise ValueError("label must be a non-empty string")
        _require_absolute_path_tuple(self.entrypoints, field="entrypoints")


@dataclass(frozen=True, slots=True)
class BaseLanguageCapabilities:
    """Capabilities established without requiring GF execution."""

    source_ready: bool
    scan_ready: bool

    def __post_init__(self) -> None:
        if type(self.source_ready) is not bool:
            raise TypeError("source_ready must be a bool")
        if type(self.scan_ready) is not bool:
            raise TypeError("scan_ready must be a bool")
        if self.scan_ready and not self.source_ready:
            raise ValueError("scan_ready requires source_ready")


@dataclass(frozen=True, slots=True)
class ResolvedLanguageContext:
    """Immutable source and language authority for one active runtime."""

    language_key: str
    display_name: str
    selected_path: Path
    selected_path_kind: LanguagePathKind
    language_directory: Path
    rgl_source_root: Path
    rgl_root: Path
    selected_file: Path | None
    focused_target: Path | None
    module_suffix: str | None
    module_suffix_candidates: tuple[str, ...]
    available_entrypoints: tuple[Path, ...]
    source_inventory: tuple[Path, ...]
    gf_path_requirements: tuple[Path, ...]
    capabilities: BaseLanguageCapabilities
    structural_diagnostics: tuple[LanguageProbeDiagnostic, ...]
    resolution_provenance: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.language_key, str) or not self.language_key:
            raise ValueError("language_key must be a non-empty string")
        if self.language_key.startswith("/") or "\\" in self.language_key:
            raise ValueError("language_key must be a portable relative value")
        if not isinstance(self.display_name, str) or not self.display_name:
            raise ValueError("display_name must be a non-empty string")
        if not isinstance(self.selected_path_kind, LanguagePathKind):
            raise TypeError("selected_path_kind must be a LanguagePathKind")

        selected_path = _require_absolute_path(
            self.selected_path,
            field="selected_path",
        )
        language_directory = _require_absolute_path(
            self.language_directory,
            field="language_directory",
        )
        rgl_source_root = _require_absolute_path(
            self.rgl_source_root,
            field="rgl_source_root",
        )
        rgl_root = _require_absolute_path(self.rgl_root, field="rgl_root")

        if not language_directory.is_relative_to(rgl_source_root):
            raise ValueError(
                "language_directory must be contained in rgl_source_root"
            )
        if language_directory == rgl_source_root:
            raise ValueError(
                "language_directory must identify a subtree of rgl_source_root"
            )
        if rgl_source_root.parent != rgl_root:
            raise ValueError("rgl_root must be the parent of rgl_source_root")

        selected_file = _require_optional_absolute_path(
            self.selected_file,
            field="selected_file",
        )
        focused_target = _require_optional_absolute_path(
            self.focused_target,
            field="focused_target",
        )
        if selected_file is not None and selected_file.parent != language_directory:
            raise ValueError(
                "selected_file must belong directly to language_directory"
            )
        if focused_target is not None and focused_target != selected_file:
            raise ValueError("focused_target must equal selected_file")

        if self.module_suffix is not None:
            if not isinstance(self.module_suffix, str):
                raise TypeError("module_suffix must be a string or None")
            if not re.fullmatch(r"[A-Z][A-Za-z0-9_]*", self.module_suffix):
                raise ValueError("module_suffix has an invalid format")

        suffix_candidates = _require_unique_text_tuple(
            self.module_suffix_candidates,
            field="module_suffix_candidates",
        )
        if (
            self.module_suffix is not None
            and self.module_suffix not in suffix_candidates
        ):
            raise ValueError(
                "module_suffix must be present in module_suffix_candidates"
            )

        entrypoints = _require_absolute_path_tuple(
            self.available_entrypoints,
            field="available_entrypoints",
        )
        inventory = _require_absolute_path_tuple(
            self.source_inventory,
            field="source_inventory",
        )
        gf_path = _require_absolute_path_tuple(
            self.gf_path_requirements,
            field="gf_path_requirements",
        )
        if not inventory:
            raise ValueError("source_inventory must not be empty")
        if language_directory not in gf_path:
            raise ValueError(
                "gf_path_requirements must contain language_directory"
            )
        if selected_file is not None and selected_file not in inventory:
            raise ValueError("selected_file must be present in source_inventory")
        if any(path not in inventory for path in entrypoints):
            raise ValueError(
                "available_entrypoints must be present in source_inventory"
            )
        if not isinstance(self.capabilities, BaseLanguageCapabilities):
            raise TypeError(
                "capabilities must be a BaseLanguageCapabilities"
            )
        if not isinstance(self.structural_diagnostics, tuple):
            raise TypeError("structural_diagnostics must be a tuple")
        for diagnostic in self.structural_diagnostics:
            if not isinstance(diagnostic, LanguageProbeDiagnostic):
                raise TypeError(
                    "structural_diagnostics must contain diagnostics"
                )
        provenance = _require_unique_text_tuple(
            self.resolution_provenance,
            field="resolution_provenance",
        )

        object.__setattr__(self, "selected_path", selected_path)
        object.__setattr__(self, "language_directory", language_directory)
        object.__setattr__(self, "rgl_source_root", rgl_source_root)
        object.__setattr__(self, "rgl_root", rgl_root)
        object.__setattr__(self, "selected_file", selected_file)
        object.__setattr__(self, "focused_target", focused_target)
        object.__setattr__(self, "module_suffix_candidates", suffix_candidates)
        object.__setattr__(self, "available_entrypoints", entrypoints)
        object.__setattr__(self, "source_inventory", inventory)
        object.__setattr__(self, "gf_path_requirements", gf_path)
        object.__setattr__(self, "resolution_provenance", provenance)


@dataclass(frozen=True, slots=True)
class LanguageProbeRequest:
    """Complete immutable input for one bounded language probe."""

    selected_path: PathInput
    explicit_rgl_root: PathInput | None = None
    max_ancestor_depth: int = 12
    max_source_files: int = 0
    require_unambiguous_suffix: bool = False

    def __post_init__(self) -> None:
        selected_path = _coerce_path(self.selected_path, field="selected_path")
        explicit_root = (
            None
            if self.explicit_rgl_root is None
            else _coerce_path(
                self.explicit_rgl_root,
                field="explicit_rgl_root",
            )
        )
        if isinstance(self.max_ancestor_depth, bool) or not isinstance(
            self.max_ancestor_depth,
            int,
        ):
            raise TypeError("max_ancestor_depth must be an integer")
        if self.max_ancestor_depth < 1:
            raise ValueError("max_ancestor_depth must be at least 1")
        if isinstance(self.max_source_files, bool) or not isinstance(
            self.max_source_files,
            int,
        ):
            raise TypeError("max_source_files must be an integer")
        if self.max_source_files < 0:
            raise ValueError("max_source_files must not be negative")
        if type(self.require_unambiguous_suffix) is not bool:
            raise TypeError("require_unambiguous_suffix must be a bool")
        object.__setattr__(self, "selected_path", selected_path)
        object.__setattr__(self, "explicit_rgl_root", explicit_root)


@dataclass(frozen=True, slots=True)
class LanguageProbeResult:
    """Terminal result of one language-probe request."""

    status: LanguageProbeStatus
    context: ResolvedLanguageContext | None = None
    diagnostics: tuple[LanguageProbeDiagnostic, ...] = ()
    choices: tuple[LanguageProbeChoice, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, LanguageProbeStatus):
            raise TypeError("status must be a LanguageProbeStatus")
        if self.context is not None and not isinstance(
            self.context,
            ResolvedLanguageContext,
        ):
            raise TypeError(
                "context must be a ResolvedLanguageContext or None"
            )
        if self.status is LanguageProbeStatus.RESOLVED:
            if self.context is None:
                raise ValueError("resolved result requires a context")
        elif self.context is not None:
            raise ValueError("non-resolved result must not expose a context")
        if not isinstance(self.diagnostics, tuple):
            raise TypeError("diagnostics must be a tuple")
        for diagnostic in self.diagnostics:
            if not isinstance(diagnostic, LanguageProbeDiagnostic):
                raise TypeError("diagnostics must contain diagnostics")
        if not isinstance(self.choices, tuple):
            raise TypeError("choices must be a tuple")
        for choice in self.choices:
            if not isinstance(choice, LanguageProbeChoice):
                raise TypeError("choices must contain LanguageProbeChoice")
        if (
            self.status is LanguageProbeStatus.NEEDS_USER_INPUT
            and not self.choices
        ):
            raise ValueError("needs_user_input result requires choices")

    @property
    def resolved(self) -> bool:
        """Whether the result contains a usable language context."""

        return self.status is LanguageProbeStatus.RESOLVED


@runtime_checkable
class LanguageSourceSelector(Protocol):
    """Public source-inventory contract consumed by the language probe."""

    def select_source_tree(
        self,
        source_root: Path,
        *,
        containment_root: Path,
        max_files: int = 0,
    ) -> tuple[Sequence[Path], Sequence[object]]:
        """Return deterministic selected sources and exclusion evidence."""


@runtime_checkable
class LanguageProbeFilesystem(Protocol):
    """Filesystem operations required before source selection."""

    def resolve(self, path: Path, *, strict: bool) -> Path:
        ...

    def exists(self, path: Path) -> bool:
        ...

    def is_file(self, path: Path) -> bool:
        ...

    def is_directory(self, path: Path) -> bool:
        ...

    def is_readable(self, path: Path) -> bool:
        ...


class _LocalLanguageProbeFilesystem:
    __slots__ = ()

    def resolve(self, path: Path, *, strict: bool) -> Path:
        return path.expanduser().resolve(strict=strict)

    def exists(self, path: Path) -> bool:
        return path.exists()

    def is_file(self, path: Path) -> bool:
        return path.is_file()

    def is_directory(self, path: Path) -> bool:
        return path.is_dir()

    def is_readable(self, path: Path) -> bool:
        return os.access(path, os.R_OK)


_LOCAL_FILESYSTEM: Final[LanguageProbeFilesystem] = (
    _LocalLanguageProbeFilesystem()
)


@dataclass(frozen=True, slots=True)
class _RootResolution:
    rgl_source_root: Path
    rgl_root: Path
    provenance: str


@dataclass(frozen=True, slots=True)
class _ModuleClassification:
    module_suffix: str | None
    suffix_candidates: tuple[str, ...]
    entrypoints: tuple[Path, ...]
    choices: tuple[LanguageProbeChoice, ...]
    diagnostics: tuple[LanguageProbeDiagnostic, ...]


@dataclass(frozen=True, slots=True)
class LanguageProbeService:
    """Coordinate bounded path discovery through existing public services."""

    selection_service: LanguageSourceSelector = field(
        default_factory=SelectionService
    )
    filesystem: LanguageProbeFilesystem = _LOCAL_FILESYSTEM

    def __post_init__(self) -> None:
        if not isinstance(self.selection_service, LanguageSourceSelector):
            raise TypeError(
                "selection_service must satisfy LanguageSourceSelector"
            )
        if not isinstance(self.filesystem, LanguageProbeFilesystem):
            raise TypeError(
                "filesystem must satisfy LanguageProbeFilesystem"
            )

    def probe(self, request: LanguageProbeRequest) -> LanguageProbeResult:
        """Resolve one selected path into one immutable language context."""

        if not isinstance(request, LanguageProbeRequest):
            raise TypeError("request must be a LanguageProbeRequest")

        selection = self._resolve_selected_path(request.selected_path)
        if isinstance(selection, LanguageProbeResult):
            return selection
        selected_path, path_kind, language_directory, selected_file = selection

        roots = self._resolve_roots(
            language_directory=language_directory,
            explicit_rgl_root=request.explicit_rgl_root,
            max_ancestor_depth=request.max_ancestor_depth,
        )
        if isinstance(roots, LanguageProbeResult):
            return roots

        try:
            inventory = self._select_language_sources(
                language_directory=language_directory,
                rgl_source_root=roots.rgl_source_root,
                max_source_files=request.max_source_files,
            )
        except GFWordbenchError as exc:
            return LanguageProbeResult(
                status=LanguageProbeStatus.INVALID_SELECTION,
                diagnostics=(
                    _diagnostic_from_wordbench_error(
                        exc,
                        subject=str(language_directory),
                    ),
                ),
            )
        except (OSError, TypeError, ValueError) as exc:
            return LanguageProbeResult(
                status=LanguageProbeStatus.INTERNAL_ERROR,
                diagnostics=(
                    LanguageProbeDiagnostic(
                        code="GF-WB-INTERNAL-251",
                        severity=LanguageProbeSeverity.ERROR,
                        stage="language_probe",
                        subject=str(language_directory),
                        message="Source inventory could not be constructed.",
                        detail=f"{type(exc).__name__}: {exc}",
                        remediation=(
                            "Review the selected path and the public source-"
                            "selection contract."
                        ),
                    ),
                ),
            )

        if not inventory:
            return LanguageProbeResult(
                status=LanguageProbeStatus.INVALID_SELECTION,
                diagnostics=(
                    LanguageProbeDiagnostic(
                        code="GF-WB-CONFIG-251",
                        severity=LanguageProbeSeverity.ERROR,
                        stage="language_probe",
                        subject=str(language_directory),
                        message=(
                            "The selected language directory contains no "
                            "eligible GF source files."
                        ),
                        remediation=(
                            "Select a directory containing readable .gf files "
                            "or select one .gf file directly."
                        ),
                    ),
                ),
            )

        if selected_file is not None and selected_file not in inventory:
            return LanguageProbeResult(
                status=LanguageProbeStatus.INVALID_SELECTION,
                diagnostics=(
                    LanguageProbeDiagnostic(
                        code="GF-WB-CONFIG-252",
                        severity=LanguageProbeSeverity.ERROR,
                        stage="language_probe",
                        subject=str(selected_file),
                        message=(
                            "The explicitly selected GF file was excluded by "
                            "the canonical source-selection service."
                        ),
                        remediation=(
                            "Review file readability, containment and source-"
                            "selection filters."
                        ),
                    ),
                ),
            )

        language_key = _portable_language_key(
            language_directory,
            rgl_source_root=roots.rgl_source_root,
        )
        classification = _classify_modules(
            inventory,
            focused_target=selected_file,
        )

        if (
            request.require_unambiguous_suffix
            and len(classification.suffix_candidates) > 1
            and classification.module_suffix is None
        ):
            return LanguageProbeResult(
                status=LanguageProbeStatus.NEEDS_USER_INPUT,
                diagnostics=classification.diagnostics,
                choices=classification.choices,
            )

        diagnostics = list(classification.diagnostics)
        if not classification.entrypoints:
            diagnostics.append(
                LanguageProbeDiagnostic(
                    code="GF-WB-CONFIG-253",
                    severity=LanguageProbeSeverity.INFO,
                    stage="language_probe",
                    subject=str(language_directory),
                    message=(
                        "No standard Lang, Grammar or All entrypoint was "
                        "identified."
                    ),
                    remediation=(
                        "Continue with explicit file targets or load an "
                        "optional validation profile when entrypoints are "
                        "required."
                    ),
                )
            )

        context = ResolvedLanguageContext(
            language_key=language_key,
            display_name=language_directory.name,
            selected_path=selected_path,
            selected_path_kind=path_kind,
            language_directory=language_directory,
            rgl_source_root=roots.rgl_source_root,
            rgl_root=roots.rgl_root,
            selected_file=selected_file,
            focused_target=selected_file,
            module_suffix=classification.module_suffix,
            module_suffix_candidates=classification.suffix_candidates,
            available_entrypoints=classification.entrypoints,
            source_inventory=inventory,
            gf_path_requirements=(language_directory,),
            capabilities=BaseLanguageCapabilities(
                source_ready=True,
                scan_ready=True,
            ),
            structural_diagnostics=tuple(diagnostics),
            resolution_provenance=(
                "explicit_selected_path",
                "bounded_ancestor_resolution",
                roots.provenance,
                "selection_service",
                "standard_module_role_classification",
            ),
        )
        return LanguageProbeResult(
            status=LanguageProbeStatus.RESOLVED,
            context=context,
            diagnostics=tuple(diagnostics),
        )

    def _resolve_selected_path(
        self,
        selected_path: Path,
    ) -> tuple[Path, LanguagePathKind, Path, Path | None] | LanguageProbeResult:
        try:
            resolved = self.filesystem.resolve(selected_path, strict=True)
        except (FileNotFoundError, OSError, RuntimeError) as exc:
            return LanguageProbeResult(
                status=LanguageProbeStatus.INVALID_SELECTION,
                diagnostics=(
                    LanguageProbeDiagnostic(
                        code="GF-WB-PATH-250",
                        severity=LanguageProbeSeverity.ERROR,
                        stage="language_probe",
                        subject=str(selected_path),
                        message="The selected language path is not usable.",
                        detail=f"{type(exc).__name__}: {exc}",
                        remediation=(
                            "Select an existing readable language directory "
                            "or .gf file."
                        ),
                    ),
                ),
            )

        if not self.filesystem.exists(resolved):
            return _invalid_path_result(
                resolved,
                code="GF-WB-PATH-251",
                message="The selected language path does not exist.",
            )
        if not self.filesystem.is_readable(resolved):
            return _invalid_path_result(
                resolved,
                code="GF-WB-IO-250",
                message="The selected language path is not readable.",
            )
        if self.filesystem.is_file(resolved):
            if resolved.suffix.casefold() != ".gf":
                return _invalid_path_result(
                    resolved,
                    code="GF-WB-CONFIG-254",
                    message="The selected file is not a .gf source file.",
                )
            if _GF_FILE_RE.fullmatch(resolved.name) is None:
                return _invalid_path_result(
                    resolved,
                    code="GF-WB-CONFIG-255",
                    message=(
                        "The selected .gf filename is not a valid module-file "
                        "candidate."
                    ),
                )
            return (
                resolved,
                LanguagePathKind.GF_FILE,
                resolved.parent,
                resolved,
            )
        if self.filesystem.is_directory(resolved):
            return (
                resolved,
                LanguagePathKind.DIRECTORY,
                resolved,
                None,
            )
        return _invalid_path_result(
            resolved,
            code="GF-WB-CONFIG-256",
            message=(
                "The selected path is neither a regular .gf file nor a "
                "directory."
            ),
        )

    def _resolve_roots(
        self,
        *,
        language_directory: Path,
        explicit_rgl_root: Path | None,
        max_ancestor_depth: int,
    ) -> _RootResolution | LanguageProbeResult:
        if explicit_rgl_root is not None:
            explicit = self._resolve_explicit_root(
                explicit_rgl_root,
                language_directory=language_directory,
            )
            if explicit is not None:
                return explicit
            return LanguageProbeResult(
                status=LanguageProbeStatus.UNSUPPORTED_LAYOUT,
                diagnostics=(
                    LanguageProbeDiagnostic(
                        code="GF-WB-PATH-252",
                        severity=LanguageProbeSeverity.ERROR,
                        stage="language_probe",
                        subject=str(explicit_rgl_root),
                        message=(
                            "The explicit RGL root does not contain the "
                            "selected language directory."
                        ),
                        remediation=(
                            "Select the matching gf-rgl repository root or its "
                            "src directory."
                        ),
                    ),
                ),
            )

        for depth, ancestor in enumerate(language_directory.parents, start=1):
            if depth > max_ancestor_depth:
                break
            if ancestor.name.casefold() != _STANDARD_SOURCE_ROOT_NAME:
                continue
            if language_directory == ancestor:
                continue
            if not language_directory.is_relative_to(ancestor):
                continue
            if not self._is_standard_source_root(ancestor):
                continue
            return _RootResolution(
                rgl_source_root=ancestor,
                rgl_root=ancestor.parent,
                provenance=self._source_root_provenance(ancestor),
            )

        return LanguageProbeResult(
            status=LanguageProbeStatus.UNSUPPORTED_LAYOUT,
            diagnostics=(
                LanguageProbeDiagnostic(
                    code="GF-WB-PATH-253",
                    severity=LanguageProbeSeverity.ERROR,
                    stage="language_probe",
                    subject=str(language_directory),
                    message=(
                        "A supported RGL source root could not be derived from "
                        "the selected path."
                    ),
                    remediation=(
                        "Select a language below <gf-rgl>/src or provide an "
                        "explicit RGL root."
                    ),
                ),
            ),
        )

    def _is_standard_source_root(self, source_root: Path) -> bool:
        """Whether an implicitly discovered ``src`` matches RGL structure."""

        if self.filesystem.is_file(source_root / "languages.csv"):
            return True
        marker_count = sum(
            self.filesystem.is_directory(source_root / marker)
            for marker in _STANDARD_SOURCE_MARKERS
        )
        return marker_count >= 2

    def _source_root_provenance(self, source_root: Path) -> str:
        if self.filesystem.is_file(source_root / "languages.csv"):
            return "standard_src_root_with_languages_csv"
        return "standard_src_root_with_shared_directories"

    def _resolve_explicit_root(
        self,
        value: Path,
        *,
        language_directory: Path,
    ) -> _RootResolution | None:
        try:
            root = self.filesystem.resolve(value, strict=True)
        except (FileNotFoundError, OSError, RuntimeError):
            return None
        if not self.filesystem.is_directory(root):
            return None
        if not self.filesystem.is_readable(root):
            return None

        source_candidates: list[tuple[Path, Path, str]] = []
        if root.name.casefold() == _STANDARD_SOURCE_ROOT_NAME:
            source_candidates.append(
                (root, root.parent, "explicit_rgl_source_root")
            )
        source_candidates.append(
            (root / _STANDARD_SOURCE_ROOT_NAME, root, "explicit_rgl_root")
        )

        for source_root, rgl_root, provenance in source_candidates:
            try:
                resolved_source = self.filesystem.resolve(
                    source_root,
                    strict=True,
                )
            except (FileNotFoundError, OSError, RuntimeError):
                continue
            if not self.filesystem.is_directory(resolved_source):
                continue
            if language_directory == resolved_source:
                continue
            if not language_directory.is_relative_to(resolved_source):
                continue
            return _RootResolution(
                rgl_source_root=resolved_source,
                rgl_root=rgl_root,
                provenance=provenance,
            )
        return None

    def _select_language_sources(
        self,
        *,
        language_directory: Path,
        rgl_source_root: Path,
        max_source_files: int,
    ) -> tuple[Path, ...]:
        selected, _excluded = self.selection_service.select_source_tree(
            language_directory,
            containment_root=rgl_source_root,
            max_files=max_source_files,
        )
        return tuple(selected)


def probe_language_path(
    selected_path: PathInput,
    *,
    explicit_rgl_root: PathInput | None = None,
    max_ancestor_depth: int = 12,
    max_source_files: int = 0,
    require_unambiguous_suffix: bool = False,
    selection_service: LanguageSourceSelector | None = None,
    filesystem: LanguageProbeFilesystem | None = None,
) -> LanguageProbeResult:
    """Convenience entrypoint for one path-resolved language probe."""

    service = LanguageProbeService(
        selection_service=(
            SelectionService()
            if selection_service is None
            else selection_service
        ),
        filesystem=filesystem or _LOCAL_FILESYSTEM,
    )
    return service.probe(
        LanguageProbeRequest(
            selected_path=selected_path,
            explicit_rgl_root=explicit_rgl_root,
            max_ancestor_depth=max_ancestor_depth,
            max_source_files=max_source_files,
            require_unambiguous_suffix=require_unambiguous_suffix,
        )
    )



def _classify_modules(
    inventory: Sequence[Path],
    *,
    focused_target: Path | None,
) -> _ModuleClassification:
    role_records: dict[str, list[tuple[str, Path]]] = {}
    entrypoint_records: dict[str, list[tuple[str, Path]]] = {}

    for path in inventory:
        module_name = extract_module_name(path)
        match = _MODULE_ROLE_RE.fullmatch(module_name)
        if match is None:
            continue
        role = match.group("role")
        suffix = match.group("suffix")
        role_records.setdefault(suffix, []).append((role, path))
        if role in _ENTRYPOINT_ROLES:
            entrypoint_records.setdefault(suffix, []).append((role, path))

    focused_suffix = _focused_suffix(focused_target)
    entrypoint_suffixes = tuple(sorted(entrypoint_records))
    role_suffixes = tuple(sorted(role_records))

    module_suffix: str | None = None
    candidates: tuple[str, ...]
    diagnostics: list[LanguageProbeDiagnostic] = []

    if len(entrypoint_suffixes) == 1:
        module_suffix = entrypoint_suffixes[0]
        candidates = entrypoint_suffixes
    elif len(entrypoint_suffixes) > 1:
        candidates = entrypoint_suffixes
        if focused_suffix in entrypoint_records:
            module_suffix = focused_suffix
            diagnostics.append(
                LanguageProbeDiagnostic(
                    code="GF-WB-CONFIG-257",
                    severity=LanguageProbeSeverity.INFO,
                    stage="language_probe",
                    subject=str(focused_target),
                    message=(
                        "The focused file disambiguated multiple standard "
                        "module suffixes."
                    ),
                    remediation=(
                        "Review the detected entrypoints before release "
                        "validation."
                    ),
                    candidates=candidates,
                )
            )
        else:
            diagnostics.append(
                _suffix_ambiguity_diagnostic(candidates)
            )
    elif len(role_suffixes) == 1:
        module_suffix = role_suffixes[0]
        candidates = role_suffixes
    elif len(role_suffixes) > 1:
        candidates = role_suffixes
        if focused_suffix in role_records:
            module_suffix = focused_suffix
            diagnostics.append(
                LanguageProbeDiagnostic(
                    code="GF-WB-CONFIG-258",
                    severity=LanguageProbeSeverity.INFO,
                    stage="language_probe",
                    subject=str(focused_target),
                    message=(
                        "The focused file selected one suffix from multiple "
                        "standard module-role candidates."
                    ),
                    remediation=(
                        "Use an explicit validation profile when a different "
                        "module family is required."
                    ),
                    candidates=candidates,
                )
            )
        else:
            diagnostics.append(_suffix_ambiguity_diagnostic(candidates))
    else:
        candidates = ()
        diagnostics.append(
            LanguageProbeDiagnostic(
                code="GF-WB-CONFIG-259",
                severity=LanguageProbeSeverity.INFO,
                stage="language_probe",
                subject="module_suffix",
                message=(
                    "No standard RGL module suffix could be derived from "
                    "filenames."
                ),
                remediation=(
                    "Continue with explicit file targets or supply an "
                    "optional validation profile."
                ),
            )
        )

    entrypoints = _ordered_entrypoints(
        entrypoint_records,
        selected_suffix=module_suffix,
    )
    choices = tuple(
        LanguageProbeChoice(
            value=suffix,
            label=suffix,
            entrypoints=_ordered_role_paths(entrypoint_records.get(suffix, [])),
        )
        for suffix in candidates
    )
    return _ModuleClassification(
        module_suffix=module_suffix,
        suffix_candidates=candidates,
        entrypoints=entrypoints,
        choices=choices,
        diagnostics=tuple(diagnostics),
    )


def _focused_suffix(path: Path | None) -> str | None:
    if path is None:
        return None
    match = _MODULE_ROLE_RE.fullmatch(extract_module_name(path))
    return None if match is None else match.group("suffix")


def _ordered_entrypoints(
    records: dict[str, list[tuple[str, Path]]],
    *,
    selected_suffix: str | None,
) -> tuple[Path, ...]:
    if selected_suffix is not None:
        return _ordered_role_paths(records.get(selected_suffix, []))
    all_records = [item for values in records.values() for item in values]
    return _ordered_role_paths(all_records)


def _ordered_role_paths(
    records: Sequence[tuple[str, Path]],
) -> tuple[Path, ...]:
    role_order = {role: index for index, role in enumerate(_ENTRYPOINT_ROLES)}
    ordered = sorted(
        records,
        key=lambda item: (
            role_order.get(item[0], len(role_order)),
            item[1].name.casefold(),
            str(item[1]),
        ),
    )
    return tuple(path for _role, path in ordered)


def _suffix_ambiguity_diagnostic(
    candidates: tuple[str, ...],
) -> LanguageProbeDiagnostic:
    return LanguageProbeDiagnostic(
        code="GF-WB-CONFIG-260",
        severity=LanguageProbeSeverity.WARNING,
        stage="language_probe",
        subject="module_suffix",
        message="Several standard RGL module suffixes were detected.",
        remediation=(
            "Select one suffix when the requested operation requires an "
            "unambiguous module family."
        ),
        candidates=candidates,
    )



def _portable_language_key(
    language_directory: Path,
    *,
    rgl_source_root: Path,
) -> str:
    relative = language_directory.relative_to(rgl_source_root)
    key = relative.as_posix()
    if key in {"", "."}:
        raise ValueError("language key must identify a source-root subtree")
    return key


def _diagnostic_from_wordbench_error(
    exc: GFWordbenchError,
    *,
    subject: str,
) -> LanguageProbeDiagnostic:
    code = exc.code or "GF-WB-CONFIG-261"
    detail = getattr(exc, "detail", "") or str(exc)
    return LanguageProbeDiagnostic(
        code=code,
        severity=LanguageProbeSeverity.ERROR,
        stage="language_probe",
        subject=subject,
        message=exc.message,
        detail=detail,
        remediation=(
            "Correct the selected source path or its canonical selection "
            "configuration."
        ),
    )


def _invalid_path_result(
    path: Path,
    *,
    code: str,
    message: str,
) -> LanguageProbeResult:
    return LanguageProbeResult(
        status=LanguageProbeStatus.INVALID_SELECTION,
        diagnostics=(
            LanguageProbeDiagnostic(
                code=code,
                severity=LanguageProbeSeverity.ERROR,
                stage="language_probe",
                subject=str(path),
                message=message,
                remediation=(
                    "Select an existing readable GF language directory or "
                    ".gf file."
                ),
            ),
        ),
    )


def _coerce_path(value: PathInput, *, field: str) -> Path:
    if isinstance(value, str):
        text = value
    elif isinstance(value, os.PathLike):
        text = os.fspath(value)
    else:
        raise TypeError(f"{field} must be a string or os.PathLike")
    if not isinstance(text, str):
        raise TypeError(f"{field} must resolve to text")
    if not text:
        raise ValueError(f"{field} must not be empty")
    if "\x00" in text:
        raise ValueError(f"{field} must not contain NUL")
    return Path(text)


def _require_absolute_path(value: Path, *, field: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be a pathlib.Path")
    if not value.is_absolute():
        raise ValueError(f"{field} must be absolute")
    normalized = Path(os.path.normpath(os.fspath(value)))
    if normalized != value:
        raise ValueError(f"{field} must be lexically normalized")
    return value


def _require_optional_absolute_path(
    value: Path | None,
    *,
    field: str,
) -> Path | None:
    if value is None:
        return None
    return _require_absolute_path(value, field=field)


def _require_absolute_path_tuple(
    value: tuple[Path, ...],
    *,
    field: str,
) -> tuple[Path, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field} must be a tuple")
    seen: set[str] = set()
    for index, path in enumerate(value):
        normalized = _require_absolute_path(
            path,
            field=f"{field}[{index}]",
        )
        key = os.path.normcase(os.fspath(normalized))
        if key in seen:
            raise ValueError(f"{field} must not contain duplicate paths")
        seen.add(key)
    return value


def _require_unique_text_tuple(
    value: tuple[str, ...],
    *,
    field: str,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field} must be a tuple")
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            raise ValueError(f"{field}[{index}] must be a non-empty string")
        if item in seen:
            raise ValueError(f"{field} must not contain duplicates")
        seen.add(item)
    return value
