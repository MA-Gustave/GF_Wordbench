"""Compilation orchestration service for GF Wordbench."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, Protocol, runtime_checkable

from gf_wordbench.infrastructure.process import (
    CancellationToken,
    ProcessResult,
)
from gf_wordbench.kernel.errors import (
    CancellationRequested,
    GFWordbenchError,
)
from gf_wordbench.kernel.statuses import (
    ErrorKind,
    ValidationStatus,
)

from .models import (
    CompilePlan,
    CompileRequest,
    CompileSummary,
    CompileTarget,
)

__all__ = (
    "CompilationExecutor",
    "CompilationObserver",
    "CompilationPreflight",
    "CompilationPreflightValidator",
    "CompilationRequestBuilder",
    "CompilationService",
    "CompilationSummaryFactory",
)

_COMPILE_TARGET_KINDS: Final[frozenset[str]] = frozenset(
    {"source", "checkpoint", "entrypoint", "pgf"}
)
_FAIL_FAST_STATUSES: Final[frozenset[ValidationStatus]] = frozenset(
    {ValidationStatus.FAIL, ValidationStatus.ERROR}
)
_MAX_PREFLIGHT_WARNINGS: Final[int] = 128
_MAX_TEXT_LENGTH: Final[int] = 4096


@dataclass(frozen=True, slots=True)
class CompilationPreflight:
    succeeded: bool
    error_kind: ErrorKind = ErrorKind.OK
    message: str = ""
    detail: str = ""
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.succeeded, bool):
            raise TypeError("succeeded must be a boolean")
        if not isinstance(self.error_kind, ErrorKind):
            raise TypeError("error_kind must be an ErrorKind")

        message = _bounded_text(
            self.message,
            field="message",
            allow_empty=True,
        )
        detail = _bounded_text(
            self.detail,
            field="detail",
            allow_empty=True,
        )
        warnings = _validate_warnings(self.warnings)

        if self.succeeded:
            if self.error_kind is not ErrorKind.OK:
                raise ValueError("successful preflight must use ErrorKind.OK")
            if message:
                raise ValueError("successful preflight must not contain an error message")
        else:
            if self.error_kind is ErrorKind.OK:
                raise ValueError("failed preflight must not use ErrorKind.OK")
            if not message:
                raise ValueError("failed preflight requires a message")

        object.__setattr__(self, "message", message)
        object.__setattr__(self, "detail", detail)
        object.__setattr__(self, "warnings", warnings)

    @classmethod
    def ok(
        cls,
        *,
        warnings: tuple[str, ...] = (),
    ) -> CompilationPreflight:
        return cls(
            succeeded=True,
            warnings=warnings,
        )

    @classmethod
    def failed(
        cls,
        *,
        error_kind: ErrorKind,
        message: str,
        detail: str = "",
        warnings: tuple[str, ...] = (),
    ) -> CompilationPreflight:
        return cls(
            succeeded=False,
            error_kind=error_kind,
            message=message,
            detail=detail,
            warnings=warnings,
        )


@runtime_checkable
class CompilationPreflightValidator(Protocol):
    def validate(
        self,
        plan: CompilePlan,
    ) -> CompilationPreflight: ...


@runtime_checkable
class CompilationRequestBuilder(Protocol):
    def build(
        self,
        target: CompileTarget,
        *,
        clean_build: bool,
    ) -> CompileRequest: ...


@runtime_checkable
class CompilationExecutor(Protocol):
    def execute(
        self,
        request: CompileRequest,
        *,
        cancellation_token: CancellationToken | None = None,
    ) -> ProcessResult: ...


@runtime_checkable
class CompilationSummaryFactory(Protocol):
    def from_process(
        self,
        target: CompileTarget,
        request: CompileRequest,
        process_result: ProcessResult,
    ) -> CompileSummary: ...

    def from_exception(
        self,
        target: CompileTarget,
        error: Exception,
        *,
        request: CompileRequest | None,
    ) -> CompileSummary: ...

    def preflight_error(
        self,
        target: CompileTarget,
        *,
        error_kind: ErrorKind,
        message: str,
        detail: str,
    ) -> CompileSummary: ...

    def skipped(
        self,
        target: CompileTarget,
        *,
        reason: str,
    ) -> CompileSummary: ...


@runtime_checkable
class CompilationObserver(Protocol):
    def plan_started(
        self,
        plan: CompilePlan,
    ) -> None: ...

    def preflight_completed(
        self,
        plan: CompilePlan,
        result: CompilationPreflight,
    ) -> None: ...

    def target_started(
        self,
        target: CompileTarget,
        index: int,
        total: int,
    ) -> None: ...

    def target_completed(
        self,
        target: CompileTarget,
        summary: CompileSummary,
        index: int,
        total: int,
    ) -> None: ...

    def plan_completed(
        self,
        plan: CompilePlan,
        summaries: tuple[CompileSummary, ...],
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class CompilationService:
    preflight_validator: CompilationPreflightValidator
    request_builder: CompilationRequestBuilder
    executor: CompilationExecutor
    summary_factory: CompilationSummaryFactory
    observer: CompilationObserver | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.preflight_validator,
            CompilationPreflightValidator,
        ):
            raise TypeError("preflight_validator must satisfy CompilationPreflightValidator")
        if not isinstance(
            self.request_builder,
            CompilationRequestBuilder,
        ):
            raise TypeError("request_builder must satisfy CompilationRequestBuilder")
        if not isinstance(
            self.executor,
            CompilationExecutor,
        ):
            raise TypeError("executor must satisfy CompilationExecutor")
        if not isinstance(
            self.summary_factory,
            CompilationSummaryFactory,
        ):
            raise TypeError("summary_factory must satisfy CompilationSummaryFactory")

    def validate_plan(
        self,
        plan: CompilePlan,
    ) -> CompilationPreflight:
        _validate_plan(plan)
        result = self.preflight_validator.validate(plan)
        if not isinstance(result, CompilationPreflight):
            raise TypeError("preflight validator must return CompilationPreflight")
        _notify(
            self.observer,
            "preflight_completed",
            plan,
            result,
        )
        return result

    def execute_plan(
        self,
        plan: CompilePlan,
        *,
        no_compile: bool = False,
        cancellation_token: CancellationToken | None = None,
    ) -> tuple[CompileSummary, ...]:
        _validate_plan(plan)
        if not isinstance(no_compile, bool):
            raise TypeError("no_compile must be a boolean")
        _validate_cancellation_token(cancellation_token)

        _notify(
            self.observer,
            "plan_started",
            plan,
        )

        preflight = self.validate_plan(plan)
        if not preflight.succeeded:
            preflight_summaries = tuple(
                self._preflight_error_summary(
                    target,
                    preflight,
                )
                for target in plan.targets
            )
            self._complete_plan(plan, preflight_summaries)
            return preflight_summaries

        if no_compile:
            skipped_summaries = tuple(
                self._skipped_summary(
                    target,
                    reason="no_compile",
                )
                for target in plan.targets
            )
            self._complete_plan(plan, skipped_summaries)
            return skipped_summaries

        summaries: list[CompileSummary] = []
        total = len(plan.targets)
        stop_reason: str | None = None

        for index, target in enumerate(plan.targets):
            position = index + 1

            if stop_reason is not None:
                summary = self._skipped_summary(
                    target,
                    reason=stop_reason,
                )
                summaries.append(summary)
                _notify(
                    self.observer,
                    "target_completed",
                    target,
                    summary,
                    position,
                    total,
                )
                continue

            if _is_cancelled(cancellation_token):
                stop_reason = "cancelled"
                summary = self._skipped_summary(
                    target,
                    reason=stop_reason,
                )
                summaries.append(summary)
                _notify(
                    self.observer,
                    "target_completed",
                    target,
                    summary,
                    position,
                    total,
                )
                continue

            summary = self._execute_target(
                target,
                clean_build=plan.clean_build,
                cancellation_token=cancellation_token,
                index=position,
                total=total,
            )
            summaries.append(summary)

            if (
                plan.fail_fast
                and _target_is_required(target)
                and _summary_status(summary) in _FAIL_FAST_STATUSES
            ):
                stop_reason = "fail_fast"

        frozen = tuple(summaries)
        _validate_result_set(plan, frozen)
        self._complete_plan(plan, frozen)
        return frozen

    def compile_target(
        self,
        target: CompileTarget,
        *,
        clean_build: bool = True,
        cancellation_token: CancellationToken | None = None,
    ) -> CompileSummary:
        _validate_target(target)
        if not isinstance(clean_build, bool):
            raise TypeError("clean_build must be a boolean")
        _validate_cancellation_token(cancellation_token)

        if _is_cancelled(cancellation_token):
            return self._skipped_summary(
                target,
                reason="cancelled",
            )

        return self._execute_target(
            target,
            clean_build=clean_build,
            cancellation_token=cancellation_token,
            index=1,
            total=1,
        )

    def compile_source(
        self,
        target: CompileTarget,
        *,
        clean_build: bool = True,
        cancellation_token: CancellationToken | None = None,
    ) -> CompileSummary:
        _require_target_kind(target, "source")
        return self.compile_target(
            target,
            clean_build=clean_build,
            cancellation_token=cancellation_token,
        )

    def compile_checkpoint(
        self,
        target: CompileTarget,
        *,
        clean_build: bool = True,
        cancellation_token: CancellationToken | None = None,
    ) -> CompileSummary:
        _require_target_kind(target, "checkpoint")
        return self.compile_target(
            target,
            clean_build=clean_build,
            cancellation_token=cancellation_token,
        )

    def compile_entrypoint(
        self,
        target: CompileTarget,
        *,
        clean_build: bool = True,
        cancellation_token: CancellationToken | None = None,
    ) -> CompileSummary:
        _require_target_kind(target, "entrypoint")
        return self.compile_target(
            target,
            clean_build=clean_build,
            cancellation_token=cancellation_token,
        )

    def build_release_pgf(
        self,
        target: CompileTarget,
        *,
        clean_build: bool = True,
        cancellation_token: CancellationToken | None = None,
    ) -> CompileSummary:
        _require_target_kind(target, "pgf")
        return self.compile_target(
            target,
            clean_build=clean_build,
            cancellation_token=cancellation_token,
        )

    def _execute_target(
        self,
        target: CompileTarget,
        *,
        clean_build: bool,
        cancellation_token: CancellationToken | None,
        index: int,
        total: int,
    ) -> CompileSummary:
        _validate_target(target)
        _notify(
            self.observer,
            "target_started",
            target,
            index,
            total,
        )

        request: CompileRequest | None = None
        try:
            request = self.request_builder.build(
                target,
                clean_build=clean_build,
            )
            _validate_request_identity(
                target,
                request,
            )

            if _is_cancelled(cancellation_token):
                summary = self._skipped_summary(
                    target,
                    reason="cancelled",
                )
            else:
                process_result = self.executor.execute(
                    request,
                    cancellation_token=cancellation_token,
                )
                if not isinstance(
                    process_result,
                    ProcessResult,
                ):
                    raise TypeError("executor must return a ProcessResult")

                summary = self.summary_factory.from_process(
                    target,
                    request,
                    process_result,
                )
        except CancellationRequested:
            summary = self._skipped_summary(
                target,
                reason="cancelled",
            )
        except (GFWordbenchError, OSError, ValueError, TypeError) as exc:
            summary = self.summary_factory.from_exception(
                target,
                exc,
                request=request,
            )
        except Exception as exc:
            summary = self.summary_factory.from_exception(
                target,
                exc,
                request=request,
            )

        _validate_summary_identity(
            target,
            summary,
        )
        _notify(
            self.observer,
            "target_completed",
            target,
            summary,
            index,
            total,
        )
        return summary

    def _preflight_error_summary(
        self,
        target: CompileTarget,
        result: CompilationPreflight,
    ) -> CompileSummary:
        summary = self.summary_factory.preflight_error(
            target,
            error_kind=result.error_kind,
            message=result.message,
            detail=result.detail,
        )
        _validate_summary_identity(
            target,
            summary,
        )
        return summary

    def _skipped_summary(
        self,
        target: CompileTarget,
        *,
        reason: str,
    ) -> CompileSummary:
        normalized_reason = _bounded_text(
            reason,
            field="reason",
            allow_empty=False,
        )
        summary = self.summary_factory.skipped(
            target,
            reason=normalized_reason,
        )
        _validate_summary_identity(
            target,
            summary,
        )
        if _summary_status(summary) is not ValidationStatus.SKIPPED:
            raise ValueError("summary_factory.skipped must return ValidationStatus.SKIPPED")
        return summary

    def _complete_plan(
        self,
        plan: CompilePlan,
        summaries: tuple[CompileSummary, ...],
    ) -> None:
        _validate_result_set(plan, summaries)
        _notify(
            self.observer,
            "plan_completed",
            plan,
            summaries,
        )


def _validate_plan(
    plan: CompilePlan,
) -> None:
    if not isinstance(plan, CompilePlan):
        raise TypeError("plan must be a CompilePlan")
    if not isinstance(plan.targets, tuple):
        raise TypeError("plan.targets must be a tuple")
    if not isinstance(plan.clean_build, bool):
        raise TypeError("plan.clean_build must be a boolean")
    if not isinstance(plan.fail_fast, bool):
        raise TypeError("plan.fail_fast must be a boolean")
    if not isinstance(plan.gf_version_required, bool):
        raise TypeError("plan.gf_version_required must be a boolean")

    seen: set[str] = set()
    previous_order: int | None = None

    for target in plan.targets:
        _validate_target(target)
        target_id = _target_id(target)
        if target_id in seen:
            raise ValueError(f"duplicate compile target ID: {target_id}")
        seen.add(target_id)

        declared_order = _declared_order(target)
        if previous_order is not None and declared_order < previous_order:
            raise ValueError("compile targets must preserve deterministic declared order")
        previous_order = declared_order


def _validate_target(
    target: CompileTarget,
) -> None:
    if not isinstance(target, CompileTarget):
        raise TypeError("target must be a CompileTarget")

    _target_id(target)
    kind = _target_kind(target)
    if kind not in _COMPILE_TARGET_KINDS:
        raise ValueError(f"unsupported compile target kind: {kind}")
    _declared_order(target)
    _target_is_required(target)


def _validate_request_identity(
    target: CompileTarget,
    request: CompileRequest,
) -> None:
    if not isinstance(request, CompileRequest):
        raise TypeError("request_builder must return a CompileRequest")

    request_target = getattr(request, "target", None)
    if request_target is not None:
        if not isinstance(request_target, CompileTarget):
            raise TypeError("CompileRequest.target must be a CompileTarget")
        if _target_id(request_target) != _target_id(target):
            raise ValueError(
                "compile request target identity does not match the requested compile target"
            )

    request_target_id = getattr(
        request,
        "target_id",
        None,
    )
    if request_target_id is not None:
        if request_target_id != _target_id(target):
            raise ValueError(
                "compile request target_id does not match the requested compile target"
            )


def _validate_summary_identity(
    target: CompileTarget,
    summary: CompileSummary,
) -> None:
    if not isinstance(summary, CompileSummary):
        raise TypeError("summary factory must return a CompileSummary")

    summary_target_id = getattr(
        summary,
        "target_id",
        None,
    )
    if summary_target_id is not None:
        if summary_target_id != _target_id(target):
            raise ValueError("compile summary target_id does not match the compile target")

    _summary_status(summary)


def _validate_result_set(
    plan: CompilePlan,
    summaries: tuple[CompileSummary, ...],
) -> None:
    if not isinstance(summaries, tuple):
        raise TypeError("summaries must be a tuple")
    if len(summaries) != len(plan.targets):
        raise ValueError("compile result count must equal compile target count")

    for target, summary in zip(
        plan.targets,
        summaries,
        strict=True,
    ):
        _validate_summary_identity(
            target,
            summary,
        )


def _target_id(
    target: CompileTarget,
) -> str:
    value = getattr(target, "target_id", None)
    return _bounded_text(
        value,
        field="target.target_id",
        allow_empty=False,
    )


def _target_kind(
    target: CompileTarget,
) -> str:
    value: object = getattr(target, "kind", None)
    if isinstance(value, Enum):
        value = value.value
    return _bounded_text(
        value,
        field="target.kind",
        allow_empty=False,
    )


def _require_target_kind(
    target: CompileTarget,
    expected: str,
) -> None:
    _validate_target(target)
    actual = _target_kind(target)
    if actual != expected:
        raise ValueError(f"compile target kind must be {expected!r}, got {actual!r}")


def _declared_order(
    target: CompileTarget,
) -> int:
    value = getattr(target, "declared_order", None)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("target.declared_order must be an integer")
    if value < 0:
        raise ValueError("target.declared_order must be non-negative")
    return value


def _target_is_required(
    target: CompileTarget,
) -> bool:
    value = getattr(target, "required", None)
    if not isinstance(value, bool):
        raise TypeError("target.required must be a boolean")
    return value


def _summary_status(
    summary: CompileSummary,
) -> ValidationStatus:
    value = getattr(summary, "status", None)
    if isinstance(value, ValidationStatus):
        return value
    if not isinstance(value, str):
        raise ValueError("compile summary status must be a canonical ValidationStatus")
    try:
        return ValidationStatus(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("compile summary status must be a canonical ValidationStatus") from exc


def _validate_cancellation_token(
    token: CancellationToken | None,
) -> None:
    if token is None:
        return
    if not callable(getattr(token, "is_cancelled", None)):
        raise TypeError("cancellation_token must expose is_cancelled()")
    if not callable(getattr(token, "reason", None)):
        raise TypeError("cancellation_token must expose reason()")


def _is_cancelled(
    token: CancellationToken | None,
) -> bool:
    if token is None:
        return False
    value = token.is_cancelled()
    if not isinstance(value, bool):
        raise TypeError("CancellationToken.is_cancelled() must return bool")
    return value


def _validate_warnings(
    warnings: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(warnings, tuple):
        raise TypeError("warnings must be a tuple")
    if len(warnings) > _MAX_PREFLIGHT_WARNINGS:
        raise ValueError("warnings exceeds the bounded preflight limit")

    normalized: list[str] = []
    seen: set[str] = set()
    for index, warning in enumerate(warnings):
        value = _bounded_text(
            warning,
            field=f"warnings[{index}]",
            allow_empty=False,
        )
        if value in seen:
            raise ValueError("warnings must not contain duplicate values")
        seen.add(value)
        normalized.append(value)

    return tuple(normalized)


def _bounded_text(
    value: object,
    *,
    field: str,
    allow_empty: bool,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")

    normalized = value.strip()
    if not allow_empty and not normalized:
        raise ValueError(f"{field} must not be empty")
    if len(normalized) > _MAX_TEXT_LENGTH:
        raise ValueError(f"{field} must not exceed {_MAX_TEXT_LENGTH} characters")
    return normalized


def _notify(
    observer: CompilationObserver | None,
    method_name: str,
    *args: object,
) -> None:
    if observer is None:
        return
    method = getattr(observer, method_name, None)
    if not callable(method):
        raise TypeError(f"observer must expose {method_name}()")
    method(*args)
