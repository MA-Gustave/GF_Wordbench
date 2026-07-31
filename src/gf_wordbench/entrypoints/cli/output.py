"""Safe, deterministic console presentation for the GF Wordbench CLI."""

from __future__ import annotations

import re
import sys
import traceback
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import TYPE_CHECKING, Final, Protocol, TextIO, runtime_checkable

from gf_wordbench.version import __version__

if TYPE_CHECKING:
    from gf_wordbench.kernel.events import LifecycleEvent, ProgressEvent

_MAX_CONSOLE_LINE: Final[int] = 4_096
_MAX_CONSOLE_MESSAGE: Final[int] = 8_192
_MAX_TRACEBACK: Final[int] = 64_000
_MAX_RESULT_ITEMS: Final[int] = 100
_APPLICATION_NAME: Final[str] = "GF Wordbench"
_STATUS_ORDER: Final[tuple[str, ...]] = ("OK", "FAIL", "ERROR", "SKIPPED")
_STDERR_STATUSES: Final[frozenset[str]] = frozenset(
    {"WARN", "WARNING", "FAIL", "FAILED", "ERROR", "FATAL", "INVALID"}
)
_ANSI_ESCAPE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:\x1B\][^\x07\x1B]*(?:\x07|\x1B\\))"
    r"|(?:\x1B\[[0-?]*[ -/]*[@-~])"
    r"|(?:\x1B[@-_])"
)
_CHANGE_ORDER: Final[tuple[str, ...]] = (
    "regressed",
    "new",
    "improved",
    "removed",
)

TextRedactor = Callable[[str], str]


@unique
class ConsoleVerbosity(StrEnum):
    QUIET = "quiet"
    NORMAL = "normal"
    VERBOSE = "verbose"


@unique
class ConsoleChannel(StrEnum):
    STDOUT = "stdout"
    STDERR = "stderr"


@dataclass(frozen=True, slots=True)
class ConsoleStreams:
    stdout: TextIO
    stderr: TextIO

    def __post_init__(self) -> None:
        for field_name in ("stdout", "stderr"):
            stream = getattr(self, field_name)
            if not callable(getattr(stream, "write", None)):
                raise TypeError(f"{field_name} must expose callable write()")
            if not callable(getattr(stream, "flush", None)):
                raise TypeError(f"{field_name} must expose callable flush()")


@dataclass(frozen=True, slots=True)
class ConsoleMessage:
    text: str
    channel: ConsoleChannel = ConsoleChannel.STDOUT
    end: str = "\n"
    preserve_newlines: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")
        if not isinstance(self.channel, ConsoleChannel):
            raise TypeError("channel must be ConsoleChannel")
        if not isinstance(self.end, str):
            raise TypeError("end must be a string")
        if "\x00" in self.end:
            raise ValueError("end must not contain NUL")
        if type(self.preserve_newlines) is not bool:
            raise TypeError("preserve_newlines must be bool")


@dataclass(frozen=True, slots=True)
class RunSummaryView:
    application_name: str
    application_version: str
    run_id: str
    mode: str
    status: str
    files_ok: int
    files_fail: int
    files_error: int
    files_skipped: int
    direct_fail: int
    downstream_fail: int
    ambiguous_fail: int
    scenarios_ok: int
    scenarios_fail: int
    scenarios_error: int
    scenarios_skipped: int
    regressed: int
    new: int
    improved: int
    removed: int
    run_dir: Path
    summary_md: Path | None
    summary_json: Path | None
    ai_ready_md: Path | None
    manifest_json: Path | None

    def __post_init__(self) -> None:
        for field_name in (
            "application_name",
            "application_version",
            "run_id",
            "mode",
            "status",
        ):
            _require_text(getattr(self, field_name), field=field_name)
        if self.status not in _STATUS_ORDER:
            raise ValueError(f"unsupported run status: {self.status!r}")
        for field_name in (
            "files_ok",
            "files_fail",
            "files_error",
            "files_skipped",
            "direct_fail",
            "downstream_fail",
            "ambiguous_fail",
            "scenarios_ok",
            "scenarios_fail",
            "scenarios_error",
            "scenarios_skipped",
            "regressed",
            "new",
            "improved",
            "removed",
        ):
            _require_count(getattr(self, field_name), field=field_name)
        _require_path(self.run_dir, field="run_dir")
        for field_name in (
            "summary_md",
            "summary_json",
            "ai_ready_md",
            "manifest_json",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _require_path(value, field=field_name)

    def lines(self) -> tuple[str, ...]:
        result = [
            f"{self.application_name} {self.application_version}",
            f"Run: {self.run_id}",
            f"Mode: {self.mode}",
            f"Status: {self.status}",
            "",
            (
                "Files: "
                f"{self.files_ok} OK, "
                f"{self.files_fail} FAIL, "
                f"{self.files_error} ERROR, "
                f"{self.files_skipped} SKIPPED"
            ),
            (
                "Failures: "
                f"{self.direct_fail} direct, "
                f"{self.downstream_fail} downstream, "
                f"{self.ambiguous_fail} ambiguous"
            ),
            (
                "Scenarios: "
                f"{self.scenarios_ok} OK, "
                f"{self.scenarios_fail} FAIL, "
                f"{self.scenarios_error} ERROR, "
                f"{self.scenarios_skipped} SKIPPED"
            ),
            (
                "Regression: "
                f"{self.regressed} regressed, "
                f"{self.new} new, "
                f"{self.improved} improved, "
                f"{self.removed} removed"
            ),
            "",
            f"Run directory: {self.run_dir}",
        ]
        if self.summary_md is not None:
            result.append(f"Summary: {self.summary_md}")
        if self.summary_json is not None:
            result.append(f"JSON: {self.summary_json}")
        if self.ai_ready_md is not None:
            result.append(f"AI packet: {self.ai_ready_md}")
        if self.manifest_json is not None:
            result.append(f"Manifest: {self.manifest_json}")
        return tuple(result)


@runtime_checkable
class RunResultLike(Protocol):
    run_config: object
    run_paths: object
    overall_status: object
    totals: object
    diff_entries: Sequence[object]


class ConsolePresenter:
    __slots__ = ("_streams", "_verbosity", "_redactor", "_flush")

    def __init__(
        self,
        *,
        streams: ConsoleStreams | None = None,
        verbosity: ConsoleVerbosity | str = ConsoleVerbosity.NORMAL,
        redactor: TextRedactor | None = None,
        flush: bool = True,
    ) -> None:
        self._streams = streams or ConsoleStreams(sys.stdout, sys.stderr)
        self._verbosity = _coerce_verbosity(verbosity)
        if redactor is not None and not callable(redactor):
            raise TypeError("redactor must be callable or None")
        if type(flush) is not bool:
            raise TypeError("flush must be bool")
        self._redactor = redactor
        self._flush = flush

    @property
    def verbosity(self) -> ConsoleVerbosity:
        return self._verbosity

    @property
    def streams(self) -> ConsoleStreams:
        return self._streams

    def write(self, message: ConsoleMessage) -> None:
        if not isinstance(message, ConsoleMessage):
            raise TypeError("message must be ConsoleMessage")
        text = safe_console_text(
            message.text,
            redactor=self._redactor,
            max_length=_MAX_CONSOLE_MESSAGE,
            preserve_newlines=message.preserve_newlines,
        )
        stream = (
            self._streams.stdout
            if message.channel is ConsoleChannel.STDOUT
            else self._streams.stderr
        )
        stream.write(text)
        stream.write(message.end)
        if self._flush:
            stream.flush()

    def stdout(
        self,
        text: object = "",
        *,
        end: str = "\n",
        preserve_newlines: bool = False,
    ) -> None:
        self.write(
            ConsoleMessage(
                text=_coerce_message(text),
                channel=ConsoleChannel.STDOUT,
                end=end,
                preserve_newlines=preserve_newlines,
            )
        )

    def stderr(
        self,
        text: object = "",
        *,
        end: str = "\n",
        preserve_newlines: bool = False,
    ) -> None:
        self.write(
            ConsoleMessage(
                text=_coerce_message(text),
                channel=ConsoleChannel.STDERR,
                end=end,
                preserve_newlines=preserve_newlines,
            )
        )

    def warning(self, message: object) -> None:
        self.stderr(f"Warning: {_coerce_message(message)}")

    def error(
        self,
        error: object,
        *,
        category: str | None = None,
        command: str | None = None,
        run_dir: Path | None = None,
        summary_path: Path | None = None,
        remediation: str | None = None,
        cancelled: bool | None = None,
        debug: bool = False,
        traceback_text: str | None = None,
    ) -> None:
        for line in format_error(
            error,
            category=category,
            command=command,
            run_dir=run_dir,
            summary_path=summary_path,
            remediation=remediation,
            cancelled=cancelled,
            debug=debug,
            traceback_text=traceback_text,
            redactor=None,
        ):
            self.stderr(line, preserve_newlines="\n" in line)

    def run_summary(
        self,
        run_result: RunResultLike,
        *,
        application_version: str = __version__,
        existing_artifacts_only: bool = False,
    ) -> RunSummaryView:
        view = build_run_summary_view(
            run_result,
            application_version=application_version,
            existing_artifacts_only=existing_artifacts_only,
        )
        self.compatibility_warnings(run_result)
        if self._verbosity is ConsoleVerbosity.QUIET:
            return view
        for line in view.lines():
            self.stdout(line)
        return view

    def compatibility_warnings(self, run_result: object) -> tuple[str, ...]:
        run_config = getattr(run_result, "run_config", None)
        values = getattr(run_config, "compatibility_warnings", ())
        warnings = _string_sequence(
            values,
            field="run_config.compatibility_warnings",
        )
        for warning in warnings:
            self.warning(warning)
        return warnings

    def result(
        self,
        result: object,
        *,
        request: object | None = None,
        application_version: str = __version__,
        existing_artifacts_only: bool = False,
    ) -> object:
        """Present one canonical command result."""

        if isinstance(result, RunResultLike):
            _present_request_warnings_not_in_result(self, request, result)
            return self.run_summary(
                result,
                application_version=application_version,
                existing_artifacts_only=existing_artifacts_only,
            )

        for warning in _request_warnings(request):
            self.warning(warning)

        lines = format_result(
            result,
            verbose=self._verbosity is ConsoleVerbosity.VERBOSE,
        )
        if self._verbosity is ConsoleVerbosity.QUIET:
            lines = lines[:1]
        writer = self.stderr if _result_uses_stderr(result) else self.stdout
        for line in lines:
            writer(line, preserve_newlines="\n" in line)
        return result

    def progress(self, event: object) -> None:
        severity = _event_severity(event)
        warning_or_error = severity in {"WARN", "WARNING", "ERROR", "FATAL"}
        if (
            self._verbosity is not ConsoleVerbosity.VERBOSE
            and not warning_or_error
        ):
            return
        line = format_progress_event(event)
        if warning_or_error:
            self.stderr(line)
        else:
            self.stdout(line)

    def lifecycle(self, event: object) -> None:
        severity = _event_severity(event, level_field="level")
        warning_or_error = severity in {"WARN", "WARNING", "ERROR", "FATAL"}
        if (
            self._verbosity is not ConsoleVerbosity.VERBOSE
            and not warning_or_error
        ):
            return
        line = format_lifecycle_event(event)
        if warning_or_error:
            self.stderr(line)
        else:
            self.stdout(line)


def build_run_summary_view(
    run_result: RunResultLike,
    *,
    application_version: str = __version__,
    existing_artifacts_only: bool = False,
) -> RunSummaryView:
    if not isinstance(run_result, RunResultLike):
        raise TypeError("run_result must expose the canonical RunResult fields")
    if type(existing_artifacts_only) is not bool:
        raise TypeError("existing_artifacts_only must be bool")

    totals = run_result.totals
    paths = run_result.run_paths
    config = run_result.run_config
    changes = _change_counts(run_result.diff_entries)

    run_dir = _path_attribute(paths, "run_dir", required=True)
    summary_md = _optional_artifact_path(
        paths,
        "summary_md",
        existing_only=existing_artifacts_only,
    )
    summary_json = _optional_artifact_path(
        paths,
        "summary_json",
        existing_only=existing_artifacts_only,
    )
    ai_ready_md = _optional_artifact_path(
        paths,
        "ai_ready_md",
        existing_only=existing_artifacts_only,
    )
    manifest_json = _optional_artifact_path(
        paths,
        "manifest_json",
        existing_only=existing_artifacts_only,
    )

    return RunSummaryView(
        application_name=_APPLICATION_NAME,
        application_version=_require_text(
            application_version,
            field="application_version",
        ),
        run_id=_enum_text(
            getattr(paths, "run_id", None),
            field="run_paths.run_id",
        ),
        mode=_enum_text(
            getattr(config, "mode", None),
            field="run_config.mode",
        ),
        status=_enum_text(
            run_result.overall_status,
            field="run_result.overall_status",
        ).upper(),
        files_ok=_count_attribute(totals, "files_ok"),
        files_fail=_count_attribute(totals, "files_fail"),
        files_error=_count_attribute(totals, "files_error"),
        files_skipped=_count_attribute(totals, "files_skipped"),
        direct_fail=_count_attribute(totals, "direct_fail"),
        downstream_fail=_count_attribute(totals, "downstream_fail"),
        ambiguous_fail=_count_attribute(totals, "ambiguous_fail"),
        scenarios_ok=_count_attribute(totals, "scenarios_ok"),
        scenarios_fail=_count_attribute(totals, "scenarios_fail"),
        scenarios_error=_count_attribute(totals, "scenarios_error"),
        scenarios_skipped=_count_attribute(totals, "scenarios_skipped"),
        regressed=changes["regressed"],
        new=changes["new"],
        improved=changes["improved"],
        removed=changes["removed"],
        run_dir=run_dir,
        summary_md=summary_md,
        summary_json=summary_json,
        ai_ready_md=ai_ready_md,
        manifest_json=manifest_json,
    )


def format_run_summary(
    run_result: RunResultLike,
    *,
    application_version: str = __version__,
    existing_artifacts_only: bool = False,
) -> str:
    view = build_run_summary_view(
        run_result,
        application_version=application_version,
        existing_artifacts_only=existing_artifacts_only,
    )
    return "\n".join(view.lines())


def present_run_summary(
    run_result: RunResultLike,
    *,
    quiet: bool = False,
    verbose: bool = False,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    redactor: TextRedactor | None = None,
    application_version: str = __version__,
    existing_artifacts_only: bool = False,
) -> RunSummaryView:
    presenter = _presenter(
        quiet=quiet,
        verbose=verbose,
        stdout=stdout,
        stderr=stderr,
        redactor=redactor,
    )
    return presenter.run_summary(
        run_result,
        application_version=application_version,
        existing_artifacts_only=existing_artifacts_only,
    )



def format_result(
    result: object,
    *,
    verbose: bool = False,
) -> tuple[str, ...]:
    """Return a bounded text projection for a non-run command result."""

    if type(verbose) is not bool:
        raise TypeError("verbose must be bool")
    if result is None or type(result) is int:
        return ()
    if isinstance(result, str):
        return (result,)
    if isinstance(result, Path):
        return (str(result),)
    if type(result) is bool:
        return (f"Status: {'OK' if result else 'FAIL'}",)
    if isinstance(result, Mapping):
        return _mapping_lines(result, verbose=verbose)
    if isinstance(result, Sequence) and not isinstance(
        result,
        (str, bytes, bytearray),
    ):
        return _sequence_lines(result, verbose=verbose)
    return _object_lines(result, verbose=verbose)


def present_result(
    result: object,
    *,
    request: object | None = None,
    quiet: bool | None = None,
    verbose: bool | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    redactor: TextRedactor | None = None,
    application_version: str = __version__,
    existing_artifacts_only: bool = False,
) -> object:
    """Present a command result using request verbosity when available."""

    request_quiet, request_verbose = _request_verbosity(request)
    resolved_quiet = (
        request_quiet
        if quiet is None
        else _require_bool(quiet, field="quiet")
    )
    resolved_verbose = (
        request_verbose
        if verbose is None
        else _require_bool(verbose, field="verbose")
    )
    presenter = _presenter(
        quiet=resolved_quiet,
        verbose=resolved_verbose,
        stdout=stdout,
        stderr=stderr,
        redactor=redactor,
    )
    return presenter.result(
        result,
        request=request,
        application_version=application_version,
        existing_artifacts_only=existing_artifacts_only,
    )

def format_error(
    error: object,
    *,
    category: str | None = None,
    command: str | None = None,
    run_dir: Path | None = None,
    summary_path: Path | None = None,
    remediation: str | None = None,
    cancelled: bool | None = None,
    debug: bool = False,
    traceback_text: str | None = None,
    redactor: TextRedactor | None = None,
) -> tuple[str, ...]:
    if type(debug) is not bool:
        raise TypeError("debug must be bool")
    if cancelled is not None and type(cancelled) is not bool:
        raise TypeError("cancelled must be bool or None")

    message = safe_console_text(
        _error_message(error),
        redactor=redactor,
        max_length=_MAX_CONSOLE_MESSAGE,
    )
    normalized_category = (
        _optional_label(category, field="category")
        or _error_category(error)
        or "ERROR"
    )
    lines = [f"Error [{normalized_category}]: {message}"]

    normalized_command = _optional_text(command, field="command")
    if normalized_command is not None:
        lines.append(f"Command: {normalized_command}")

    if run_dir is not None:
        lines.append(f"Run directory: {_require_path(run_dir, field='run_dir')}")
    if summary_path is not None:
        lines.append(
            f"Summary: {_require_path(summary_path, field='summary_path')}"
        )

    normalized_remediation = _optional_text(
        remediation,
        field="remediation",
    )
    if normalized_remediation is not None:
        lines.append(f"Remediation: {normalized_remediation}")

    if cancelled is not None:
        lines.append(f"Cancelled: {'yes' if cancelled else 'no'}")

    if debug:
        rendered_traceback = traceback_text
        if rendered_traceback is None and isinstance(error, BaseException):
            rendered_traceback = "".join(
                traceback.format_exception(
                    type(error),
                    error,
                    error.__traceback__,
                )
            )
        if rendered_traceback:
            cleaned = safe_console_text(
                rendered_traceback,
                redactor=redactor,
                max_length=_MAX_TRACEBACK,
                preserve_newlines=True,
            )
            lines.extend(("Traceback:", cleaned))

    return tuple(lines)


def present_error(
    error: object,
    *,
    category: str | None = None,
    command: str | None = None,
    run_dir: Path | None = None,
    summary_path: Path | None = None,
    remediation: str | None = None,
    cancelled: bool | None = None,
    debug: bool = False,
    traceback_text: str | None = None,
    stderr: TextIO | None = None,
    redactor: TextRedactor | None = None,
) -> None:
    presenter = ConsolePresenter(
        streams=ConsoleStreams(sys.stdout, _stream_or_default(stderr, sys.stderr)),
        redactor=redactor,
    )
    presenter.error(
        error,
        category=category,
        command=command,
        run_dir=run_dir,
        summary_path=summary_path,
        remediation=remediation,
        cancelled=cancelled,
        debug=debug,
        traceback_text=traceback_text,
    )


def present_warning(
    message: object,
    *,
    stderr: TextIO | None = None,
    redactor: TextRedactor | None = None,
) -> None:
    ConsolePresenter(
        streams=ConsoleStreams(sys.stdout, _stream_or_default(stderr, sys.stderr)),
        redactor=redactor,
    ).warning(message)


def present_failure(
    message: object,
    *,
    command: str | None = None,
    run_dir: Path | None = None,
    summary_path: Path | None = None,
    remediation: str | None = None,
    stderr: TextIO | None = None,
    redactor: TextRedactor | None = None,
) -> None:
    present_error(
        message,
        category="VALIDATION",
        command=command,
        run_dir=run_dir,
        summary_path=summary_path,
        remediation=remediation,
        stderr=stderr,
        redactor=redactor,
    )


def present_progress(
    event: ProgressEvent,
    *,
    verbose: bool = False,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    redactor: TextRedactor | None = None,
) -> None:
    ConsolePresenter(
        streams=ConsoleStreams(
            _stream_or_default(stdout, sys.stdout),
            _stream_or_default(stderr, sys.stderr),
        ),
        verbosity=(
            ConsoleVerbosity.VERBOSE
            if verbose
            else ConsoleVerbosity.NORMAL
        ),
        redactor=redactor,
    ).progress(event)


def present_lifecycle_event(
    event: LifecycleEvent,
    *,
    verbose: bool = False,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    redactor: TextRedactor | None = None,
) -> None:
    ConsolePresenter(
        streams=ConsoleStreams(
            _stream_or_default(stdout, sys.stdout),
            _stream_or_default(stderr, sys.stderr),
        ),
        verbosity=(
            ConsoleVerbosity.VERBOSE
            if verbose
            else ConsoleVerbosity.NORMAL
        ),
        redactor=redactor,
    ).lifecycle(event)


def build_progress_sink(
    *,
    verbose: bool = False,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    redactor: TextRedactor | None = None,
) -> Callable[[ProgressEvent], None]:
    presenter = ConsolePresenter(
        streams=ConsoleStreams(
            _stream_or_default(stdout, sys.stdout),
            _stream_or_default(stderr, sys.stderr),
        ),
        verbosity=(
            ConsoleVerbosity.VERBOSE
            if verbose
            else ConsoleVerbosity.NORMAL
        ),
        redactor=redactor,
    )
    return presenter.progress


def build_lifecycle_sink(
    *,
    verbose: bool = False,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    redactor: TextRedactor | None = None,
) -> Callable[[LifecycleEvent], None]:
    presenter = ConsolePresenter(
        streams=ConsoleStreams(
            _stream_or_default(stdout, sys.stdout),
            _stream_or_default(stderr, sys.stderr),
        ),
        verbosity=(
            ConsoleVerbosity.VERBOSE
            if verbose
            else ConsoleVerbosity.NORMAL
        ),
        redactor=redactor,
    )
    return presenter.lifecycle


def format_progress_event(event: object) -> str:
    message = _event_message(event)
    stage = _optional_event_text(event, "stage")
    subject = _optional_event_text(event, "subject")
    completed = _optional_event_count(event, "completed")
    total = _optional_event_count(event, "total")

    prefix_parts: list[str] = []
    if stage is not None:
        prefix_parts.append(stage)
    if subject is not None:
        prefix_parts.append(subject)
    prefix = f"[{' / '.join(prefix_parts)}] " if prefix_parts else ""

    progress = ""
    if completed is not None and total is not None:
        progress = f" ({completed}/{total})"
    elif completed is not None:
        progress = f" ({completed})"

    return safe_console_text(
        f"{prefix}{message}{progress}",
        max_length=_MAX_CONSOLE_LINE,
    )


def format_lifecycle_event(event: object) -> str:
    message = _event_message(event)
    stage = _optional_event_text(event, "stage")
    status = _optional_event_text(event, "status")
    subject = _optional_event_text(event, "subject")

    prefix_parts = [
        value
        for value in (stage, subject, status)
        if value is not None
    ]
    prefix = f"[{' / '.join(prefix_parts)}] " if prefix_parts else ""
    return safe_console_text(
        f"{prefix}{message}",
        max_length=_MAX_CONSOLE_LINE,
    )


def safe_console_text(
    value: object,
    *,
    redactor: TextRedactor | None = None,
    max_length: int = _MAX_CONSOLE_MESSAGE,
    preserve_newlines: bool = False,
) -> str:
    if type(max_length) is not int or max_length < 1:
        raise ValueError("max_length must be a positive integer")
    text = _coerce_message(value).replace("\x00", "�")
    text = _strip_terminal_controls(text, preserve_newlines=preserve_newlines)
    if redactor is not None:
        if not callable(redactor):
            raise TypeError("redactor must be callable")
        text = redactor(text)
        if not isinstance(text, str):
            raise TypeError("redactor must return a string")
        text = text.replace("\x00", "�")
        text = _strip_terminal_controls(
            text,
            preserve_newlines=preserve_newlines,
        )
    if not preserve_newlines:
        text = " ".join(text.split())
    else:
        text = "\n".join(line.rstrip() for line in text.splitlines())
    if len(text) <= max_length:
        return text
    if max_length <= 3:
        return "." * max_length
    return f"{text[: max_length - 3]}..."


def print_error(error: object, **kwargs: object) -> None:
    present_error(error, **kwargs)


def print_warning(message: object, **kwargs: object) -> None:
    present_warning(message, **kwargs)


def print_failure(message: object, **kwargs: object) -> None:
    present_failure(message, **kwargs)


def _presenter(
    *,
    quiet: bool,
    verbose: bool,
    stdout: TextIO | None,
    stderr: TextIO | None,
    redactor: TextRedactor | None,
) -> ConsolePresenter:
    if type(quiet) is not bool:
        raise TypeError("quiet must be bool")
    if type(verbose) is not bool:
        raise TypeError("verbose must be bool")
    if quiet and verbose:
        raise ValueError("quiet and verbose are mutually exclusive")
    verbosity = (
        ConsoleVerbosity.QUIET
        if quiet
        else ConsoleVerbosity.VERBOSE
        if verbose
        else ConsoleVerbosity.NORMAL
    )
    return ConsolePresenter(
        streams=ConsoleStreams(
            _stream_or_default(stdout, sys.stdout),
            _stream_or_default(stderr, sys.stderr),
        ),
        verbosity=verbosity,
        redactor=redactor,
    )


def _change_counts(values: Iterable[object]) -> Mapping[str, int]:
    if isinstance(values, (str, bytes, bytearray, Mapping)):
        raise TypeError("diff_entries must be an iterable of structured entries")
    counts: Counter[str] = Counter()
    for entry in values:
        kind = getattr(entry, "change_kind", None)
        if kind is None:
            kind = getattr(entry, "kind", None)
        if kind is None:
            raise TypeError("diff entry must expose change_kind")
        canonical = _enum_text(kind, field="diff_entry.change_kind").lower()
        if canonical not in _CHANGE_ORDER:
            raise ValueError(f"unknown diff change kind: {canonical!r}")
        counts[canonical] += 1
    return {kind: counts[kind] for kind in _CHANGE_ORDER}


def _count_attribute(value: object, name: str) -> int:
    if not hasattr(value, name):
        raise TypeError(f"totals must expose {name}")
    return _require_count(getattr(value, name), field=f"totals.{name}")


def _path_attribute(
    value: object,
    name: str,
    *,
    required: bool,
) -> Path:
    if not hasattr(value, name):
        raise TypeError(f"run_paths must expose {name}")
    candidate = getattr(value, name)
    if candidate is None and not required:
        return candidate
    return _require_path(candidate, field=f"run_paths.{name}")


def _optional_artifact_path(
    paths: object,
    field: str,
    *,
    existing_only: bool,
) -> Path | None:
    if not hasattr(paths, field):
        return None
    value = getattr(paths, field)
    if value is None:
        return None
    path = _require_path(value, field=f"run_paths.{field}")
    if existing_only and not path.is_file():
        return None
    return path


def _event_message(event: object) -> str:
    if event is None:
        raise TypeError("event must not be None")
    value = getattr(event, "message", None)
    if value is None:
        value = getattr(event, "event", None)
    return _require_text(value, field="event.message")


def _event_severity(
    event: object,
    *,
    level_field: str = "severity",
) -> str:
    value = getattr(event, level_field, None)
    if value is None:
        return "INFO"
    return _enum_text(value, field=f"event.{level_field}").upper()


def _optional_event_text(event: object, field: str) -> str | None:
    value = getattr(event, field, None)
    if value is None:
        return None
    return _enum_text(value, field=f"event.{field}")


def _optional_event_count(event: object, field: str) -> int | None:
    value = getattr(event, field, None)
    if value is None:
        return None
    return _require_count(value, field=f"event.{field}")


def _error_message(error: object) -> str:
    if isinstance(error, BaseException):
        text = str(error).strip()
        return text or type(error).__name__
    return _coerce_message(error)


def _error_category(error: object) -> str | None:
    for field in ("category", "error_kind", "code"):
        value = getattr(error, field, None)
        if value is None:
            continue
        try:
            return _enum_text(value, field=f"error.{field}").upper()
        except (TypeError, ValueError):
            continue
    return None


def _enum_text(value: object, *, field: str) -> str:
    candidate = getattr(value, "value", value)
    return _require_text(candidate, field=field)


def _optional_label(value: object, *, field: str) -> str | None:
    text = _optional_text(value, field=field)
    return None if text is None else text.upper()


def _optional_text(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field=field)


def _string_sequence(value: object, *, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        raise TypeError(f"{field} must be a sequence, not one string")
    if not isinstance(value, Sequence):
        raise TypeError(f"{field} must be a sequence of strings")
    return tuple(
        _require_text(item, field=f"{field} item")
        for item in value
    )



def _request_verbosity(request: object | None) -> tuple[bool, bool]:
    if request is None:
        return False, False
    arguments = getattr(request, "arguments", None)
    if isinstance(arguments, Mapping):
        quiet = arguments.get("quiet", False)
        verbose = arguments.get("verbose", False)
    else:
        quiet = getattr(request, "quiet", False)
        verbose = getattr(request, "verbose", False)
    resolved_quiet = _optional_bool(quiet, field="request.quiet")
    resolved_verbose = _optional_bool(verbose, field="request.verbose")
    if resolved_quiet and resolved_verbose:
        raise ValueError("quiet and verbose are mutually exclusive")
    return resolved_quiet, resolved_verbose


def _request_warnings(request: object | None) -> tuple[str, ...]:
    if request is None:
        return ()
    return _string_sequence(
        getattr(request, "compatibility_warnings", ()),
        field="request.compatibility_warnings",
    )


def _present_request_warnings_not_in_result(
    presenter: ConsolePresenter,
    request: object | None,
    run_result: object,
) -> None:
    run_config = getattr(run_result, "run_config", None)
    existing = set(
        _string_sequence(
            getattr(run_config, "compatibility_warnings", ()),
            field="run_config.compatibility_warnings",
        )
    )
    for warning in _request_warnings(request):
        if warning not in existing:
            presenter.warning(warning)


def _mapping_lines(
    result: Mapping[object, object],
    *,
    verbose: bool,
) -> tuple[str, ...]:
    lines: list[str] = []
    for key, value in result.items():
        if not isinstance(key, str) or not key or key.startswith("_"):
            continue
        rendered = _scalar_text(value)
        if rendered is not None:
            lines.append(f"{_label(key)}: {rendered}")
        elif isinstance(value, Sequence) and not isinstance(
            value,
            (str, bytes, bytearray),
        ):
            lines.append(f"{_label(key)}: {len(value)}")
            if verbose:
                lines.extend(
                    f"  - {_detail_text(item)}"
                    for item in value[:_MAX_RESULT_ITEMS]
                )
        elif isinstance(value, Mapping):
            lines.append(f"{_label(key)}: {len(value)}")
    if not lines:
        raise TypeError("result mapping has no printable public values")
    return tuple(lines)


def _sequence_lines(
    result: Sequence[object],
    *,
    verbose: bool,
) -> tuple[str, ...]:
    if not result:
        return ()
    if not verbose:
        return (f"Items: {len(result)}",)
    return tuple(
        _detail_text(item)
        for item in result[:_MAX_RESULT_ITEMS]
    )


def _object_lines(
    result: object,
    *,
    verbose: bool,
) -> tuple[str, ...]:
    title = _label(type(result).__name__.removesuffix("Result"))
    status = _first_attribute(result, "overall_status", "status", "outcome")
    rendered_status = _scalar_text(status)
    ok = getattr(result, "ok", None)
    message = getattr(result, "message", None)

    if rendered_status is None and type(ok) is bool:
        rendered_status = "OK" if ok else "FAIL"

    if rendered_status is not None:
        lines = [f"{title}: {rendered_status}"]
        if isinstance(message, str) and message.strip():
            lines.append(f"Message: {message}")
    elif isinstance(message, str) and message.strip():
        lines = [f"{title}: {message}"]
    else:
        lines = [title]

    for field_name in (
        "run_dir",
        "summary_path",
        "manifest_path",
        "project_root",
        "project_file",
        "state_path",
        "destination",
        "destination_path",
    ):
        rendered = _scalar_text(getattr(result, field_name, None))
        if rendered is not None:
            lines.append(f"{_label(field_name)}: {rendered}")

    for field_name in ("errors", "warnings", "issues", "diagnostics"):
        value = getattr(result, field_name, None)
        if not isinstance(value, Sequence) or isinstance(
            value,
            (str, bytes, bytearray),
        ):
            continue
        lines.append(f"{_label(field_name)}: {len(value)}")
        if verbose:
            lines.extend(
                f"  - {_detail_text(item)}"
                for item in value[:_MAX_RESULT_ITEMS]
            )
    return tuple(lines)


def _result_uses_stderr(result: object) -> bool:
    status = _first_attribute(result, "overall_status", "status", "outcome")
    rendered = _scalar_text(status)
    if rendered is not None:
        return rendered.strip().upper() in _STDERR_STATUSES
    ok = getattr(result, "ok", None)
    return type(ok) is bool and not ok


def _first_attribute(result: object, *names: str) -> object | None:
    for name in names:
        value = getattr(result, name, None)
        if value is not None:
            return value
    return None


def _scalar_text(value: object) -> str | None:
    if value is None:
        return None
    candidate = getattr(value, "value", value)
    if isinstance(candidate, Path):
        return str(candidate)
    if isinstance(candidate, str):
        return candidate
    if type(candidate) in {bool, int, float}:
        return str(candidate)
    return None


def _detail_text(value: object) -> str:
    if isinstance(value, (str, Path)):
        return str(value)
    for field_name in ("message", "reason", "path", "id", "code"):
        rendered = _scalar_text(getattr(value, field_name, None))
        if rendered:
            return rendered
    return _coerce_message(value)


def _label(value: str) -> str:
    text = re.sub(r"(?<!^)(?=[A-Z])", " ", value.replace("_", " "))
    normalized = " ".join(text.split())
    return normalized[:1].upper() + normalized[1:] if normalized else "Result"


def _stream_or_default(stream: TextIO | None, default: TextIO) -> TextIO:
    return default if stream is None else stream


def _require_bool(value: object, *, field: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field} must be bool")
    return value


def _optional_bool(value: object, *, field: str) -> bool:
    if value is None:
        return False
    return _require_bool(value, field=field)

def _coerce_verbosity(
    value: ConsoleVerbosity | str,
) -> ConsoleVerbosity:
    if isinstance(value, ConsoleVerbosity):
        return value
    if not isinstance(value, str):
        raise TypeError("verbosity must be ConsoleVerbosity or string")
    try:
        return ConsoleVerbosity(value)
    except ValueError as exc:
        raise ValueError(f"unknown console verbosity {value!r}") from exc


def _coerce_message(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, BaseException):
        return str(value).strip() or type(value).__name__
    return str(value)


def _require_text(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    return value


def _require_count(value: object, *, field: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def _require_path(value: object, *, field: str) -> Path:
    if not isinstance(value, Path):
        raise TypeError(f"{field} must be pathlib.Path")
    if "\x00" in str(value):
        raise ValueError(f"{field} must not contain NUL")
    return value


def _strip_terminal_controls(
    value: str,
    *,
    preserve_newlines: bool,
) -> str:
    cleaned = _ANSI_ESCAPE_RE.sub("", value)
    result: list[str] = []
    for character in cleaned:
        codepoint = ord(character)
        if character == "\n" and preserve_newlines:
            result.append(character)
        elif character == "\r" and preserve_newlines:
            continue
        elif character == "\t":
            result.append(" ")
        elif codepoint < 32 or codepoint == 127:
            continue
        else:
            result.append(character)
    return "".join(result)



__all__ = (
    "ConsoleChannel",
    "ConsoleMessage",
    "ConsolePresenter",
    "ConsoleStreams",
    "ConsoleVerbosity",
    "RunResultLike",
    "RunSummaryView",
    "TextRedactor",
    "build_lifecycle_sink",
    "build_progress_sink",
    "build_run_summary_view",
    "format_error",
    "format_lifecycle_event",
    "format_progress_event",
    "format_result",
    "format_run_summary",
    "present_error",
    "present_failure",
    "present_lifecycle_event",
    "present_progress",
    "present_result",
    "present_run_summary",
    "present_warning",
    "print_error",
    "print_failure",
    "print_warning",
    "safe_console_text",
)
