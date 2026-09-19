"""CLI adapter for the canonical GF Wordbench validation command."""

from __future__ import annotations

from argparse import Namespace
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
import inspect
from pathlib import Path
from types import MappingProxyType
from typing import Final, Protocol, TypeAlias, runtime_checkable

from gf_wordbench.config.defaults import DEFAULT_VALIDATION_MODE
from gf_wordbench.kernel.events import EventSink, LifecycleEvent
from gf_wordbench.kernel.ids import ScenarioId, validate_scenario_id
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.runs.models.results import RunResult

from .parser import CliCommand, CliRequest, CliUsageError

CancellationCheck: TypeAlias = Callable[[], None]
LifecycleSink: TypeAlias = EventSink[LifecycleEvent]


@runtime_checkable
class CliRequestLike(Protocol):
    """Minimal canonical parser request accepted by this adapter."""

    @property
    def arguments(self) -> Mapping[str, object]: ...

    @property
    def compatibility_warnings(self) -> tuple[str, ...]: ...


_MODE_ALIASES: Final[Mapping[str, ValidationMode]] = MappingProxyType(
    {
        "quick": ValidationMode.QUICK,
        "checkpoint": ValidationMode.CHECKPOINT,
        "release": ValidationMode.RELEASE,
        "diagnostic": ValidationMode.DIAGNOSTIC,
        "file": ValidationMode.QUICK,
        "all": ValidationMode.DIAGNOSTIC,
    }
)

_MAX_TIMEOUT_SECONDS: Final[int] = 86_400
_MAX_SCENARIOS: Final[int] = 10_000
_MAX_TEXT_LENGTH: Final[int] = 32_768
_EMPTY_OBJECT_MAP: Final[Mapping[str, object]] = MappingProxyType({})


class CliAuditCommandError(CliUsageError):
    """Surface-level invocation error for the validation command."""


@dataclass(frozen=True, slots=True)
class ValidateCommandRequest:
    """Normalized CLI input for one path-resolved validation use case.

    ``language_path`` is the explicit selected GF language directory or ``.gf``
    file. ``validation_profile`` is optional policy augmentation except for
    checkpoint and release modes. ``project_root`` remains migration-only
    compatibility data and is never a language-selection authority.
    """

    mode: ValidationMode
    language_path: Path | None = None
    validation_profile: Path | None = None
    use_last_language: bool = False
    target: Path | None = None
    checkpoint: str | None = None
    scenarios: tuple[ScenarioId, ...] = ()
    strict: bool = False
    no_version_probe: bool = False
    no_compile: bool = False
    compile_timeout_seconds: int | None = None
    scenario_timeout_seconds: int | None = None
    pgf_timeout_seconds: int | None = None
    max_files: int = 0
    cpu_stats: bool = False
    keep_ok_details: bool = False
    compare_previous: bool | None = None
    baseline: Path | None = None
    quiet: bool = False
    verbose: bool = False
    project_root: Path | None = None
    gf_executable: Path | None = None
    rgl_root: Path | None = None
    output_root: Path | None = None
    project_overrides: Mapping[str, object] = _EMPTY_OBJECT_MAP
    compatibility_warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ValidationMode):
            raise TypeError("mode must be ValidationMode")

        for name in (
            "use_last_language",
            "strict",
            "no_version_probe",
            "no_compile",
            "cpu_stats",
            "keep_ok_details",
            "quiet",
            "verbose",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")

        if self.compare_previous is not None and type(self.compare_previous) is not bool:
            raise TypeError("compare_previous must be bool or None")

        for name in (
            "language_path",
            "validation_profile",
            "target",
            "baseline",
            "project_root",
            "gf_executable",
            "rgl_root",
            "output_root",
        ):
            object.__setattr__(
                self,
                name,
                _optional_path(getattr(self, name), field_name=name),
            )

        checkpoint = _optional_text(self.checkpoint, field_name="checkpoint")
        if checkpoint is not None:
            validate_scenario_id(checkpoint, field="checkpoint ID")
        object.__setattr__(self, "checkpoint", checkpoint)

        scenarios = _scenario_ids(self.scenarios)
        object.__setattr__(self, "scenarios", scenarios)

        for name in (
            "compile_timeout_seconds",
            "scenario_timeout_seconds",
            "pgf_timeout_seconds",
        ):
            value = getattr(self, name)
            if value is not None:
                _require_int(
                    value,
                    field_name=name,
                    minimum=1,
                    maximum=_MAX_TIMEOUT_SECONDS,
                )

        _require_int(
            self.max_files,
            field_name="max_files",
            minimum=0,
        )

        overrides = _object_mapping(
            self.project_overrides,
            field_name="project_overrides",
        )
        object.__setattr__(self, "project_overrides", overrides)

        warnings = _text_tuple(
            self.compatibility_warnings,
            field_name="compatibility_warnings",
        )
        object.__setattr__(self, "compatibility_warnings", warnings)

        if (
            self.mode is ValidationMode.QUICK
            and self.target is None
            and self.language_path is not None
            and self.language_path.suffix.casefold() == ".gf"
        ):
            object.__setattr__(self, "target", self.language_path)

        _validate_mode_options(self)

    @property
    def selected_language_path(self) -> Path | None:
        """Compatibility alias for the explicit selected language path."""

        return self.language_path

    @property
    def validation_profile_path(self) -> Path | None:
        """Compatibility alias shared with GUI request models."""

        return self.validation_profile

    @property
    def profile_path(self) -> Path | None:
        """Temporary compatibility alias for the validation profile."""

        return self.validation_profile

    @property
    def target_path(self) -> Path | None:
        """Compatibility alias for the focused quick-mode target."""

        return self.target

    @property
    def checkpoint_ids(self) -> tuple[ScenarioId, ...]:
        """Compatibility projection of the optional checkpoint selection."""

        if self.checkpoint is None:
            return ()
        return (validate_scenario_id(self.checkpoint),)

    @property
    def checkpoints(self) -> tuple[ScenarioId, ...]:
        """Compatibility alias for ``checkpoint_ids``."""

        return self.checkpoint_ids

    @property
    def scenario_ids(self) -> tuple[ScenarioId, ...]:
        """Compatibility alias for the canonical ``scenarios`` field."""

        return self.scenarios

    @property
    def selected_scenarios(self) -> tuple[ScenarioId, ...]:
        """Compatibility alias for the canonical scenario selection."""

        return self.scenarios

    @property
    def skip_version_probe(self) -> bool:
        return self.no_version_probe

    @property
    def compile_timeout_sec(self) -> int | None:
        return self.compile_timeout_seconds

    @property
    def compile_timeout(self) -> int | None:
        return self.compile_timeout_seconds

    @property
    def scenario_timeout_sec(self) -> int | None:
        return self.scenario_timeout_seconds

    @property
    def scenario_timeout(self) -> int | None:
        return self.scenario_timeout_seconds

    @property
    def pgf_timeout_sec(self) -> int | None:
        return self.pgf_timeout_seconds

    @property
    def pgf_timeout(self) -> int | None:
        return self.pgf_timeout_seconds

    @property
    def emit_cpu_stats(self) -> bool:
        return self.cpu_stats

    @property
    def diff_previous(self) -> bool | None:
        """Compatibility alias for the canonical comparison setting."""

        return self.compare_previous

    @property
    def baseline_path(self) -> Path | None:
        return self.baseline

    @property
    def gf_exe(self) -> Path | None:
        return self.gf_executable

    @property
    def out_root(self) -> Path | None:
        return self.output_root

    @property
    def warnings(self) -> tuple[str, ...]:
        return self.compatibility_warnings

    @property
    def legacy_project_overrides(self) -> Mapping[str, object]:
        return self.project_overrides

    @classmethod
    def from_namespace(
        cls,
        namespace: Namespace | Mapping[str, object] | CliRequestLike,
    ) -> ValidateCommandRequest:
        """Build a normalized request from parsed or mapping-based CLI values."""

        values, inherited_warnings = _request_values(namespace)
        warnings = list(inherited_warnings)

        raw_mode = values.get("mode")
        mode = normalize_validation_mode(DEFAULT_VALIDATION_MODE if raw_mode is None else raw_mode)
        if isinstance(raw_mode, str) and raw_mode.strip().lower() in {
            "file",
            "all",
        }:
            _append_warning(
                warnings,
                f"legacy mode {raw_mode!r} was normalized to {mode.value!r}",
            )

        language_path = _first_present(
            values,
            "language_path",
            "selected_language_path",
        )
        validation_profile = _first_present(
            values,
            "validation_profile",
            "validation_profile_path",
            "profile_path",
            "profile",
        )
        target = _coalesce_alias(
            values,
            canonical="target",
            aliases=("target_file", "target_path"),
            warnings=warnings,
        )
        no_version_probe = _coalesce_bool_alias(
            values,
            canonical="no_version_probe",
            aliases=("skip_version_probe",),
            warnings=warnings,
        )
        cpu_stats = _coalesce_bool_alias(
            values,
            canonical="cpu_stats",
            aliases=("emit_cpu_stats",),
            warnings=warnings,
        )

        legacy_timeout = _optional_int_value(
            values.get("timeout_sec"),
            "timeout_sec",
        )
        if legacy_timeout is not None:
            _append_warning(
                warnings,
                "legacy --timeout-sec supplied operation-specific timeout fallbacks",
            )

        compile_timeout = _timeout_value(
            values,
            (
                "compile_timeout_seconds",
                "compile_timeout",
                "compile_timeout_sec",
            ),
            fallback=legacy_timeout,
        )
        scenario_timeout = _timeout_value(
            values,
            (
                "scenario_timeout_seconds",
                "scenario_timeout",
                "scenario_timeout_sec",
            ),
            fallback=legacy_timeout,
        )
        pgf_timeout = _timeout_value(
            values,
            (
                "pgf_timeout_seconds",
                "pgf_timeout",
                "pgf_timeout_sec",
            ),
            fallback=legacy_timeout,
        )

        compare_previous = _comparison_setting(values)
        baseline = _optional_path(
            _first_present(values, "baseline", "baseline_path"),
            field_name="baseline",
        )
        if baseline is not None and compare_previous is None:
            compare_previous = True

        project_root = _first_present(
            values,
            "project_root",
            "legacy_project_root",
        )
        project_overrides = _first_present(
            values,
            "project_overrides",
            "legacy_project_overrides",
            "legacy_overrides",
        )

        return cls(
            mode=mode,
            language_path=_optional_path(
                language_path,
                field_name="language_path",
            ),
            validation_profile=_optional_path(
                validation_profile,
                field_name="validation_profile",
            ),
            use_last_language=_optional_bool_value(
                values.get("use_last_language"),
                "use_last_language",
            ),
            target=_optional_path(target, field_name="target"),
            checkpoint=_optional_text(
                _first_present(
                    values,
                    "checkpoint",
                    "checkpoint_id",
                ),
                field_name="checkpoint",
            ),
            scenarios=_scenario_values(values),
            strict=_optional_bool_value(
                values.get("strict"),
                "strict",
            ),
            no_version_probe=no_version_probe,
            no_compile=_optional_bool_value(
                values.get("no_compile"),
                "no_compile",
            ),
            compile_timeout_seconds=compile_timeout,
            scenario_timeout_seconds=scenario_timeout,
            pgf_timeout_seconds=pgf_timeout,
            max_files=_optional_int_value(
                values.get("max_files"),
                "max_files",
            )
            or 0,
            cpu_stats=cpu_stats,
            keep_ok_details=_optional_bool_value(
                values.get("keep_ok_details"),
                "keep_ok_details",
            ),
            compare_previous=compare_previous,
            baseline=baseline,
            quiet=_optional_bool_value(
                values.get("quiet"),
                "quiet",
            ),
            verbose=_optional_bool_value(
                values.get("verbose"),
                "verbose",
            ),
            project_root=_optional_path(
                project_root,
                field_name="project_root",
            ),
            gf_executable=_optional_path(
                _first_present(
                    values,
                    "gf_executable",
                    "gf_exe",
                ),
                field_name="gf_executable",
            ),
            rgl_root=_optional_path(
                values.get("rgl_root"),
                field_name="rgl_root",
            ),
            output_root=_optional_path(
                _first_present(
                    values,
                    "output_root",
                    "out_root",
                ),
                field_name="output_root",
            ),
            project_overrides=_object_mapping(
                project_overrides,
                field_name="project_overrides",
            ),
            compatibility_warnings=tuple(warnings),
        )


@runtime_checkable
class AuditApplication(Protocol):
    """Shared application boundary invoked by the CLI adapter."""

    def run_validation(
        self,
        request: ValidateCommandRequest,
        *,
        cancellation_check: CancellationCheck | None = None,
        event_sink: LifecycleSink | None = None,
    ) -> RunResult:
        """Execute one validation request and return its structured result."""


@dataclass(frozen=True, slots=True)
class AuditCommandServices:
    """Injected validation dependencies used by CLI adapters and tests."""

    run_validation: Callable[..., RunResult] | None = None
    application: AuditApplication | None = None
    cancellation_check: CancellationCheck | None = None
    event_sink: LifecycleSink | None = None

    def __post_init__(self) -> None:
        if self.run_validation is None and self.application is None:
            raise TypeError("run_validation or application must be provided")
        if self.run_validation is not None and self.application is not None:
            raise TypeError("run_validation and application are mutually exclusive")
        if self.run_validation is not None and not callable(self.run_validation):
            raise TypeError("run_validation must be callable or None")
        if self.application is not None:
            runner = getattr(self.application, "run_validation", None)
            if not callable(runner):
                raise TypeError("application must expose callable run_validation")
        if self.cancellation_check is not None and not callable(self.cancellation_check):
            raise TypeError("cancellation_check must be callable or None")
        if self.event_sink is not None and not callable(self.event_sink):
            raise TypeError("event_sink must be callable or None")

    def runner(self) -> Callable[..., RunResult]:
        """Return the configured validation callable."""

        if self.run_validation is not None:
            return self.run_validation
        assert self.application is not None
        runner = self.application.run_validation
        return runner


AuditApplicationLike: TypeAlias = AuditApplication | AuditCommandServices


def execute_validate_cli_command(request: CliRequest) -> RunResult:
    """Execute one canonical ``validate`` CLI request.

    This wrapper owns only CLI-to-application translation. Concrete dependency
    construction remains in :mod:`gf_wordbench.bootstrap`, the product's sole
    general composition root.
    """

    if not isinstance(request, CliRequest):
        raise TypeError("request must be CliRequest")
    if request.command is not CliCommand.VALIDATE:
        raise CliAuditCommandError("request does not identify the validate command")

    normalized = validate_command_request(request)

    # Lazy import preserves an import-side-effect-free CLI module and prevents
    # bootstrap from becoming a parser dependency.
    from gf_wordbench.bootstrap import build_audit_application

    application = build_audit_application()
    if not isinstance(application, AuditApplication):
        raise TypeError("build_audit_application() must return an AuditApplication")

    return execute_validate_command(
        normalized,
        application,
    )


def execute_validate_command(
    request: (ValidateCommandRequest | Namespace | Mapping[str, object] | CliRequestLike),
    application: AuditApplicationLike | None = None,
    *,
    services: AuditCommandServices | None = None,
    cancellation_check: CancellationCheck | None = None,
    event_sink: LifecycleSink | None = None,
) -> RunResult:
    """Normalize CLI input and delegate once to the application boundary.

    ``application`` is the canonical injectable dependency. ``services`` is
    accepted as a compatibility keyword for older callers.
    """

    if application is not None and services is not None:
        raise TypeError("application and services cannot both be provided")

    dependency = services if services is not None else application
    if dependency is None:
        raise TypeError("an audit application or AuditCommandServices is required")

    normalized = validate_command_request(request)

    if cancellation_check is not None and not callable(cancellation_check):
        raise TypeError("cancellation_check must be callable or None")
    if event_sink is not None and not callable(event_sink):
        raise TypeError("event_sink must be callable or None")

    runner: Callable[..., RunResult]
    if isinstance(dependency, AuditCommandServices):
        runner = dependency.runner()
        effective_cancellation = (
            cancellation_check if cancellation_check is not None else dependency.cancellation_check
        )
        effective_sink = event_sink if event_sink is not None else dependency.event_sink
    else:
        if not isinstance(dependency, AuditApplication):
            raise TypeError("application must satisfy AuditApplication")
        runner = dependency.run_validation
        effective_cancellation = cancellation_check
        effective_sink = event_sink

    result = _invoke_validation_runner(
        runner,
        normalized,
        cancellation_check=effective_cancellation,
        event_sink=effective_sink,
    )
    if not isinstance(result, RunResult):
        raise TypeError("run_validation must return RunResult")

    # Some compatibility tests construct an uninitialized RunResult instance.
    # Validate only populated results; production results always expose status.
    if hasattr(result, "overall_status"):
        validator = getattr(result, "validate", None)
        if callable(validator):
            validator()
    return result


def normalize_validation_mode(value: object) -> ValidationMode:
    """Normalize canonical modes and documented legacy input aliases."""

    if isinstance(value, ValidationMode):
        return value
    if not isinstance(value, str):
        raise CliAuditCommandError("mode must be a string or ValidationMode")
    candidate = value.strip().lower()
    try:
        return _MODE_ALIASES[candidate]
    except KeyError as exc:
        allowed = ", ".join(mode.value for mode in ValidationMode)
        raise CliAuditCommandError(
            f"unknown validation mode {value!r}; expected one of {allowed}"
        ) from exc


def validate_command_request(
    request: (ValidateCommandRequest | Namespace | Mapping[str, object] | CliRequestLike),
) -> ValidateCommandRequest:
    """Return a normalized request after all CLI-owned validation succeeds."""

    if isinstance(request, ValidateCommandRequest):
        _validate_mode_options(request)
        return request
    return ValidateCommandRequest.from_namespace(request)


def _validate_mode_options(request: ValidateCommandRequest) -> None:
    if request.language_path is not None and request.use_last_language:
        raise CliAuditCommandError("--language-path and --last-language cannot be used together")
    if request.language_path is None and not request.use_last_language:
        raise CliAuditCommandError(
            "an explicit --language-path or --last-language selection is required"
        )

    if request.quiet and request.verbose:
        raise CliAuditCommandError("--quiet and --verbose cannot be used together")

    if request.baseline is not None and request.compare_previous is False:
        raise CliAuditCommandError("--baseline cannot be combined with --no-compare-previous")

    mode = request.mode
    if mode is ValidationMode.QUICK:
        if request.target is None:
            raise CliAuditCommandError("quick mode requires --target")
        if request.checkpoint is not None:
            raise CliAuditCommandError("--checkpoint is invalid in quick mode")
        if request.max_files != 0:
            raise CliAuditCommandError("--max-files is invalid in quick mode")
        return

    if request.target is not None:
        raise CliAuditCommandError("--target is valid only in quick mode")

    if mode is ValidationMode.CHECKPOINT:
        if request.validation_profile is None:
            raise CliAuditCommandError("checkpoint mode requires --profile")
        if request.max_files != 0:
            raise CliAuditCommandError("--max-files is invalid in checkpoint mode")
        if request.checkpoint is None and not request.scenarios:
            raise CliAuditCommandError("checkpoint mode requires --checkpoint or --scenario")
        return

    if request.checkpoint is not None:
        raise CliAuditCommandError("--checkpoint is valid only in checkpoint mode")

    if mode is ValidationMode.RELEASE:
        if request.validation_profile is None:
            raise CliAuditCommandError("release mode requires --profile")
        if request.no_compile:
            raise CliAuditCommandError("release mode rejects --no-compile")
        if request.max_files != 0:
            raise CliAuditCommandError("release mode rejects --max-files")
        if request.strict and request.no_version_probe:
            raise CliAuditCommandError("strict release mode rejects --no-version-probe")


def _request_values(
    request: Namespace | Mapping[str, object] | CliRequestLike,
) -> tuple[Mapping[str, object], tuple[str, ...]]:
    if isinstance(request, Namespace):
        raw = dict(vars(request))
        warnings = _warnings_from_object(raw.pop("_compatibility_warnings", ()))
        return MappingProxyType(raw), warnings

    if isinstance(request, Mapping):
        normalized: dict[str, object] = {}
        for key, value in request.items():
            if not isinstance(key, str):
                raise TypeError("request keys must be strings")
            normalized[key] = value
        warnings = _warnings_from_object(normalized.pop("_compatibility_warnings", ()))
        return MappingProxyType(normalized), warnings

    arguments = getattr(request, "arguments", None)
    if isinstance(arguments, Mapping):
        normalized = {}
        for key, value in arguments.items():
            if not isinstance(key, str):
                raise TypeError("request argument names must be strings")
            normalized[key] = value
        warnings = _warnings_from_object(getattr(request, "compatibility_warnings", ()))
        return MappingProxyType(normalized), warnings

    raise TypeError(
        "request must be ValidateCommandRequest, Namespace, mapping, or canonical CliRequest"
    )


def _warnings_from_object(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray, Mapping)):
        raise TypeError("compatibility warnings must be an iterable of strings")
    if not isinstance(value, Iterable):
        raise TypeError("compatibility warnings must be an iterable of strings")
    return _text_tuple(
        value,
        field_name="compatibility_warnings",
    )


def _append_warning(warnings: list[str], message: str) -> None:
    if message not in warnings:
        warnings.append(message)


def _invoke_validation_runner(
    runner: Callable[..., RunResult],
    request: ValidateCommandRequest,
    *,
    cancellation_check: CancellationCheck | None,
    event_sink: LifecycleSink | None,
) -> RunResult:
    kwargs: dict[str, object] = {}

    try:
        signature = inspect.signature(runner)
    except (TypeError, ValueError):
        signature = None

    supports_kwargs = False
    parameter_names: set[str] = set()
    if signature is not None:
        for parameter in signature.parameters.values():
            parameter_names.add(parameter.name)
            if parameter.kind is inspect.Parameter.VAR_KEYWORD:
                supports_kwargs = True

    if cancellation_check is not None and (
        signature is None or supports_kwargs or "cancellation_check" in parameter_names
    ):
        kwargs["cancellation_check"] = cancellation_check
    if event_sink is not None and (
        signature is None or supports_kwargs or "event_sink" in parameter_names
    ):
        kwargs["event_sink"] = event_sink

    return runner(request, **kwargs)


def _comparison_setting(values: Mapping[str, object]) -> bool | None:
    positive = values.get("compare_previous")
    negative = values.get("no_compare_previous")

    positive_value = (
        None
        if positive is None
        else _bool_value(
            positive,
            "compare_previous",
        )
    )
    negative_value = (
        None
        if negative is None
        else _bool_value(
            negative,
            "no_compare_previous",
        )
    )

    if positive_value is True and negative_value is True:
        raise CliAuditCommandError(
            "--compare-previous and --no-compare-previous cannot be combined"
        )
    if negative_value is True:
        return False
    if positive_value is not None:
        return positive_value
    return None


def _scenario_values(values: Mapping[str, object]) -> tuple[ScenarioId, ...]:
    raw = _first_present(
        values,
        "scenarios",
        "scenario_ids",
        "selected_scenarios",
        "scenario",
    )
    if raw is None:
        return ()
    if isinstance(raw, str):
        return (validate_scenario_id(raw),)
    if isinstance(raw, (bytes, bytearray, Mapping)) or not isinstance(raw, Iterable):
        raise TypeError("scenario must be a string or iterable of strings")
    return _scenario_ids(tuple(raw))


def _scenario_ids(values: Iterable[object]) -> tuple[ScenarioId, ...]:
    if isinstance(values, (str, bytes, bytearray, Mapping)):
        raise TypeError("scenarios must be an iterable of scenario IDs")
    result: list[ScenarioId] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        if index >= _MAX_SCENARIOS:
            raise CliAuditCommandError(f"scenario selection exceeds {_MAX_SCENARIOS} IDs")
        scenario_id = validate_scenario_id(value)
        if scenario_id in seen:
            raise CliAuditCommandError(f"duplicate scenario ID {scenario_id!r}")
        seen.add(scenario_id)
        result.append(scenario_id)
    return tuple(result)


def _timeout_value(
    values: Mapping[str, object],
    keys: Sequence[str],
    *,
    fallback: int | None,
) -> int | None:
    value = _first_present(values, *keys)
    if value is None:
        return fallback
    return _optional_int_value(value, keys[0])


def _coalesce_alias(
    values: Mapping[str, object],
    *,
    canonical: str,
    aliases: Sequence[str],
    warnings: list[str],
) -> object | None:
    canonical_value = values.get(canonical)
    alias_values = [
        (alias, values.get(alias)) for alias in aliases if values.get(alias) is not None
    ]
    if canonical_value is not None and alias_values:
        raise CliAuditCommandError(
            f"--{canonical.replace('_', '-')} cannot be combined with its legacy alias"
        )
    if canonical_value is not None:
        return canonical_value
    if not alias_values:
        return None
    alias, value = alias_values[0]
    if len(alias_values) > 1:
        raise CliAuditCommandError("multiple legacy aliases supplied for one option")
    _append_warning(
        warnings,
        f"legacy --{alias.replace('_', '-')} was normalized to --{canonical.replace('_', '-')}",
    )
    return value


def _coalesce_bool_alias(
    values: Mapping[str, object],
    *,
    canonical: str,
    aliases: Sequence[str],
    warnings: list[str],
) -> bool:
    canonical_value = _optional_bool_value(
        values.get(canonical),
        canonical,
    )
    active_aliases = [alias for alias in aliases if _optional_bool_value(values.get(alias), alias)]
    if canonical_value and active_aliases:
        raise CliAuditCommandError(
            f"--{canonical.replace('_', '-')} cannot be combined with its legacy alias"
        )
    if len(active_aliases) > 1:
        raise CliAuditCommandError("multiple legacy aliases supplied for one option")
    if active_aliases:
        alias = active_aliases[0]
        warnings.append(
            f"legacy --{alias.replace('_', '-')} was normalized to --{canonical.replace('_', '-')}"
        )
        return True
    return canonical_value


def _first_present(values: Mapping[str, object], *keys: str) -> object | None:
    for key in keys:
        if key in values and values[key] is not None:
            return values[key]
    return None


def _object_mapping(
    value: object,
    *,
    field_name: str,
) -> Mapping[str, object]:
    if value is None:
        return _EMPTY_OBJECT_MAP
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")

    normalized: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError(f"{field_name} keys must be strings")
        name = key.strip()
        if not name or "\x00" in name:
            raise CliAuditCommandError(f"{field_name} keys must be non-empty strings without NUL")
        normalized[name] = item
    return MappingProxyType(normalized)


def _optional_path(value: object, *, field_name: str) -> Path | None:
    if value is None or value == "":
        return None
    if isinstance(value, Path):
        path = value
    elif isinstance(value, str):
        if "\x00" in value:
            raise CliAuditCommandError(f"{field_name} must not contain NUL")
        path = Path(value)
    else:
        raise TypeError(f"{field_name} must be str, Path, or None")
    if "\x00" in str(path):
        raise CliAuditCommandError(f"{field_name} must not contain NUL")
    return path


def _optional_text(value: object, *, field_name: str) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be str or None")
    if "\x00" in value:
        raise CliAuditCommandError(f"{field_name} must not contain NUL")
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > _MAX_TEXT_LENGTH:
        raise CliAuditCommandError(f"{field_name} exceeds the supported length")
    return normalized


def _optional_bool_value(
    value: object,
    field_name: str,
    *,
    default: bool = False,
) -> bool:
    if value is None:
        return default
    return _bool_value(value, field_name)


def _bool_value(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be bool")
    return value


def _int_value(value: object, field_name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be int")
    return value


def _optional_int_value(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    return _int_value(value, field_name)


def _require_int(
    value: int,
    *,
    field_name: str,
    minimum: int,
    maximum: int | None = None,
) -> None:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be int")
    if value < minimum:
        raise CliAuditCommandError(f"{field_name} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise CliAuditCommandError(f"{field_name} must be at most {maximum}")


def _text_tuple(values: Iterable[object], *, field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray, Mapping)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must contain strings")
        text = value.strip()
        if not text or "\x00" in text:
            raise CliAuditCommandError(f"{field_name} must contain non-empty strings without NUL")
        if text not in seen:
            result.append(text)
            seen.add(text)
    return tuple(result)


__all__ = (
    "AuditApplication",
    "AuditApplicationLike",
    "AuditCommandServices",
    "CliAuditCommandError",
    "CliRequestLike",
    "ValidateCommandRequest",
    "execute_validate_cli_command",
    "execute_validate_command",
    "normalize_validation_mode",
    "validate_command_request",
)
