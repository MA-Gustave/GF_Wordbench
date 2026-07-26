"""Canonical PySide6 entrypoint for the GF Wordbench desktop GUI."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import re
import sys
import threading
import traceback
from types import TracebackType
from typing import Final, Protocol, TextIO, runtime_checkable

from gf_wordbench.version import __version__

APPLICATION_NAME: Final[str] = "GF Wordbench"
APPLICATION_DISPLAY_NAME: Final[str] = "GF Wordbench"
ORGANIZATION_NAME: Final[str] = "GF Wordbench"
ORGANIZATION_DOMAIN: Final[str] = "gf-wordbench.local"

EXIT_OK: Final[int] = 0
EXIT_RUNTIME_ERROR: Final[int] = 3

_MAX_ERROR_SUMMARY: Final[int] = 2_000
_MAX_TRACEBACK_LENGTH: Final[int] = 250_000
_SECRET_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?i)\b("
    r"api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret"
    r")\b(\s*[:=]\s*)([^\s,;]+)"
)


@runtime_checkable
class GuiRuntime(Protocol):
    """Bootstrap-owned GUI composition returned to the entrypoint."""

    @property
    def window(self) -> object:
        """Return the top-level Qt window."""

    def shutdown(self) -> None:
        """Release GUI-owned resources without starting new work."""


GuiRuntimeFactory = Callable[[object], GuiRuntime]


@dataclass(frozen=True, slots=True)
class ExceptionHookState:
    """Previous process exception hooks restored during shutdown."""

    sys_hook: Callable[
        [type[BaseException], BaseException, TracebackType | None],
        object,
    ]
    thread_hook: Callable[[threading.ExceptHookArgs], object]


class FatalErrorReporter:
    """Record bounded fatal-error details and present a concise Qt dialog."""

    __slots__ = ("_application", "_stderr", "_reporting")

    def __init__(
        self,
        application: object,
        *,
        stderr: TextIO = sys.stderr,
    ) -> None:
        self._application = application
        self._stderr = stderr
        self._reporting = False

    def report(
        self,
        exception_type: type[BaseException],
        exception: BaseException,
        traceback_object: TracebackType | None,
        *,
        title: str = "GF Wordbench could not continue",
        show_dialog: bool = True,
    ) -> Path | None:
        if self._reporting:
            self._write_stderr(
                f"{title}: {_safe_exception_summary(exception)}"
            )
            return None

        self._reporting = True
        try:
            details = _format_exception(
                exception_type,
                exception,
                traceback_object,
            )
            log_path = self._write_crash_log(details)
            summary = _safe_exception_summary(exception)
            self._write_stderr(f"{title}: {summary}")
            if log_path is not None:
                self._write_stderr(f"Technical details: {log_path}")

            if show_dialog:
                self._show_dialog(
                    title=title,
                    summary=summary,
                    details=details,
                    log_path=log_path,
                )
            return log_path
        finally:
            self._reporting = False

    def report_thread_exception(
        self,
        args: threading.ExceptHookArgs,
    ) -> None:
        self.report(
            args.exc_type,
            args.exc_value,
            args.exc_traceback,
            title="Unexpected GUI worker failure",
            show_dialog=False,
        )

    def _write_crash_log(self, details: str) -> Path | None:
        try:
            directory = _application_log_directory()
            directory.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
            path = directory / f"gui_crash_{timestamp}.log"
            payload = (
                f"application={APPLICATION_NAME}\n"
                f"version={__version__}\n"
                f"timestamp_utc={datetime.now(UTC).isoformat()}\n\n"
                f"{details}"
            )
            path.write_text(payload, encoding="utf-8", newline="\n")
            return path
        except Exception:
            return None

    def _show_dialog(
        self,
        *,
        title: str,
        summary: str,
        details: str,
        log_path: Path | None,
    ) -> None:
        try:
            from PySide6.QtWidgets import QMessageBox

            dialog = QMessageBox()
            dialog.setIcon(QMessageBox.Icon.Critical)
            dialog.setWindowTitle(title)
            dialog.setText(summary)
            dialog.setInformativeText(
                (
                    "Review the technical details and restart GF Wordbench."
                    if log_path is None
                    else (
                        "Technical details were written to:\n"
                        f"{log_path}"
                    )
                )
            )
            dialog.setDetailedText(details)
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            dialog.exec()
        except Exception:
            return

    def _write_stderr(self, message: str) -> None:
        try:
            self._stderr.write(f"{message}\n")
            self._stderr.flush()
        except Exception:
            return


def main(argv: Sequence[str] | None = None) -> int:
    """Create the Qt application, bootstrap the GUI, and run its event loop."""

    arguments = _normalize_argv(argv)

    try:
        application, owns_application = _create_qapplication(arguments)
    except Exception as exc:
        _write_startup_failure(exc)
        return EXIT_RUNTIME_ERROR

    _configure_application(application)
    reporter = FatalErrorReporter(application)
    previous_hooks = install_exception_hooks(reporter)

    runtime: GuiRuntime | None = None
    result = EXIT_RUNTIME_ERROR

    try:
        runtime = _default_runtime_factory(application)
        _validate_runtime(runtime)
        _show_window(runtime.window)

        if not owns_application:
            return EXIT_OK

        qt_result = application.exec()
        result = EXIT_OK if int(qt_result) == 0 else EXIT_RUNTIME_ERROR
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        reporter.report(
            type(exc),
            exc,
            exc.__traceback__,
            title="GF Wordbench GUI startup failed",
        )
        result = EXIT_RUNTIME_ERROR
    finally:
        if runtime is not None:
            try:
                runtime.shutdown()
            except Exception as exc:
                reporter.report(
                    type(exc),
                    exc,
                    exc.__traceback__,
                    title="GF Wordbench GUI shutdown failed",
                    show_dialog=False,
                )
                result = EXIT_RUNTIME_ERROR
        restore_exception_hooks(previous_hooks)

    return result


def install_exception_hooks(
    reporter: FatalErrorReporter,
) -> ExceptionHookState:
    """Install bounded process-wide handlers for otherwise uncaught failures."""

    if not isinstance(reporter, FatalErrorReporter):
        raise TypeError("reporter must be FatalErrorReporter")

    previous = ExceptionHookState(
        sys_hook=sys.excepthook,
        thread_hook=threading.excepthook,
    )

    def sys_hook(
        exception_type: type[BaseException],
        exception: BaseException,
        traceback_object: TracebackType | None,
    ) -> None:
        if issubclass(exception_type, KeyboardInterrupt):
            previous.sys_hook(
                exception_type,
                exception,
                traceback_object,
            )
            return
        reporter.report(
            exception_type,
            exception,
            traceback_object,
            title="Unexpected GF Wordbench GUI failure",
        )

    def thread_hook(args: threading.ExceptHookArgs) -> None:
        if issubclass(args.exc_type, SystemExit):
            return
        reporter.report_thread_exception(args)

    sys.excepthook = sys_hook
    threading.excepthook = thread_hook
    return previous


def restore_exception_hooks(state: ExceptionHookState) -> None:
    """Restore exception hooks previously returned by ``install_exception_hooks``."""

    if not isinstance(state, ExceptionHookState):
        raise TypeError("state must be ExceptionHookState")
    sys.excepthook = state.sys_hook
    threading.excepthook = state.thread_hook


def _default_runtime_factory(application: object) -> GuiRuntime:
    from gf_wordbench.bootstrap import build_gui_runtime

    runtime = build_gui_runtime(application)
    return runtime


def _create_qapplication(
    argv: tuple[str, ...],
) -> tuple[object, bool]:
    from PySide6.QtWidgets import QApplication

    existing = QApplication.instance()
    if existing is not None:
        if not isinstance(existing, QApplication):
            raise RuntimeError(
                "A non-GUI Qt application already exists in this process."
            )
        return existing, False

    return QApplication(list(argv)), True


def _configure_application(application: object) -> None:
    setters = (
        ("setApplicationName", APPLICATION_NAME),
        ("setApplicationDisplayName", APPLICATION_DISPLAY_NAME),
        ("setApplicationVersion", __version__),
        ("setOrganizationName", ORGANIZATION_NAME),
        ("setOrganizationDomain", ORGANIZATION_DOMAIN),
    )
    for method_name, value in setters:
        method = getattr(application, method_name, None)
        if callable(method):
            method(value)

    set_quit = getattr(application, "setQuitOnLastWindowClosed", None)
    if callable(set_quit):
        set_quit(True)


def _validate_runtime(runtime: object) -> None:
    if not isinstance(runtime, GuiRuntime):
        raise TypeError(
            "build_gui_runtime() must return an object satisfying GuiRuntime"
        )
    _require_callable_member(runtime.window, "show")
    _require_callable_member(runtime, "shutdown")


def _show_window(window: object) -> None:
    show = _require_callable_member(window, "show")
    show()

    raise_ = getattr(window, "raise_", None)
    if callable(raise_):
        raise_()

    activate = getattr(window, "activateWindow", None)
    if callable(activate):
        activate()


def _require_callable_member(
    value: object,
    name: str,
) -> Callable[..., object]:
    member = getattr(value, name, None)
    if not callable(member):
        raise TypeError(f"{type(value).__name__}.{name} must be callable")
    return member


def _normalize_argv(
    argv: Sequence[str] | None,
) -> tuple[str, ...]:
    source = sys.argv if argv is None else argv
    if isinstance(source, (str, bytes, bytearray)):
        raise TypeError("argv must be a sequence of strings")

    result: list[str] = []
    for index, item in enumerate(source):
        if not isinstance(item, str):
            raise TypeError(f"argv[{index}] must be a string")
        if "\x00" in item:
            raise ValueError(f"argv[{index}] must not contain NUL")
        result.append(item)

    if not result:
        result.append("gf-wordbench-gui")
    return tuple(result)


def _application_log_directory() -> Path:
    try:
        from PySide6.QtCore import QStandardPaths

        location = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppLocalDataLocation
        )
        if location:
            return Path(location) / "logs"
    except Exception:
        pass

    return Path.home() / ".gf_wordbench" / "logs"


def _format_exception(
    exception_type: type[BaseException],
    exception: BaseException,
    traceback_object: TracebackType | None,
) -> str:
    rendered = "".join(
        traceback.format_exception(
            exception_type,
            exception,
            traceback_object,
        )
    )
    rendered = _redact_secrets(rendered.replace("\x00", "\\x00"))
    if len(rendered) > _MAX_TRACEBACK_LENGTH:
        rendered = (
            f"{rendered[: _MAX_TRACEBACK_LENGTH - 28]}"
            "\n...[traceback truncated]\n"
        )
    return rendered


def _safe_exception_summary(exception: BaseException) -> str:
    message = " ".join(
        str(exception).replace("\x00", "\\x00").split()
    )
    message = _redact_secrets(message)
    if not message:
        message = type(exception).__name__
    if len(message) > _MAX_ERROR_SUMMARY:
        message = f"{message[: _MAX_ERROR_SUMMARY - 3]}..."
    return message


def _redact_secrets(value: str) -> str:
    return _SECRET_PATTERN.sub(
        lambda match: (
            f"{match.group(1)}{match.group(2)}<redacted>"
        ),
        value,
    )


def _write_startup_failure(exception: BaseException) -> None:
    summary = _safe_exception_summary(exception)
    try:
        sys.stderr.write(f"GF Wordbench GUI startup failed: {summary}\n")
        sys.stderr.flush()
    except Exception:
        return


__all__ = (
    "APPLICATION_DISPLAY_NAME",
    "APPLICATION_NAME",
    "ExceptionHookState",
    "FatalErrorReporter",
    "GuiRuntime",
    "GuiRuntimeFactory",
    "main",
    "install_exception_hooks",
    "restore_exception_hooks",
)


if __name__ == "__main__":
    raise SystemExit(main())
