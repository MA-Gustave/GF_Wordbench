"""CLI adapter for the canonical GF Wordbench validation command."""

from __future__ import annotations

from argparse import Namespace
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Final, Protocol, TypeAlias, runtime_checkable

from gf_wordbench.kernel.events import EventSink, LifecycleEvent
from gf_wordbench.kernel.ids import ScenarioId, validate_scenario_id
from gf_wordbench.kernel.statuses import ValidationMode
from gf_wordbench.runs.models.results import RunResult

CancellationCheck: TypeAlias = Callable[[], None]
LifecycleSink: TypeAlias = EventSink[LifecycleEvent]

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


class CliAuditCommandError(ValueError):
    """Surface-level invocation error for the validation command."""


@dataclass(frozen=True, slots=True)
class ValidateCommandRequest:
    """Normalized CLI input for one shared validation use case."""

    mode: ValidationMode
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
    compatibility_warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.mode, ValidationMode):
            raise TypeError("mode must be ValidationMode")

        for name in (
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

        warnings = _text_tuple(
            self.compatibility_warnings,
            field_name="compatibility_warnings",
        )
        object.__setattr__(self, "compatibility_warnings", warnings)
        _validate_mode_options(self)

    @classmethod
    def from_namespace(cls, namespace: Namespace | Mapping[str, object]) -> ValidateCommandRequest:
        """Build a normalized request from parsed CLI values."""

        values = _namespace_values(namespace)
        warnings: list[str] = []

        mode = normalize_validation_mode(values.get("mode", ValidationMode.CHECKPOINT))
        raw_mode = values.get("mode")
        if isinstance(raw_mode, str) and raw_mode in {"file", "all"}:
            warnings.append(
                f"legacy mode {raw_mode!r} was normalized to {mode.value!r}"
            )

        target = _coalesce_alias(
            values,
            canonical="target",
            aliases=("target_file",),
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

        legacy_timeout = _optional_int_value(values.get("timeout_sec"), "timeout_sec")
        if legacy_timeout is not None:
            warnings.append(
                "legacy --timeout-sec supplied operation-specific timeout fallbacks"
            )

        compile_timeout = _timeout_value(
            values,
            ("compile_timeout_seconds", "compile_timeout"),
            fallback=legacy_timeout,
        )
        scenario_timeout = _timeout_value(
            values,
            ("scenario_timeout_seconds", "scenario_timeout"),
            fallback=legacy_timeout,
        )
        pgf_timeout = _timeout_value(
            values,
            ("pgf_timeout_seconds", "pgf_timeout"),
            fallback=legacy_timeout,
        )

        compare_previous = _comparison_setting(values)

        return cls(
            mode=mode,
            target=_optional_path(target, field_name="target"),
            checkpoint=_optional_text(values.get("checkpoint"), field_name="checkpoint"),
            scenarios=_scenario_values(values),
            strict=_bool_value(values.get("strict", False), "strict"),
            no_version_probe=no_version_probe,
            no_compile=_bool_value(values.get("no_compile", False), "no_compile"),
            compile_timeout_seconds=compile_timeout,
            scenario_timeout_seconds=scenario_timeout,
            pgf_timeout_seconds=pgf_timeout,
            max_files=_int_value(values.get("max_files", 0), "max_files"),
            cpu_stats=cpu_stats,
            keep_ok_details=_bool_value(
                values.get("keep_ok_details", False),
                "keep_ok_details",
            ),
            compare_previous=compare_previous,
            baseline=_optional_path(values.get("baseline"), field_name="baseline"),
            quiet=_bool_value(values.get("quiet", False), "quiet"),
            verbose=_bool_value(values.get("verbose", False), "verbose"),
            project_root=_optional_path(
                values.get("project_root"),
                field_name="project_root",
            ),
            gf_executable=_optional_path(
                _first_present(values, "gf_executable", "gf_exe"),
                field_name="gf_executable",
            ),
            rgl_root=_optional_path(values.get("rgl_root"), field_name="rgl_root"),
            output_root=_optional_path(
                _first_present(values, "output_root", "out_root"),
                field_name="output_root",
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
    """Callable application boundary for functional composition and tests."""

    run_validation: Callable[..., RunResult]

    def __post_init__(self) -> None:
        if not callable(self.run_validation):
            raise TypeError("run_validation must be callable")


AuditApplicationLike: TypeAlias = AuditApplication | AuditCommandServices


def execute_validate_command(
    request: ValidateCommandRequest | Namespace | Mapping[str, object],
    application: AuditApplicationLike,
    *,
    cancellation_check: CancellationCheck | None = None,
    event_sink: LifecycleSink | None = None,
) -> RunResult:
    """Validate CLI input and delegate execution to the shared application layer."""

    normalized = (
        request
        if isinstance(request, ValidateCommandRequest)
        else ValidateCommandRequest.from_namespace(request)
    )

    if cancellation_check is not None and not callable(cancellation_check):
        raise TypeError("cancellation_check must be callable or None")
    if event_sink is not None and not callable(event_sink):
        raise TypeError("event_sink must be callable or None")

    runner = getattr(application, "run_validation", None)
    if not callable(runner):
        raise TypeError("application must expose callable run_validation")

    result = runner(
        normalized,
        cancellation_check=cancellation_check,
        event_sink=event_sink,
    )
    if not isinstance(result, RunResult):
        raise TypeError("run_validation must return RunResult")
    result.validate()
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
    request: ValidateCommandRequest | Namespace | Mapping[str, object],
) -> ValidateCommandRequest:
    """Return a normalized request after all CLI-owned validation succeeds."""

    if isinstance(request, ValidateCommandRequest):
        return request
    return ValidateCommandRequest.from_namespace(request)


def _validate_mode_options(request: ValidateCommandRequest) -> None:
    if request.quiet and request.verbose:
        raise CliAuditCommandError("--quiet and --verbose cannot be used together")

    if request.baseline is not None and request.compare_previous is False:
        raise CliAuditCommandError(
            "--baseline cannot be combined with --no-compare-previous"
        )

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
        if request.max_files != 0:
            raise CliAuditCommandError("--max-files is invalid in checkpoint mode")
        return

    if request.checkpoint is not None:
        raise CliAuditCommandError(
            "--checkpoint is valid only in checkpoint mode"
        )

    if mode is ValidationMode.RELEASE:
        if request.no_compile:
            raise CliAuditCommandError("release mode rejects --no-compile")
        if request.max_files != 0:
            raise CliAuditCommandError("release mode rejects --max-files")


def _namespace_values(
    namespace: Namespace | Mapping[str, object],
) -> Mapping[str, object]:
    if isinstance(namespace, Namespace):
        return MappingProxyType(dict(vars(namespace)))
    if isinstance(namespace, Mapping):
        normalized: dict[str, object] = {}
        for key, value in namespace.items():
            if not isinstance(key, str):
                raise TypeError("namespace keys must be strings")
            normalized[key] = value
        return MappingProxyType(normalized)
    raise TypeError("request must be ValidateCommandRequest, Namespace, or mapping")


def _comparison_setting(values: Mapping[str, object]) -> bool | None:
    positive = values.get("compare_previous")
    negative = values.get("no_compare_previous")

    positive_value = None if positive is None else _bool_value(
        positive,
        "compare_previous",
    )
    negative_value = None if negative is None else _bool_value(
        negative,
        "no_compare_previous",
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
    raw = _first_present(values, "scenarios", "scenario")
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
            raise CliAuditCommandError(
                f"scenario selection exceeds {_MAX_SCENARIOS} IDs"
            )
        scenario_id = validate_scenario_id(value)
        if scenario_id in seen:
            raise CliAuditCommandError(
                f"duplicate scenario ID {scenario_id!r}"
            )
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
        (alias, values.get(alias))
        for alias in aliases
        if values.get(alias) is not None
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
    warnings.append(
        f"legacy --{alias.replace('_', '-')} was normalized to "
        f"--{canonical.replace('_', '-')}"
    )
    return value


def _coalesce_bool_alias(
    values: Mapping[str, object],
    *,
    canonical: str,
    aliases: Sequence[str],
    warnings: list[str],
) -> bool:
    canonical_value = _bool_value(values.get(canonical, False), canonical)
    active_aliases = [
        alias
        for alias in aliases
        if _bool_value(values.get(alias, False), alias)
    ]
    if canonical_value and active_aliases:
        raise CliAuditCommandError(
            f"--{canonical.replace('_', '-')} cannot be combined with its legacy alias"
        )
    if len(active_aliases) > 1:
        raise CliAuditCommandError("multiple legacy aliases supplied for one option")
    if active_aliases:
        alias = active_aliases[0]
        warnings.append(
            f"legacy --{alias.replace('_', '-')} was normalized to "
            f"--{canonical.replace('_', '-')}"
        )
        return True
    return canonical_value


def _first_present(values: Mapping[str, object], *keys: str) -> object | None:
    for key in keys:
        if key in values and values[key] is not None:
            return values[key]
    return None


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
            raise CliAuditCommandError(
                f"{field_name} must contain non-empty strings without NUL"
            )
        if text not in seen:
            result.append(text)
            seen.add(text)
    return tuple(result)


__all__ = (
    "AuditApplication",
    "AuditApplicationLike",
    "AuditCommandServices",
    "CliAuditCommandError",
    "ValidateCommandRequest",
    "execute_validate_command",
    "normalize_validation_mode",
    "validate_command_request",
)
