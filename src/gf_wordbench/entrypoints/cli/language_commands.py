"""CLI adapter for path-resolved language probing.

This module owns only command-line translation and result projection for the
ADR-0015 language-probe use case. It does not enumerate source files, resolve
GF paths, execute GF, read application state, or inspect the filesystem beyond
validating path-shaped CLI values.

Concrete dependency composition belongs to :mod:`gf_wordbench.bootstrap`.
The canonical one-argument handler obtains its application boundary lazily from
``build_language_probe_application()`` so importing this module remains free of
composition and filesystem side effects.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum, StrEnum, unique
from pathlib import Path
from types import MappingProxyType
from typing import Final, Protocol, TypeAlias, runtime_checkable

from gf_wordbench.kernel.statuses import OverallStatus

from .parser import CliRequest, CliUsageError

_LANGUAGE_PROBE_CANONICAL_COMMAND: Final[str] = "language.probe"
_MAX_TEXT_LENGTH: Final[int] = 32_768
_MAX_ANCESTOR_DEPTH: Final[int] = 256
_MAX_REMEDIATION_PATHS: Final[int] = 256

ProbeValue: TypeAlias = object


@unique
class LanguageProbeOutcome(StrEnum):
    """Canonical terminal outcome of one language-probe request."""

    RESOLVED = "resolved"
    NEEDS_USER_INPUT = "needs_user_input"
    INVALID_SELECTION = "invalid_selection"
    UNSUPPORTED_LAYOUT = "unsupported_layout"
    CAPABILITY_UNAVAILABLE = "capability_unavailable"
    INTERNAL_ERROR = "internal_error"


@unique
class SelectedPathKind(StrEnum):
    """Accepted kind of explicit startup selection."""

    FILE = "file"
    DIRECTORY = "directory"


@dataclass(frozen=True, slots=True)
class LanguageProbeCommandRequest:
    """Normalized CLI input for one path-resolved language probe."""

    selected_path: Path
    explicit_rgl_root: Path | None = None
    validation_profile: Path | None = None
    gf_executable: Path | None = None
    verify_gf: bool = False
    allow_exact_path_remediation: bool = False
    strict: bool = False
    max_ancestor_depth: int = 16
    max_remediation_paths: int = 10
    quiet: bool = False
    verbose: bool = False

    def __post_init__(self) -> None:
        _require_path(self.selected_path, field="selected_path")
        for field_name in (
            "explicit_rgl_root",
            "validation_profile",
            "gf_executable",
        ):
            _require_optional_path(
                getattr(self, field_name),
                field=field_name,
            )
        for field_name in (
            "verify_gf",
            "allow_exact_path_remediation",
            "strict",
            "quiet",
            "verbose",
        ):
            _require_bool(getattr(self, field_name), field=field_name)
        if self.quiet and self.verbose:
            raise ValueError("quiet and verbose cannot both be enabled")
        _require_bounded_positive_int(
            self.max_ancestor_depth,
            field="max_ancestor_depth",
            maximum=_MAX_ANCESTOR_DEPTH,
        )
        _require_bounded_nonnegative_int(
            self.max_remediation_paths,
            field="max_remediation_paths",
            maximum=_MAX_REMEDIATION_PATHS,
        )
        if not self.allow_exact_path_remediation and self.max_remediation_paths != 0:
            object.__setattr__(self, "max_remediation_paths", 0)

    @property
    def language_path(self) -> Path:
        """Compatibility alias for the explicit selected language path."""

        return self.selected_path

    @property
    def selected_language_path(self) -> Path:
        """Compatibility alias shared with other ADR-0015 CLI requests."""

        return self.selected_path

    @property
    def rgl_root(self) -> Path | None:
        """Compatibility alias for the explicit RGL root."""

        return self.explicit_rgl_root

    @property
    def validation_profile_path(self) -> Path | None:
        """Compatibility alias for the optional validation profile."""

        return self.validation_profile

    @property
    def profile_path(self) -> Path | None:
        """Temporary compatibility alias for the validation profile."""

        return self.validation_profile

    @property
    def gf_exe(self) -> Path | None:
        """Compatibility alias for the configured GF executable."""

        return self.gf_executable

    @property
    def verify_with_gf(self) -> bool:
        """Compatibility alias for the canonical GF verification flag."""

        return self.verify_gf


@dataclass(frozen=True, slots=True)
class LanguageProbeIssue:
    """Bounded CLI projection of one probe diagnostic."""

    severity: str
    code: str
    stage: str
    message: str
    path: Path | None = None
    remediation: str | None = None
    candidates: tuple[Path, ...] = ()

    def __post_init__(self) -> None:
        severity = _require_choice(
            self.severity,
            field="severity",
            allowed={"error", "warning", "info"},
        )
        object.__setattr__(self, "severity", severity)
        for field_name in ("code", "stage", "message"):
            _require_text(getattr(self, field_name), field=field_name)
        _require_optional_path(self.path, field="path")
        if self.remediation is not None:
            _require_text(self.remediation, field="remediation")
        candidates = tuple(self.candidates)
        for index, candidate in enumerate(candidates):
            _require_path(candidate, field=f"candidates[{index}]")
        object.__setattr__(self, "candidates", candidates)


@runtime_checkable
class LanguageProbeResultLike(Protocol):
    """Minimum application-result surface consumed by this CLI adapter."""

    @property
    def diagnostics(self) -> Sequence[object]: ...


@runtime_checkable
class LanguageProbeApplication(Protocol):
    """Application boundary consumed by the language-probe CLI adapter."""

    def probe_language(
        self,
        request: LanguageProbeCommandRequest,
    ) -> LanguageProbeResultLike: ...


@dataclass(frozen=True, slots=True)
class LanguageCommandServices:
    """Validated dependencies used by the language-probe CLI adapter."""

    application: LanguageProbeApplication

    def __post_init__(self) -> None:
        _require_language_probe_application(self.application)


@dataclass(frozen=True, slots=True)
class LanguageProbeCommandResult(Mapping[str, object]):
    """Structured, printable result of one path-resolved language probe."""

    overall_status: OverallStatus
    outcome: LanguageProbeOutcome
    selected_path: Path
    selected_path_kind: SelectedPathKind | None = None
    language_key: str | None = None
    language_directory: Path | None = None
    rgl_source_root: Path | None = None
    rgl_root: Path | None = None
    focused_target: Path | None = None
    module_suffix: str | None = None
    available_entrypoints: tuple[Path, ...] = ()
    capabilities: tuple[str, ...] = ()
    diagnostics: tuple[LanguageProbeIssue, ...] = ()
    message: str = "Language probe completed."

    def __post_init__(self) -> None:
        if not isinstance(self.overall_status, OverallStatus):
            raise TypeError("overall_status must be OverallStatus")
        if not isinstance(self.outcome, LanguageProbeOutcome):
            raise TypeError("outcome must be LanguageProbeOutcome")
        _require_path(self.selected_path, field="selected_path")
        if self.selected_path_kind is not None and not isinstance(
            self.selected_path_kind,
            SelectedPathKind,
        ):
            raise TypeError("selected_path_kind must be SelectedPathKind or None")
        for field_name in (
            "language_directory",
            "rgl_source_root",
            "rgl_root",
            "focused_target",
        ):
            _require_optional_path(getattr(self, field_name), field=field_name)
        for field_name in ("language_key", "module_suffix"):
            value = getattr(self, field_name)
            if value is not None:
                _require_text(value, field=field_name)
        entrypoints = tuple(self.available_entrypoints)
        for index, path in enumerate(entrypoints):
            _require_path(path, field=f"available_entrypoints[{index}]")
        object.__setattr__(self, "available_entrypoints", entrypoints)
        capabilities = _normalize_unique_texts(
            self.capabilities,
            field="capabilities",
        )
        object.__setattr__(self, "capabilities", capabilities)
        diagnostics = tuple(self.diagnostics)
        for index, diagnostic in enumerate(diagnostics):
            if not isinstance(diagnostic, LanguageProbeIssue):
                raise TypeError(
                    "diagnostics must contain LanguageProbeIssue values; "
                    f"item {index} is {type(diagnostic).__name__}"
                )
        object.__setattr__(self, "diagnostics", diagnostics)
        _require_text(self.message, field="message")

        expected = _overall_status_for_outcome(self.outcome)
        if self.overall_status is not expected:
            raise ValueError("overall_status must agree with outcome")
        if self.outcome is LanguageProbeOutcome.RESOLVED:
            if self.language_key is None:
                raise ValueError("resolved result requires language_key")
            if self.language_directory is None:
                raise ValueError("resolved result requires language_directory")

    @property
    def ok(self) -> bool:
        return self.overall_status is OverallStatus.OK

    @property
    def errors(self) -> tuple[LanguageProbeIssue, ...]:
        return tuple(item for item in self.diagnostics if item.severity == "error")

    @property
    def warnings(self) -> tuple[LanguageProbeIssue, ...]:
        return tuple(item for item in self.diagnostics if item.severity == "warning")

    def __getitem__(self, key: str) -> object:
        return self._public_mapping()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._public_mapping())

    def __len__(self) -> int:
        return len(self._public_mapping())

    def _public_mapping(self) -> Mapping[str, object]:
        values: dict[str, object] = {
            "overall_status": self.overall_status,
            "outcome": self.outcome,
            "selected_path": self.selected_path,
            "message": self.message,
        }
        optional_values: tuple[tuple[str, object | None], ...] = (
            ("selected_path_kind", self.selected_path_kind),
            ("language_key", self.language_key),
            ("language_directory", self.language_directory),
            ("rgl_source_root", self.rgl_source_root),
            ("rgl_root", self.rgl_root),
            ("focused_target", self.focused_target),
            ("module_suffix", self.module_suffix),
        )
        for name, value in optional_values:
            if value is not None:
                values[name] = value
        if self.available_entrypoints:
            values["available_entrypoints"] = self.available_entrypoints
        if self.capabilities:
            values["capabilities"] = self.capabilities
        if self.diagnostics:
            values["diagnostics"] = self.diagnostics
        return MappingProxyType(values)

    @classmethod
    def from_probe_result(
        cls,
        result: LanguageProbeResultLike,
        *,
        fallback_selected_path: Path,
    ) -> LanguageProbeCommandResult:
        """Project one application result into the canonical CLI result."""

        _require_probe_result(result)
        outcome = _coerce_outcome(_result_value(result, "outcome", "status"))
        selected_path = _coerce_path(
            _result_value(
                result,
                "selected_path",
                default=fallback_selected_path,
            ),
            field="result.selected_path",
        )
        diagnostics = tuple(
            _project_issue(item, index=index)
            for index, item in enumerate(tuple(result.diagnostics))
        )
        message = _optional_result_text(result, "message") or _default_message(
            outcome,
            diagnostics=diagnostics,
        )
        language_key = _optional_result_text(
            result,
            "language_key",
            "candidate_language_key",
        )
        return cls(
            overall_status=_overall_status_for_outcome(outcome),
            outcome=outcome,
            selected_path=selected_path,
            selected_path_kind=_optional_path_kind(result),
            language_key=language_key,
            language_directory=_optional_result_path(
                result,
                "language_directory",
            ),
            rgl_source_root=_optional_result_path(
                result,
                "rgl_source_root",
            ),
            rgl_root=_optional_result_path(result, "rgl_root"),
            focused_target=_optional_result_path(
                result,
                "focused_target",
            ),
            module_suffix=_optional_result_text(
                result,
                "module_suffix",
            ),
            available_entrypoints=_result_paths(
                result,
                "available_entrypoints",
            ),
            capabilities=_result_capabilities(result),
            diagnostics=diagnostics,
            message=message,
        )


def language_probe_request_from_cli_request(
    request: CliRequest,
) -> LanguageProbeCommandRequest:
    """Translate one canonical CLI request into a language-probe request."""

    _require_cli_command(request, _LANGUAGE_PROBE_CANONICAL_COMMAND)
    selected = _request_first(
        request,
        "language_path",
        "selected_path",
        "path",
    )
    if selected is None:
        raise CliUsageError("language probe requires a language directory or .gf file")
    return LanguageProbeCommandRequest(
        selected_path=_coerce_path(selected, field="language_path"),
        explicit_rgl_root=_optional_path(
            _request_first(request, "rgl_root", "explicit_rgl_root"),
            field="rgl_root",
        ),
        validation_profile=_optional_path(
            _request_first(
                request,
                "validation_profile",
                "profile",
                "project_file",
            ),
            field="validation_profile",
        ),
        gf_executable=_optional_path(
            _request_first(request, "gf_executable", "gf_exe"),
            field="gf_executable",
        ),
        verify_gf=_request_bool(request, "verify_gf"),
        allow_exact_path_remediation=_request_bool(
            request,
            "allow_exact_path_remediation",
        ),
        strict=_request_bool(request, "strict"),
        max_ancestor_depth=_request_int(
            request,
            "max_ancestor_depth",
            default=16,
        ),
        max_remediation_paths=_request_int(
            request,
            "max_remediation_paths",
            default=10,
        ),
        quiet=_request_bool(request, "quiet"),
        verbose=_request_bool(request, "verbose"),
    )


def language_probe_request_from_namespace(
    namespace: argparse.Namespace,
) -> LanguageProbeCommandRequest:
    """Translate one normalized argparse namespace into a probe request."""

    if not isinstance(namespace, argparse.Namespace):
        raise TypeError("namespace must be argparse.Namespace")

    command = getattr(namespace, "_command", None)
    if command is not None:
        command_name = _coerce_enum_text(
            command,
            field="namespace._command",
        ).lower()
        if command_name != _LANGUAGE_PROBE_CANONICAL_COMMAND:
            raise CliUsageError("namespace must identify language.probe")

    selected = _namespace_first(
        namespace,
        "language_path",
        "selected_language_path",
        "selected_path",
        "path",
    )
    if selected is None:
        raise CliUsageError("language probe requires a language directory or .gf file")

    return LanguageProbeCommandRequest(
        selected_path=_coerce_path(
            selected,
            field="language_path",
        ),
        explicit_rgl_root=_optional_path(
            _namespace_first(
                namespace,
                "rgl_root",
                "explicit_rgl_root",
            ),
            field="rgl_root",
        ),
        validation_profile=_optional_path(
            _namespace_first(
                namespace,
                "validation_profile",
                "validation_profile_path",
                "profile",
                "profile_path",
                "project_file",
            ),
            field="validation_profile",
        ),
        gf_executable=_optional_path(
            _namespace_first(
                namespace,
                "gf_executable",
                "gf_exe",
            ),
            field="gf_executable",
        ),
        verify_gf=_namespace_bool(
            namespace,
            "verify_gf",
            "verify_with_gf",
        ),
        allow_exact_path_remediation=_namespace_bool(
            namespace,
            "allow_exact_path_remediation",
        ),
        strict=_namespace_bool(namespace, "strict"),
        max_ancestor_depth=_namespace_int(
            namespace,
            "max_ancestor_depth",
            default=16,
        ),
        max_remediation_paths=_namespace_int(
            namespace,
            "max_remediation_paths",
            default=10,
        ),
        quiet=_namespace_bool(namespace, "quiet"),
        verbose=_namespace_bool(namespace, "verbose"),
    )


def execute_language_probe_command(
    request: CliRequest | argparse.Namespace,
    *,
    services: LanguageCommandServices | None = None,
) -> LanguageProbeCommandResult | LanguageProbeResultLike:
    """Execute one language-probe command through validated dependencies.

    ``CliRequest`` is the canonical process-entrypoint surface and returns the
    CLI projection. ``argparse.Namespace`` remains as a temporary compatibility
    surface for direct adapter tests and returns the application result.
    """

    active_services = services or _build_language_command_services()
    if not isinstance(active_services, LanguageCommandServices):
        raise TypeError("services must be LanguageCommandServices or None")

    if isinstance(request, argparse.Namespace):
        typed_request = language_probe_request_from_namespace(request)
        return active_services.application.probe_language(typed_request)

    if isinstance(request, CliRequest):
        typed_request = language_probe_request_from_cli_request(request)
        return run_language_probe(
            typed_request,
            active_services.application,
        )

    raise TypeError("request must be CliRequest or argparse.Namespace")


def run_language_probe(
    request: LanguageProbeCommandRequest,
    application: LanguageProbeApplication,
) -> LanguageProbeCommandResult:
    """Invoke the injected language-probe application and project its result."""

    if not isinstance(request, LanguageProbeCommandRequest):
        raise TypeError("request must be LanguageProbeCommandRequest")
    _require_language_probe_application(application)
    result = application.probe_language(request)
    return LanguageProbeCommandResult.from_probe_result(
        result,
        fallback_selected_path=request.selected_path,
    )


def _build_language_command_services() -> LanguageCommandServices:
    """Compose fresh command dependencies without a global service locator."""

    from gf_wordbench.bootstrap import build_language_probe_application

    return LanguageCommandServices(
        application=_require_language_probe_application(
            build_language_probe_application()
        ),
    )


def _build_language_probe_application() -> LanguageProbeApplication:
    """Compatibility helper returning the freshly composed application."""

    return _build_language_command_services().application


def _require_language_probe_application(
    application: object,
) -> LanguageProbeApplication:
    if not isinstance(application, LanguageProbeApplication):
        raise TypeError("application must satisfy LanguageProbeApplication")
    return application


def _require_probe_result(result: object) -> LanguageProbeResultLike:
    if not isinstance(result, LanguageProbeResultLike):
        raise TypeError("probe_language() must return LanguageProbeResultLike")
    if isinstance(result.diagnostics, (str, bytes, bytearray, Mapping)):
        raise TypeError("result.diagnostics must be a sequence of diagnostics")
    return result


def _project_issue(value: object, *, index: int) -> LanguageProbeIssue:
    prefix = f"result.diagnostics[{index}]"
    if isinstance(value, LanguageProbeIssue):
        return value
    if isinstance(value, Mapping):
        getter = value.get
    else:
        getter = lambda name, default=None: getattr(value, name, default)

    severity = _coerce_enum_text(
        getter("severity", "error"),
        field=f"{prefix}.severity",
    )
    code = _coerce_required_text(
        getter("code", "GF-WB-LANG-UNKNOWN"),
        field=f"{prefix}.code",
    )
    stage = _coerce_required_text(
        getter("stage", "language_probe"),
        field=f"{prefix}.stage",
    )
    message = _coerce_required_text(
        getter("message", value),
        field=f"{prefix}.message",
    )
    path = _optional_path(
        getter("path", getter("relevant_path")),
        field=f"{prefix}.path",
    )
    remediation_value = getter("remediation")
    remediation = (
        None
        if remediation_value in (None, "")
        else _coerce_required_text(
            remediation_value,
            field=f"{prefix}.remediation",
        )
    )
    candidates = _coerce_path_sequence(
        getter("candidate_choices", getter("candidates", ())),
        field=f"{prefix}.candidates",
    )
    return LanguageProbeIssue(
        severity=severity.lower(),
        code=code,
        stage=stage,
        message=message,
        path=path,
        remediation=remediation,
        candidates=candidates,
    )


def _overall_status_for_outcome(outcome: LanguageProbeOutcome) -> OverallStatus:
    if outcome is LanguageProbeOutcome.RESOLVED:
        return OverallStatus.OK
    if outcome is LanguageProbeOutcome.INTERNAL_ERROR:
        return OverallStatus.ERROR
    return OverallStatus.FAIL


def _default_message(
    outcome: LanguageProbeOutcome,
    *,
    diagnostics: tuple[LanguageProbeIssue, ...],
) -> str:
    if outcome is LanguageProbeOutcome.RESOLVED:
        return "Language path resolved successfully."
    if outcome is LanguageProbeOutcome.NEEDS_USER_INPUT:
        return "Language resolution requires an explicit user choice."
    if outcome is LanguageProbeOutcome.INVALID_SELECTION:
        return "The selected language path is invalid."
    if outcome is LanguageProbeOutcome.UNSUPPORTED_LAYOUT:
        return "The selected source layout is not supported without explicit configuration."
    if outcome is LanguageProbeOutcome.CAPABILITY_UNAVAILABLE:
        return "The requested language capability is unavailable."
    errors = sum(item.severity == "error" for item in diagnostics)
    return f"Language probing failed with an internal error ({errors} diagnostic error(s))."


def _optional_path_kind(
    result: object,
) -> SelectedPathKind | None:
    value = _result_value(
        result,
        "selected_path_kind",
        default=None,
    )
    if value is None:
        return None
    text = _coerce_enum_text(
        value,
        field="result.selected_path_kind",
    ).lower()
    try:
        return SelectedPathKind(text)
    except ValueError as exc:
        raise ValueError(f"unknown selected path kind: {text!r}") from exc


def _coerce_outcome(value: object) -> LanguageProbeOutcome:
    text = _coerce_enum_text(
        value,
        field="result.outcome",
    ).lower()
    try:
        return LanguageProbeOutcome(text)
    except ValueError as exc:
        raise ValueError(f"unknown language probe outcome: {text!r}") from exc


def _optional_result_text(
    result: object,
    *names: str,
) -> str | None:
    value = _result_value(result, *names, default=None)
    if value is None:
        return None
    return _coerce_required_text(
        value,
        field=f"result.{names[0]}",
    )


def _optional_result_path(
    result: object,
    *names: str,
) -> Path | None:
    return _optional_path(
        _result_value(result, *names, default=None),
        field=f"result.{names[0]}",
    )


def _result_paths(
    result: object,
    name: str,
) -> tuple[Path, ...]:
    value = _result_value(result, name, default=())
    values = _coerce_sequence(value, field=f"result.{name}")
    paths: list[Path] = []
    for index, item in enumerate(values):
        path_value = getattr(item, "file_path", item)
        paths.append(
            _coerce_path(
                path_value,
                field=f"result.{name}[{index}]",
            )
        )
    if len(set(paths)) != len(paths):
        raise ValueError(f"result.{name} must not contain duplicate paths")
    return tuple(paths)


def _result_capabilities(result: object) -> tuple[str, ...]:
    direct = _result_value(
        result,
        "capabilities",
        default=None,
        include_nested=False,
    )
    if direct is not None:
        return _result_texts_from_value(
            direct,
            field="result.capabilities",
        )

    context = getattr(result, "context", None)
    statuses = getattr(context, "capability_statuses", ())
    capabilities: list[str] = []
    for status in tuple(statuses):
        if not bool(getattr(status, "available", False)):
            continue
        capability = getattr(status, "capability", None)
        if capability is None:
            continue
        capabilities.append(
            _coerce_required_text(
                capability,
                field="result.capability_statuses.capability",
            )
        )
    return _normalize_unique_texts(
        capabilities,
        field="result.capabilities",
    )


def _result_texts_from_value(
    value: object,
    *,
    field: str,
) -> tuple[str, ...]:
    if value is None:
        return ()
    values: tuple[object, ...]
    if isinstance(value, Mapping):
        values = tuple(str(key) for key, enabled in value.items() if enabled)
    else:
        values = _coerce_sequence(value, field=field)
    return _normalize_unique_texts(values, field=field)


def _result_value(
    result: object,
    *names: str,
    default: object = None,
    include_nested: bool = True,
) -> object:
    for name in names:
        value = getattr(result, name, None)
        if value is not None:
            return value

    if include_nested:
        for owner_name in ("context", "candidate"):
            owner = getattr(result, owner_name, None)
            if owner is None:
                continue
            for name in names:
                value = getattr(owner, name, None)
                if value is not None:
                    return value

    return default


def _require_cli_command(request: CliRequest, expected: str) -> None:
    if not isinstance(request, CliRequest):
        raise TypeError("request must be CliRequest")
    actual = _coerce_enum_text(request.command, field="request.command").lower()
    if actual != expected:
        raise CliUsageError(f"CLI request must identify {expected}")


def _request_first(request: CliRequest, *names: str) -> object:
    for name in names:
        value = request.get(name)
        if value is not None:
            return value
    return None


def _namespace_first(
    namespace: argparse.Namespace,
    *names: str,
) -> object:
    for name in names:
        value = getattr(namespace, name, None)
        if value is not None:
            return value
    return None


def _namespace_bool(
    namespace: argparse.Namespace,
    *names: str,
) -> bool:
    value = _namespace_first(namespace, *names)
    if value is None:
        return False
    return _require_bool(value, field=names[0])


def _namespace_int(
    namespace: argparse.Namespace,
    name: str,
    *,
    default: int,
) -> int:
    value = getattr(namespace, name, None)
    if value is None:
        return default
    if type(value) is not int:
        raise CliUsageError(f"{name} must be an integer")
    return value


def _request_bool(request: CliRequest, name: str) -> bool:
    value = request.get(name, False)
    if value is None:
        return False
    return _require_bool(value, field=name)


def _request_int(request: CliRequest, name: str, *, default: int) -> int:
    value = request.get(name, default)
    if value is None:
        return default
    if type(value) is not int:
        raise CliUsageError(f"{name} must be an integer")
    return value


def _optional_path(value: object, *, field: str) -> Path | None:
    if value is None:
        return None
    return _coerce_path(value, field=field)


def _coerce_path(value: object, *, field: str) -> Path:
    if isinstance(value, Path):
        path = value
    elif isinstance(value, str):
        if not value.strip():
            raise ValueError(f"{field} must not be empty")
        path = Path(value)
    else:
        raise TypeError(f"{field} must be a path")
    return _require_path(path, field=field)


def _coerce_path_sequence(value: object, *, field: str) -> tuple[Path, ...]:
    values = _coerce_sequence(value, field=field)
    paths = tuple(
        _coerce_path(item, field=f"{field}[{index}]") for index, item in enumerate(values)
    )
    if len(set(paths)) != len(paths):
        raise ValueError(f"{field} must not contain duplicate paths")
    return paths


def _coerce_sequence(value: object, *, field: str) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray, Mapping)):
        raise TypeError(f"{field} must be a sequence")
    if not isinstance(value, Sequence):
        raise TypeError(f"{field} must be a sequence")
    return tuple(value)


def _normalize_unique_texts(value: object, *, field: str) -> tuple[str, ...]:
    values = _coerce_sequence(value, field=field)
    normalized: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        text = _coerce_required_text(item, field=f"{field}[{index}]")
        if text in seen:
            raise ValueError(f"{field} contains duplicate value {text!r}")
        seen.add(text)
        normalized.append(text)
    return tuple(normalized)


def _coerce_required_text(value: object, *, field: str) -> str:
    if isinstance(value, Enum):
        value = value.value
    if not isinstance(value, str):
        value = str(value)
    return _require_text(value, field=field)


def _coerce_enum_text(value: object, *, field: str) -> str:
    if isinstance(value, Enum):
        value = value.value
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string or enum")
    return _require_text(value, field=field)


def _require_path(value: object, *, field: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be pathlib.Path")
    if "\x00" in str(value):
        raise ValueError(f"{field} must not contain NUL")
    return value


def _require_optional_path(value: object, *, field: str) -> Path | None:
    if value is None:
        return None
    return _require_path(value, field=field)


def _require_bool(value: object, *, field: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field} must be bool")
    return value


def _require_bounded_positive_int(
    value: object,
    *,
    field: str,
    maximum: int,
) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be int")
    if value <= 0 or value > maximum:
        raise ValueError(f"{field} must be between 1 and {maximum}")
    return value


def _require_bounded_nonnegative_int(
    value: object,
    *,
    field: str,
    maximum: int,
) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be int")
    if value < 0 or value > maximum:
        raise ValueError(f"{field} must be between 0 and {maximum}")
    return value


def _require_choice(
    value: object,
    *,
    field: str,
    allowed: set[str],
) -> str:
    text = _coerce_enum_text(value, field=field).lower()
    if text not in allowed:
        expected = ", ".join(sorted(allowed))
        raise ValueError(f"{field} must be one of: {expected}")
    return text


def _require_text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty without outer whitespace")
    if "\x00" in value or "\r" in value or "\n" in value:
        raise ValueError(f"{field} must be one line without NUL")
    if len(value) > _MAX_TEXT_LENGTH:
        raise ValueError(f"{field} exceeds {_MAX_TEXT_LENGTH} characters")
    return value


__all__ = (
    "LanguageCommandServices",
    "LanguageProbeApplication",
    "LanguageProbeCommandRequest",
    "LanguageProbeCommandResult",
    "LanguageProbeIssue",
    "LanguageProbeOutcome",
    "LanguageProbeResultLike",
    "SelectedPathKind",
    "execute_language_probe_command",
    "language_probe_request_from_cli_request",
    "language_probe_request_from_namespace",
    "run_language_probe",
)
