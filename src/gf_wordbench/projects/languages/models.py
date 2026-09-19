"""Immutable contracts for path-resolved language startup.

The models in this module describe one bounded attempt to turn an explicit GF
language directory or ``.gf`` file into one immutable language context.  They
contain no filesystem, GUI, process, compiler, state, or report behavior.

Validation profiles are intentionally absent.  They are optional run-policy
inputs resolved after a language context exists and must not become startup or
language-identity authorities.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Final

_GF_SUFFIX: Final[str] = ".gf"
_DIAGNOSTIC_CODE_RE: Final[re.Pattern[str]] = re.compile(r"^GF-WB-[A-Z][A-Z0-9]*-[0-9]{3}$")
_MODULE_SUFFIX_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Z][A-Za-z0-9_]*$")
_STANDARD_MODULE_FILE_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:Lang|Grammar|All|Syntax|Lexicon|Paradigms|Morpho|Cat|Noun|Verb|Structural)"
    r"(?P<suffix>[A-Z][A-Za-z0-9_]*)\.gf$"
)
_PROVENANCE_FIELD_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$"
)


@unique
class SelectedPathKind(StrEnum):
    """Kind of explicit path supplied to language startup."""

    DIRECTORY = "directory"
    FILE = "file"


# Compatibility alias for consumers written before the canonical rename.
# It is intentionally absent from ``__all__``.
LanguagePathKind = SelectedPathKind


@unique
class LanguageProbeStatus(StrEnum):
    """Terminal outcome of one language-probe request."""

    RESOLVED = "resolved"
    NEEDS_USER_INPUT = "needs_user_input"
    INVALID_SELECTION = "invalid_selection"
    UNSUPPORTED_LAYOUT = "unsupported_layout"
    CAPABILITY_UNAVAILABLE = "capability_unavailable"
    INTERNAL_ERROR = "internal_error"


@unique
class LanguageProbeSeverity(StrEnum):
    """Severity of one language-resolution diagnostic."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# The retired ``LanguageDiagnosticSeverity`` name is resolved lazily below so
# it does not become a second public contract owner.


@unique
class LanguageCapability(StrEnum):
    """Capability that may be exposed by a resolved language or run setup."""

    SOURCE_READY = "source_ready"
    SCAN_READY = "scan_ready"
    COMPILE_READY = "compile_ready"
    SCENARIO_READY = "scenario_ready"
    RELEASE_READY = "release_ready"


@unique
class CapabilityAvailability(StrEnum):
    """Availability state for one language capability."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@unique
class LanguageModuleRole(StrEnum):
    """Recognized standard RGL filename role.

    Recognition is a user-assistance classification only.  It does not assert
    that GF accepts the module or that the module is a release entrypoint.
    """

    LANG = "lang"
    GRAMMAR = "grammar"
    ALL = "all"
    SYNTAX = "syntax"
    LEXICON = "lexicon"
    PARADIGMS = "paradigms"
    MORPHO = "morpho"
    CAT = "cat"
    NOUN = "noun"
    VERB = "verb"
    STRUCTURAL = "structural"


@unique
class LanguageResolutionSource(StrEnum):
    """Source of one resolved language fact."""

    EXPLICIT_SELECTED_PATH = "explicit_selected_path"
    EXPLICIT_RGL_ROOT = "explicit_rgl_root"
    REMEMBERED_SELECTED_PATH = "remembered_selected_path"
    LANGUAGE_PROBE = "language_probe"
    SELECTION_SERVICE = "selection_service"
    MODULE_CLASSIFICATION = "module_classification"
    PATH_RESOLVER = "path_resolver"
    PREFLIGHT = "preflight"
    USER_CHOICE = "user_choice"
    LEGACY_MIGRATION = "legacy_migration"


@dataclass(frozen=True, slots=True)
class LanguageProbeRequest:
    """Explicit, bounded input to the pre-runtime language loader.

    The request describes one user-selected path.  It never selects a default
    language, opens a validation profile, creates a run, or authorizes the main
    Wordbench runtime.  Optional choices are responses to a previously reported
    ambiguity and remain explicit user input.
    """

    selected_path: Path
    explicit_rgl_root: Path | None = None
    max_ancestor_depth: int = 12
    max_source_files: int = 0
    require_unambiguous_suffix: bool = False
    module_suffix_choice: str | None = None
    entrypoint_choice: Path | None = None
    verify_with_gf: bool = False

    def __post_init__(self) -> None:
        selected_path = _require_absolute_path(
            self.selected_path,
            field="selected_path",
        )
        explicit_rgl_root = _require_optional_absolute_path(
            self.explicit_rgl_root,
            field="explicit_rgl_root",
        )
        module_suffix_choice = _require_optional_module_suffix(
            self.module_suffix_choice,
            field="module_suffix_choice",
        )
        entrypoint_choice = _require_optional_gf_path(
            self.entrypoint_choice,
            field="entrypoint_choice",
        )

        if type(self.max_ancestor_depth) is not int:
            raise TypeError("max_ancestor_depth must be an integer")
        if self.max_ancestor_depth < 1:
            raise ValueError("max_ancestor_depth must be at least 1")
        if type(self.max_source_files) is not int:
            raise TypeError("max_source_files must be an integer")
        if self.max_source_files < 0:
            raise ValueError("max_source_files must not be negative")
        if type(self.require_unambiguous_suffix) is not bool:
            raise TypeError("require_unambiguous_suffix must be a bool")
        if type(self.verify_with_gf) is not bool:
            raise TypeError("verify_with_gf must be a bool")

        # ``explicit_rgl_root`` is a dependency root, not necessarily the
        # physical owner of the selected language sources.  ADR-0015 permits
        # nonstandard/external GF source trees when their RGL dependency root
        # is supplied explicitly, so the two paths may be disjoint.
        if (
            entrypoint_choice is not None
            and module_suffix_choice is not None
            and not _path_stem(entrypoint_choice).endswith(module_suffix_choice)
        ):
            raise ValueError("entrypoint_choice must agree with module_suffix_choice")

        object.__setattr__(self, "selected_path", selected_path)
        object.__setattr__(self, "explicit_rgl_root", explicit_rgl_root)
        object.__setattr__(
            self,
            "module_suffix_choice",
            module_suffix_choice,
        )
        object.__setattr__(self, "entrypoint_choice", entrypoint_choice)


@dataclass(frozen=True, slots=True)
class LanguageModuleCandidate:
    """One standard RGL module-role candidate observed in the source tree."""

    file_path: Path
    role: LanguageModuleRole
    module_suffix: str

    def __post_init__(self) -> None:
        file_path = _require_gf_path(
            self.file_path,
            field="file_path",
        )
        if not isinstance(self.role, LanguageModuleRole):
            raise TypeError("role must be a LanguageModuleRole")
        module_suffix = _require_module_suffix(
            self.module_suffix,
            field="module_suffix",
        )

        expected_name = f"{_module_role_prefix(self.role)}{module_suffix}"
        if _path_stem(file_path) != expected_name:
            raise ValueError(
                "file_path stem must match role and module_suffix; "
                f"expected {expected_name!r}, got {_path_stem(file_path)!r}"
            )

        object.__setattr__(self, "file_path", file_path)
        object.__setattr__(self, "module_suffix", module_suffix)

    @property
    def module_name(self) -> str:
        """Return the filename-derived GF module-name candidate."""

        return _path_stem(self.file_path)

    @property
    def name(self) -> str:
        """Expose the underlying filename for path-compatible consumers."""

        return self.file_path.name

    def as_posix(self) -> str:
        """Return the underlying candidate path in portable form."""

        return self.file_path.as_posix()

    def __fspath__(self) -> str:
        return str(self.file_path)

    @property
    def entrypoint_priority(self) -> int | None:
        """Return the standard presentation rank for entrypoint-like roles."""

        priorities = {
            LanguageModuleRole.LANG: 0,
            LanguageModuleRole.GRAMMAR: 1,
            LanguageModuleRole.ALL: 2,
        }
        return priorities.get(self.role)


@dataclass(frozen=True, slots=True)
class LanguageProbeChoice:
    """One explicit choice offered by the loader to resolve ambiguity."""

    value: str
    label: str
    entrypoints: tuple[Path, ...] = ()

    def __post_init__(self) -> None:
        value = _require_single_line_text(
            self.value,
            field="value",
            allow_empty=False,
            allow_unicode=False,
        )
        label = _require_single_line_text(
            self.label,
            field="label",
            allow_empty=False,
            allow_unicode=True,
        )
        entrypoints = _require_path_tuple(
            self.entrypoints,
            field="entrypoints",
            require_gf_suffix=True,
        )
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "entrypoints", entrypoints)


@dataclass(frozen=True, slots=True)
class LanguageProbeDiagnostic:
    """One structured finding produced during language resolution."""

    code: str
    severity: LanguageProbeSeverity
    stage: str
    subject: str
    message: str
    remediation: str = ""
    detail: str = ""
    relevant_path: Path | None = None
    candidates: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        code = _require_diagnostic_code(self.code)
        if not isinstance(self.severity, LanguageProbeSeverity):
            raise TypeError("severity must be a LanguageProbeSeverity")
        stage = _require_single_line_text(
            self.stage,
            field="stage",
            allow_empty=False,
        )
        subject = _require_single_line_text(
            self.subject,
            field="subject",
            allow_empty=False,
            allow_unicode=True,
        )
        message = _require_single_line_text(
            self.message,
            field="message",
            allow_empty=False,
            allow_unicode=True,
        )
        remediation = _require_text(
            self.remediation,
            field="remediation",
            allow_empty=True,
            allow_unicode=True,
        )
        detail = _require_text(
            self.detail,
            field="detail",
            allow_empty=True,
            allow_unicode=True,
        )
        relevant_path = _require_optional_absolute_path(
            self.relevant_path,
            field="relevant_path",
        )
        candidates = _require_unique_text_tuple(
            self.candidates,
            field="candidates",
            allow_unicode=True,
        )

        if self.severity is LanguageProbeSeverity.ERROR and not remediation:
            raise ValueError("error diagnostics must provide remediation")

        object.__setattr__(self, "code", code)
        object.__setattr__(self, "stage", stage)
        object.__setattr__(self, "subject", subject)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "remediation", remediation)
        object.__setattr__(self, "detail", detail)
        object.__setattr__(self, "relevant_path", relevant_path)
        object.__setattr__(self, "candidates", candidates)

    @property
    def technical_detail(self) -> str:
        """Compatibility projection for older diagnostic renderers."""

        return self.detail

    @property
    def candidate_choices(self) -> tuple[str, ...]:
        """Compatibility projection for older ambiguity renderers."""

        return self.candidates


@dataclass(frozen=True, slots=True)
class LanguageCapabilityStatus:
    """Availability and explanation for one capability."""

    capability: LanguageCapability
    availability: CapabilityAvailability
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.capability, LanguageCapability):
            raise TypeError("capability must be a LanguageCapability")
        if not isinstance(self.availability, CapabilityAvailability):
            raise TypeError("availability must be a CapabilityAvailability")
        reason = _require_single_line_text(
            self.reason,
            field="reason",
            allow_empty=True,
            allow_unicode=True,
        )
        if self.availability is not CapabilityAvailability.AVAILABLE and not reason:
            raise ValueError("unavailable or unknown capabilities must provide a reason")
        object.__setattr__(self, "reason", reason)

    @property
    def available(self) -> bool:
        return self.availability is CapabilityAvailability.AVAILABLE


@dataclass(frozen=True, slots=True)
class LanguageResolutionProvenance:
    """Provenance for one diagnostically important resolved field."""

    field: str
    value: str
    source: LanguageResolutionSource

    def __post_init__(self) -> None:
        field = _require_single_line_text(
            self.field,
            field="field",
            allow_empty=False,
        )
        if _PROVENANCE_FIELD_RE.fullmatch(field) is None:
            raise ValueError("field must use lowercase dotted identifier syntax")
        value = _require_single_line_text(
            self.value,
            field="value",
            allow_empty=False,
            allow_unicode=True,
        )
        if not isinstance(self.source, LanguageResolutionSource):
            raise TypeError("source must be a LanguageResolutionSource")
        object.__setattr__(self, "field", field)
        object.__setattr__(self, "value", value)


@dataclass(frozen=True, slots=True)
class LanguageCandidate:
    """Provisional, non-executable facts derived from one selected path."""

    selected_path: Path
    selected_path_kind: SelectedPathKind
    language_directory: Path
    rgl_source_root: Path | None = None
    rgl_root: Path | None = None
    focused_target: Path | None = None
    candidate_language_key: str | None = None
    module_suffixes: tuple[str, ...] = ()
    module_candidates: tuple[LanguageModuleCandidate, ...] = ()
    source_inventory: tuple[Path, ...] = ()
    gf_path_requirements: tuple[Path, ...] = ()
    diagnostics: tuple[LanguageProbeDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        selected_path = _require_absolute_path(
            self.selected_path,
            field="selected_path",
        )
        if not isinstance(self.selected_path_kind, SelectedPathKind):
            raise TypeError("selected_path_kind must be a SelectedPathKind")
        language_directory = _require_absolute_path(
            self.language_directory,
            field="language_directory",
        )
        rgl_source_root = _require_optional_absolute_path(
            self.rgl_source_root,
            field="rgl_source_root",
        )
        rgl_root = _require_optional_absolute_path(
            self.rgl_root,
            field="rgl_root",
        )
        focused_target = _require_optional_gf_path(
            self.focused_target,
            field="focused_target",
        )
        candidate_language_key = _require_optional_language_key(
            self.candidate_language_key,
            field="candidate_language_key",
        )
        module_suffixes = _require_module_suffix_tuple(
            self.module_suffixes,
            field="module_suffixes",
        )
        module_candidates = _require_module_candidate_tuple(
            self.module_candidates,
            field="module_candidates",
        )
        source_inventory = _require_path_tuple(
            self.source_inventory,
            field="source_inventory",
            require_gf_suffix=True,
        )
        gf_path_requirements = _require_path_tuple(
            self.gf_path_requirements,
            field="gf_path_requirements",
            require_gf_suffix=False,
        )
        diagnostics = _require_diagnostic_tuple(
            self.diagnostics,
            field="diagnostics",
        )

        _validate_selected_path_relationship(
            selected_path=selected_path,
            selected_path_kind=self.selected_path_kind,
            language_directory=language_directory,
            focused_target=focused_target,
        )
        _validate_root_relationships(
            language_directory=language_directory,
            rgl_source_root=rgl_source_root,
            rgl_root=rgl_root,
        )
        _require_paths_contained(
            source_inventory,
            parent=language_directory,
            field="source_inventory",
        )
        _require_module_candidates_in_inventory(
            module_candidates,
            source_inventory=source_inventory,
        )
        _require_suffixes_cover_candidates(
            module_suffixes,
            candidates=module_candidates,
        )

        object.__setattr__(self, "selected_path", selected_path)
        object.__setattr__(self, "language_directory", language_directory)
        object.__setattr__(self, "rgl_source_root", rgl_source_root)
        object.__setattr__(self, "rgl_root", rgl_root)
        object.__setattr__(self, "focused_target", focused_target)
        object.__setattr__(
            self,
            "candidate_language_key",
            candidate_language_key,
        )
        object.__setattr__(self, "module_suffixes", module_suffixes)
        object.__setattr__(self, "module_candidates", module_candidates)
        object.__setattr__(self, "source_inventory", source_inventory)
        object.__setattr__(
            self,
            "gf_path_requirements",
            gf_path_requirements,
        )
        object.__setattr__(self, "diagnostics", diagnostics)

    @property
    def entrypoint_candidates(self) -> tuple[LanguageModuleCandidate, ...]:
        """Return standard entrypoint-like candidates in stored order."""

        return tuple(
            candidate
            for candidate in self.module_candidates
            if candidate.entrypoint_priority is not None
        )

    @property
    def display_name(self) -> str:
        """Return a local presentation label, never a portable identity."""

        return _path_name(self.language_directory)


@dataclass(frozen=True, slots=True, init=False)
class ResolvedLanguageContext:
    """Immutable language and source authority for one Wordbench runtime."""

    language_key: str
    selected_path: Path
    selected_path_kind: SelectedPathKind
    language_directory: Path
    rgl_source_root: Path
    rgl_root: Path | None
    focused_target: Path | None
    module_suffix: str | None
    available_entrypoints: tuple[LanguageModuleCandidate, ...]
    source_inventory: tuple[Path, ...]
    gf_path_requirements: tuple[Path, ...]
    structural_diagnostics: tuple[LanguageProbeDiagnostic, ...] = ()
    capability_statuses: tuple[LanguageCapabilityStatus, ...] = ()
    resolution_provenance: tuple[LanguageResolutionProvenance, ...] = ()

    def __init__(
        self,
        language_key: str,
        selected_path: Path,
        selected_path_kind: SelectedPathKind,
        language_directory: Path,
        rgl_source_root: Path,
        rgl_root: Path | None,
        focused_target: Path | None,
        module_suffix: str | None,
        available_entrypoints: tuple[LanguageModuleCandidate | Path, ...],
        source_inventory: tuple[Path, ...],
        gf_path_requirements: tuple[Path, ...],
        structural_diagnostics: tuple[LanguageProbeDiagnostic, ...] = (),
        capability_statuses: (tuple[LanguageCapabilityStatus, ...] | Mapping[str, bool]) = (),
        resolution_provenance: tuple[LanguageResolutionProvenance, ...] = (),
        *,
        selected_file: Path | None = None,
    ) -> None:
        if selected_file is not None and selected_file != selected_path:
            raise ValueError("selected_file conflicts with selected_path")

        normalized_target = focused_target
        if normalized_target is not None and not _is_absolute_path(normalized_target):
            normalized_target = language_directory / normalized_target

        normalized_entrypoints: list[LanguageModuleCandidate] = []
        for index, entrypoint in enumerate(available_entrypoints):
            if isinstance(entrypoint, LanguageModuleCandidate):
                normalized_entrypoints.append(entrypoint)
                continue
            if not isinstance(entrypoint, Path):
                raise TypeError(
                    f"available_entrypoints[{index}] must be a LanguageModuleCandidate or Path"
                )
            path = entrypoint if _is_absolute_path(entrypoint) else language_directory / entrypoint
            match = _STANDARD_MODULE_FILE_RE.fullmatch(_path_name(path))
            if match is None:
                raise ValueError("available entrypoint paths must use a standard GF role")
            prefix = _path_stem(path)[: -len(match.group("suffix"))]
            role = next(
                (
                    candidate_role
                    for candidate_role in LanguageModuleRole
                    if _module_role_prefix(candidate_role) == prefix
                ),
                None,
            )
            if role is None:
                raise ValueError("available entrypoint role is unsupported")
            normalized_entrypoints.append(
                LanguageModuleCandidate(
                    file_path=path,
                    role=role,
                    module_suffix=match.group("suffix"),
                )
            )

        normalized_capabilities: tuple[LanguageCapabilityStatus, ...]
        if isinstance(capability_statuses, Mapping):
            statuses: list[LanguageCapabilityStatus] = []
            for raw_name, available in capability_statuses.items():
                if not isinstance(raw_name, str) or type(available) is not bool:
                    raise TypeError("capability_statuses mappings require string/bool items")
                token = raw_name.replace("-", "_")
                try:
                    capability = LanguageCapability(token)
                except ValueError as exc:
                    raise ValueError(f"unsupported language capability {raw_name!r}") from exc
                statuses.append(
                    LanguageCapabilityStatus(
                        capability=capability,
                        availability=(
                            CapabilityAvailability.AVAILABLE
                            if available
                            else CapabilityAvailability.UNAVAILABLE
                        ),
                        reason="" if available else "Unavailable.",
                    )
                )
            normalized_capabilities = tuple(statuses)
        else:
            normalized_capabilities = tuple(capability_statuses)

        for name, value in (
            ("language_key", language_key),
            ("selected_path", selected_path),
            ("selected_path_kind", selected_path_kind),
            ("language_directory", language_directory),
            ("rgl_source_root", rgl_source_root),
            ("rgl_root", rgl_root),
            ("focused_target", normalized_target),
            ("module_suffix", module_suffix),
            ("available_entrypoints", tuple(normalized_entrypoints)),
            ("source_inventory", tuple(source_inventory)),
            ("gf_path_requirements", tuple(gf_path_requirements)),
            ("structural_diagnostics", tuple(structural_diagnostics)),
            ("capability_statuses", normalized_capabilities),
            ("resolution_provenance", tuple(resolution_provenance)),
        ):
            object.__setattr__(self, name, value)
        self.__post_init__()

    def __post_init__(self) -> None:
        language_key = _require_language_key(
            self.language_key,
            field="language_key",
        )
        selected_path = _require_absolute_path(
            self.selected_path,
            field="selected_path",
        )
        if not isinstance(self.selected_path_kind, SelectedPathKind):
            raise TypeError("selected_path_kind must be a SelectedPathKind")
        language_directory = _require_absolute_path(
            self.language_directory,
            field="language_directory",
        )
        rgl_source_root = _require_absolute_path(
            self.rgl_source_root,
            field="rgl_source_root",
        )
        rgl_root = _require_optional_absolute_path(
            self.rgl_root,
            field="rgl_root",
        )
        focused_target = _require_optional_gf_path(
            self.focused_target,
            field="focused_target",
        )
        module_suffix = _require_optional_module_suffix(
            self.module_suffix,
            field="module_suffix",
        )
        available_entrypoints = _require_module_candidate_tuple(
            self.available_entrypoints,
            field="available_entrypoints",
        )
        source_inventory = _require_path_tuple(
            self.source_inventory,
            field="source_inventory",
            require_gf_suffix=True,
            require_non_empty=True,
        )
        gf_path_requirements = _require_path_tuple(
            self.gf_path_requirements,
            field="gf_path_requirements",
            require_gf_suffix=False,
            require_non_empty=True,
        )
        structural_diagnostics = _require_diagnostic_tuple(
            self.structural_diagnostics,
            field="structural_diagnostics",
        )
        capability_statuses = _require_capability_status_tuple(
            self.capability_statuses,
            field="capability_statuses",
        )
        resolution_provenance = _require_provenance_tuple(
            self.resolution_provenance,
            field="resolution_provenance",
        )

        _validate_selected_path_relationship(
            selected_path=selected_path,
            selected_path_kind=self.selected_path_kind,
            language_directory=language_directory,
            focused_target=focused_target,
        )
        _validate_root_relationships(
            language_directory=language_directory,
            rgl_source_root=rgl_source_root,
            rgl_root=rgl_root,
        )
        _require_paths_contained(
            source_inventory,
            parent=language_directory,
            field="source_inventory",
        )
        _require_module_candidates_in_inventory(
            available_entrypoints,
            source_inventory=source_inventory,
        )
        if any(candidate.entrypoint_priority is None for candidate in available_entrypoints):
            raise ValueError("available_entrypoints may contain only Lang, Grammar, or All roles")
        if module_suffix is not None and any(
            candidate.module_suffix != module_suffix for candidate in available_entrypoints
        ):
            raise ValueError("available_entrypoints must agree with module_suffix")
        if focused_target is not None and not _contains_path(
            language_directory,
            focused_target,
            allow_equal=False,
        ):
            raise ValueError("focused_target must remain inside language_directory")
        if not any(
            status.capability is LanguageCapability.SOURCE_READY and status.available
            for status in capability_statuses
        ):
            raise ValueError("a resolved language context must be source-ready")

        object.__setattr__(self, "language_key", language_key)
        object.__setattr__(self, "selected_path", selected_path)
        object.__setattr__(self, "language_directory", language_directory)
        object.__setattr__(self, "rgl_source_root", rgl_source_root)
        object.__setattr__(self, "rgl_root", rgl_root)
        object.__setattr__(self, "focused_target", focused_target)
        object.__setattr__(self, "module_suffix", module_suffix)
        object.__setattr__(
            self,
            "available_entrypoints",
            available_entrypoints,
        )
        object.__setattr__(self, "source_inventory", source_inventory)
        object.__setattr__(
            self,
            "gf_path_requirements",
            gf_path_requirements,
        )
        object.__setattr__(
            self,
            "structural_diagnostics",
            structural_diagnostics,
        )
        object.__setattr__(
            self,
            "capability_statuses",
            capability_statuses,
        )
        object.__setattr__(
            self,
            "resolution_provenance",
            resolution_provenance,
        )

    @property
    def selected_file(self) -> Path | None:
        """Return the explicitly selected file, when startup began from one."""

        if self.selected_path_kind is SelectedPathKind.FILE:
            return self.selected_path
        return None

    @property
    def display_name(self) -> str:
        """Return a local presentation label distinct from language_key."""

        return _path_name(self.language_directory)

    @property
    def module_suffix_candidates(self) -> tuple[str, ...]:
        """Return every standard module suffix present in the source inventory."""

        suffixes: list[str] = []
        for path in self.source_inventory:
            match = _STANDARD_MODULE_FILE_RE.fullmatch(_path_name(path))
            if match is None:
                continue
            suffix = match.group("suffix")
            if suffix not in suffixes:
                suffixes.append(suffix)
        return tuple(sorted(suffixes, key=lambda value: value.casefold()))

    @property
    def entrypoint_paths(self) -> tuple[Path, ...]:
        """Return entrypoint paths for GUI and CLI presentation."""

        return tuple(candidate.file_path for candidate in self.available_entrypoints)

    def capability(
        self,
        capability: LanguageCapability,
    ) -> LanguageCapabilityStatus | None:
        """Return the recorded status for one capability, when present."""

        if not isinstance(capability, LanguageCapability):
            raise TypeError("capability must be a LanguageCapability")
        return next(
            (status for status in self.capability_statuses if status.capability is capability),
            None,
        )


@dataclass(frozen=True, slots=True)
class LanguageProbeResult:
    """Typed terminal result of one pre-runtime language-probe request."""

    status: LanguageProbeStatus
    candidate: LanguageCandidate | None = None
    context: ResolvedLanguageContext | None = None
    diagnostics: tuple[LanguageProbeDiagnostic, ...] = ()
    choices: tuple[LanguageProbeChoice, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, LanguageProbeStatus):
            raise TypeError("status must be a LanguageProbeStatus")
        if self.candidate is not None and not isinstance(
            self.candidate,
            LanguageCandidate,
        ):
            raise TypeError("candidate must be a LanguageCandidate or None")
        if self.context is not None and not isinstance(
            self.context,
            ResolvedLanguageContext,
        ):
            raise TypeError("context must be a ResolvedLanguageContext or None")
        diagnostics = _require_diagnostic_tuple(
            self.diagnostics,
            field="diagnostics",
        )
        choices = _require_choice_tuple(
            self.choices,
            field="choices",
        )

        if self.status is LanguageProbeStatus.RESOLVED:
            if self.context is None:
                raise ValueError("resolved probe results require a context")
            if choices:
                raise ValueError("resolved probe results must not publish ambiguity choices")
            if any(
                diagnostic.severity is LanguageProbeSeverity.ERROR for diagnostic in diagnostics
            ):
                raise ValueError("resolved probe results cannot contain error diagnostics")
        elif self.context is not None:
            raise ValueError("non-resolved probe results must not publish a context")

        if self.status is LanguageProbeStatus.NEEDS_USER_INPUT:
            if not choices:
                raise ValueError("needs-user-input results require explicit choices")
        elif choices:
            raise ValueError("only needs-user-input results may publish choices")

        if (
            self.status
            in {
                LanguageProbeStatus.INVALID_SELECTION,
                LanguageProbeStatus.UNSUPPORTED_LAYOUT,
                LanguageProbeStatus.CAPABILITY_UNAVAILABLE,
                LanguageProbeStatus.INTERNAL_ERROR,
            }
            and not diagnostics
        ):
            raise ValueError("unsuccessful probe results require diagnostics")

        object.__setattr__(self, "diagnostics", diagnostics)
        object.__setattr__(self, "choices", choices)

    @property
    def resolved(self) -> bool:
        """Return whether one immutable monolingual runtime context exists."""

        return self.status is LanguageProbeStatus.RESOLVED

    @property
    def is_resolved(self) -> bool:
        """Compatibility predicate used by startup and integration boundaries."""

        return self.resolved and self.context is not None

    @property
    def disposition(self) -> LanguageProbeStatus:
        """Compatibility presentation name for the canonical status."""

        return self.status

    @property
    def needs_user_input(self) -> bool:
        return self.status is LanguageProbeStatus.NEEDS_USER_INPUT


def __getattr__(name: str) -> object:
    if name == "LanguageDiagnosticSeverity":
        return LanguageProbeSeverity
    raise AttributeError(name)


# Validation helpers -------------------------------------------------------


def _require_diagnostic_code(value: object) -> str:
    text = _require_single_line_text(
        value,
        field="code",
        allow_empty=False,
    )
    if _DIAGNOSTIC_CODE_RE.fullmatch(text) is None:
        raise ValueError("code must match GF-WB-<DOMAIN>-<NNN>")
    return text


def _require_text(
    value: object,
    *,
    field: str,
    allow_empty: bool,
    allow_unicode: bool = False,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if not allow_empty and not value:
        raise ValueError(f"{field} must not be empty")
    if not allow_unicode and not value.isascii():
        raise ValueError(f"{field} must use ASCII characters only")
    return value


def _require_single_line_text(
    value: object,
    *,
    field: str,
    allow_empty: bool,
    allow_unicode: bool = False,
) -> str:
    text = _require_text(
        value,
        field=field,
        allow_empty=allow_empty,
        allow_unicode=allow_unicode,
    )
    if text != text.strip():
        raise ValueError(f"{field} must not contain surrounding whitespace")
    if "\r" in text or "\n" in text:
        raise ValueError(f"{field} must be a single-line string")
    return text


def _require_absolute_path(value: object, *, field: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be a pathlib.Path")
    rendered = os.fspath(value)
    if "\x00" in rendered:
        raise ValueError(f"{field} must not contain NUL")
    if not _is_absolute_path(value):
        raise ValueError(f"{field} must be absolute")
    if any(part == ".." for part in _path_parts(value)):
        raise ValueError(f"{field} must not contain unresolved parent traversal")
    return value


def _require_optional_absolute_path(
    value: object,
    *,
    field: str,
) -> Path | None:
    if value is None:
        return None
    return _require_absolute_path(value, field=field)


def _require_gf_path(value: object, *, field: str) -> Path:
    path = _require_absolute_path(value, field=field)
    if _path_suffix(path).casefold() != _GF_SUFFIX:
        raise ValueError(f"{field} must end in '.gf'")
    if not _path_stem(path):
        raise ValueError(f"{field} must have a non-empty stem")
    return path


def _require_optional_gf_path(
    value: object,
    *,
    field: str,
) -> Path | None:
    if value is None:
        return None
    return _require_gf_path(value, field=field)


def _require_module_suffix(value: object, *, field: str) -> str:
    text = _require_single_line_text(
        value,
        field=field,
        allow_empty=False,
    )
    if _MODULE_SUFFIX_RE.fullmatch(text) is None:
        raise ValueError(f"{field} must be an ASCII GF module suffix")
    return text


def _require_optional_module_suffix(
    value: object,
    *,
    field: str,
) -> str | None:
    if value is None:
        return None
    return _require_module_suffix(value, field=field)


def _require_language_key(value: object, *, field: str) -> str:
    text = _require_single_line_text(
        value,
        field=field,
        allow_empty=False,
    )
    if "\\" in text:
        raise ValueError(f"{field} must use '/' separators")
    posix = PurePosixPath(text)
    windows = PureWindowsPath(text)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise ValueError(f"{field} must be portable and relative")
    if text != posix.as_posix():
        raise ValueError(f"{field} must be canonically normalized")
    if any(part in {"", ".", ".."} for part in posix.parts):
        raise ValueError(f"{field} must not contain empty, current, or parent segments")
    return text


def _require_optional_language_key(
    value: object,
    *,
    field: str,
) -> str | None:
    if value is None:
        return None
    return _require_language_key(value, field=field)


def _require_unique_text_tuple(
    value: object,
    *,
    field: str,
    allow_unicode: bool,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field} must be a tuple")
    result: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        text = _require_single_line_text(
            item,
            field=f"{field}[{index}]",
            allow_empty=False,
            allow_unicode=allow_unicode,
        )
        if text in seen:
            raise ValueError(f"{field} must not contain duplicates")
        seen.add(text)
        result.append(text)
    return tuple(result)


def _require_module_suffix_tuple(
    value: object,
    *,
    field: str,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field} must be a tuple")
    result: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        suffix = _require_module_suffix(
            item,
            field=f"{field}[{index}]",
        )
        if suffix in seen:
            raise ValueError(f"{field} must not contain duplicates")
        seen.add(suffix)
        result.append(suffix)
    return tuple(result)


def _require_path_tuple(
    value: object,
    *,
    field: str,
    require_gf_suffix: bool,
    require_non_empty: bool = False,
) -> tuple[Path, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field} must be a tuple")
    if require_non_empty and not value:
        raise ValueError(f"{field} must not be empty")
    result: list[Path] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        path = (
            _require_gf_path(item, field=f"{field}[{index}]")
            if require_gf_suffix
            else _require_absolute_path(item, field=f"{field}[{index}]")
        )
        identity = _path_identity(path)
        if identity in seen:
            raise ValueError(f"{field} must not contain duplicates")
        seen.add(identity)
        result.append(path)
    return tuple(result)


def _require_module_candidate_tuple(
    value: object,
    *,
    field: str,
) -> tuple[LanguageModuleCandidate, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field} must be a tuple")
    result: list[LanguageModuleCandidate] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, LanguageModuleCandidate):
            raise TypeError(f"{field}[{index}] must be a LanguageModuleCandidate")
        identity = _path_identity(item.file_path)
        if identity in seen:
            raise ValueError(f"{field} must not contain duplicate paths")
        seen.add(identity)
        result.append(item)
    return tuple(result)


def _require_diagnostic_tuple(
    value: object,
    *,
    field: str,
) -> tuple[LanguageProbeDiagnostic, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field} must be a tuple")
    for index, item in enumerate(value):
        if not isinstance(item, LanguageProbeDiagnostic):
            raise TypeError(f"{field}[{index}] must be a LanguageProbeDiagnostic")
    return value


def _require_choice_tuple(
    value: object,
    *,
    field: str,
) -> tuple[LanguageProbeChoice, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field} must be a tuple")
    result: list[LanguageProbeChoice] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, LanguageProbeChoice):
            raise TypeError(f"{field}[{index}] must be a LanguageProbeChoice")
        if item.value in seen:
            raise ValueError(f"{field} must not contain duplicate values")
        seen.add(item.value)
        result.append(item)
    return tuple(result)


def _require_capability_status_tuple(
    value: object,
    *,
    field: str,
) -> tuple[LanguageCapabilityStatus, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field} must be a tuple")
    seen: set[LanguageCapability] = set()
    for index, item in enumerate(value):
        if not isinstance(item, LanguageCapabilityStatus):
            raise TypeError(f"{field}[{index}] must be a LanguageCapabilityStatus")
        if item.capability in seen:
            raise ValueError(f"{field} must contain at most one status per capability")
        seen.add(item.capability)
    return value


def _require_provenance_tuple(
    value: object,
    *,
    field: str,
) -> tuple[LanguageResolutionProvenance, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field} must be a tuple")
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, LanguageResolutionProvenance):
            raise TypeError(f"{field}[{index}] must be a LanguageResolutionProvenance")
        if item.field in seen:
            raise ValueError(f"{field} must contain at most one value per field")
        seen.add(item.field)
    return value


def _validate_selected_path_relationship(
    *,
    selected_path: Path,
    selected_path_kind: SelectedPathKind,
    language_directory: Path,
    focused_target: Path | None,
) -> None:
    if selected_path_kind is SelectedPathKind.FILE:
        if _path_suffix(selected_path).casefold() != _GF_SUFFIX:
            raise ValueError("a file selected_path must end in '.gf'")
        if _path_identity(_path_parent(selected_path)) != _path_identity(language_directory):
            raise ValueError("a selected file's parent must equal language_directory")
        if focused_target is None:
            raise ValueError("a file selection requires focused_target")
        if _path_identity(focused_target) != _path_identity(selected_path):
            raise ValueError("focused_target must preserve the explicitly selected file")
    else:
        if _path_identity(selected_path) != _path_identity(language_directory):
            raise ValueError("a selected directory must equal language_directory")
        if focused_target is not None:
            raise ValueError("a directory selection must not invent a focused target")


def _validate_root_relationships(
    *,
    language_directory: Path,
    rgl_source_root: Path | None,
    rgl_root: Path | None,
) -> None:
    if rgl_source_root is None:
        if rgl_root is not None:
            raise ValueError("rgl_root requires rgl_source_root")
        return

    # A standard RGL language normally lives below ``rgl_source_root``.
    # External GF projects are also valid when an explicit RGL dependency root
    # is supplied; in that case ``language_directory`` is intentionally
    # disjoint from ``rgl_source_root``.  Source containment is enforced
    # independently by ``source_inventory`` below.
    if _path_identity(rgl_source_root) == _path_identity(language_directory):
        raise ValueError("rgl_source_root must not equal language_directory")

    if rgl_root is not None:
        if not _contains_path(
            rgl_root,
            rgl_source_root,
            allow_equal=False,
        ):
            raise ValueError("rgl_root must contain rgl_source_root")
        if _path_identity(_path_parent(rgl_source_root)) != _path_identity(rgl_root):
            raise ValueError(
                "for the standard RGL layout, rgl_root must be the parent of rgl_source_root"
            )


def _require_paths_contained(
    paths: tuple[Path, ...],
    *,
    parent: Path,
    field: str,
) -> None:
    for index, path in enumerate(paths):
        if not _contains_path(parent, path, allow_equal=False):
            raise ValueError(f"{field}[{index}] must remain inside language_directory")


def _require_module_candidates_in_inventory(
    candidates: tuple[LanguageModuleCandidate, ...],
    *,
    source_inventory: tuple[Path, ...],
) -> None:
    inventory = {_path_identity(path) for path in source_inventory}
    for candidate in candidates:
        if _path_identity(candidate.file_path) not in inventory:
            raise ValueError("module candidate paths must exist in source_inventory")


def _require_suffixes_cover_candidates(
    suffixes: tuple[str, ...],
    *,
    candidates: tuple[LanguageModuleCandidate, ...],
) -> None:
    declared = set(suffixes)
    observed = {candidate.module_suffix for candidate in candidates}
    if observed != declared:
        raise ValueError("module_suffixes must equal the suffixes observed in module_candidates")


def _module_role_prefix(role: LanguageModuleRole) -> str:
    return {
        LanguageModuleRole.LANG: "Lang",
        LanguageModuleRole.GRAMMAR: "Grammar",
        LanguageModuleRole.ALL: "All",
        LanguageModuleRole.SYNTAX: "Syntax",
        LanguageModuleRole.LEXICON: "Lexicon",
        LanguageModuleRole.PARADIGMS: "Paradigms",
        LanguageModuleRole.MORPHO: "Morpho",
        LanguageModuleRole.CAT: "Cat",
        LanguageModuleRole.NOUN: "Noun",
        LanguageModuleRole.VERB: "Verb",
        LanguageModuleRole.STRUCTURAL: "Structural",
    }[role]


def _is_absolute_path(path: Path) -> bool:
    rendered = os.fspath(path)
    windows = PureWindowsPath(rendered)
    return path.is_absolute() or windows.is_absolute() or bool(windows.drive)


def _is_windows_style(path: Path) -> bool:
    rendered = os.fspath(path)
    windows = PureWindowsPath(rendered)
    return bool(windows.drive) or "\\" in rendered


def _path_parts(path: Path) -> tuple[str, ...]:
    rendered = os.fspath(path)
    if _is_windows_style(path):
        return PureWindowsPath(rendered).parts
    return path.parts


def _path_name(path: Path) -> str:
    rendered = os.fspath(path)
    if _is_windows_style(path):
        return PureWindowsPath(rendered).name
    return path.name


def _path_stem(path: Path) -> str:
    rendered = os.fspath(path)
    if _is_windows_style(path):
        return PureWindowsPath(rendered).stem
    return path.stem


def _path_suffix(path: Path) -> str:
    rendered = os.fspath(path)
    if _is_windows_style(path):
        return PureWindowsPath(rendered).suffix
    return path.suffix


def _path_parent(path: Path) -> Path:
    rendered = os.fspath(path)
    if _is_windows_style(path):
        return Path(str(PureWindowsPath(rendered).parent))
    return path.parent


def _path_identity(path: Path) -> str:
    rendered = os.fspath(path)
    if _is_windows_style(path):
        return str(PureWindowsPath(rendered)).casefold()
    return os.path.normcase(os.path.normpath(rendered))


def _contains_path(
    root: Path,
    candidate: Path | None,
    *,
    allow_equal: bool,
) -> bool:
    if candidate is None:
        return False
    if _is_windows_style(root) != _is_windows_style(candidate):
        return False

    root_parts = _comparison_parts(root)
    candidate_parts = _comparison_parts(candidate)
    if len(candidate_parts) < len(root_parts):
        return False
    if not allow_equal and len(candidate_parts) == len(root_parts):
        return False
    return candidate_parts[: len(root_parts)] == root_parts


def _comparison_parts(path: Path) -> tuple[str, ...]:
    parts = _path_parts(path)
    if _is_windows_style(path):
        return tuple(part.casefold() for part in parts)
    return parts


__all__ = (
    "LanguageCandidate",
    "LanguageCapability",
    "LanguageModuleCandidate",
    "LanguageProbeDiagnostic",
    "LanguageProbeRequest",
    "LanguageProbeResult",
    "LanguageProbeSeverity",
    "LanguageProbeStatus",
    "ResolvedLanguageContext",
    "SelectedPathKind",
)
