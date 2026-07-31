"""PySide6 dialog adapters for the GF Wordbench desktop entrypoint."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from traceback import format_exception
from typing import Final, TypeAlias

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gf_wordbench.kernel.errors import GFWordbenchError

__all__ = (
    "ConfirmationPresentation",
    "DialogService",
    "DialogSeverity",
    "ErrorPresentation",
    "PathSelection",
    "confirm_action",
    "confirm_run",
    "error_presentation_from_exception",
    "resolve_initial_location",
    "select_existing_directory",
    "select_existing_file",
    "select_language_path",
    "select_output_directory",
    "show_error",
    "show_fatal_error",
    "show_information",
    "show_warning",
)

PathLike: TypeAlias = str | Path
PathValidator: TypeAlias = Callable[[Path], bool]

_MAX_DIALOG_TEXT: Final[int] = 200_000
_MAX_SUMMARY_TEXT: Final[int] = 8_000
_MAX_PLAN_ITEMS: Final[int] = 1_000
_GF_SOURCE_FILTER: Final[str] = "Grammatical Framework source (*.gf);;All files (*)"
_VALIDATION_PROFILE_FILTER: Final[str] = (
    "GF Wordbench validation profile (project.toml);;TOML files (*.toml);;All files (*)"
)


@unique
class DialogSeverity(StrEnum):
    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class ErrorPresentation:
    summary: str
    recommended_action: str = ""
    technical_details: str = ""
    evidence_path: Path | None = None
    code: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.summary, field="summary", allow_empty=False, maximum=_MAX_SUMMARY_TEXT)
        _require_text(
            self.recommended_action,
            field="recommended_action",
            allow_empty=True,
            maximum=_MAX_SUMMARY_TEXT,
        )
        _require_text(
            self.technical_details,
            field="technical_details",
            allow_empty=True,
            maximum=_MAX_DIALOG_TEXT,
        )
        if self.evidence_path is not None and not isinstance(self.evidence_path, Path):
            raise TypeError("evidence_path must be a pathlib.Path or None")
        if self.code is not None:
            _require_text(self.code, field="code", allow_empty=False, maximum=128)

    def details_text(self) -> str:
        parts: list[str] = []
        if self.code:
            parts.append(f"Code: {self.code}")
        if self.evidence_path is not None:
            parts.append(f"Evidence: {self.evidence_path}")
        if self.technical_details:
            parts.append(self.technical_details)
        return "\n\n".join(parts)


@dataclass(frozen=True, slots=True)
class ConfirmationPresentation:
    title: str
    action_label: str
    resolved_plan: tuple[tuple[str, str], ...]
    blocking_errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    explanatory_text: str = ""
    release: bool = False

    def __post_init__(self) -> None:
        _require_text(self.title, field="title", allow_empty=False, maximum=512)
        _require_text(self.action_label, field="action_label", allow_empty=False, maximum=128)
        _require_text(
            self.explanatory_text,
            field="explanatory_text",
            allow_empty=True,
            maximum=_MAX_SUMMARY_TEXT,
        )
        if len(self.resolved_plan) > _MAX_PLAN_ITEMS:
            raise ValueError("resolved_plan contains too many items")
        for index, item in enumerate(self.resolved_plan):
            if not isinstance(item, tuple) or len(item) != 2:
                raise TypeError(f"resolved_plan[{index}] must be a two-item tuple")
            _require_text(item[0], field=f"resolved_plan[{index}].label", allow_empty=False)
            _require_text(item[1], field=f"resolved_plan[{index}].value", allow_empty=True)
        _validate_messages(self.blocking_errors, field="blocking_errors")
        _validate_messages(self.warnings, field="warnings")
        if type(self.release) is not bool:
            raise TypeError("release must be a bool")


@dataclass(frozen=True, slots=True)
class PathSelection:
    value: Path | None
    cancelled: bool

    def __post_init__(self) -> None:
        if self.value is not None and not isinstance(self.value, Path):
            raise TypeError("value must be a pathlib.Path or None")
        if type(self.cancelled) is not bool:
            raise TypeError("cancelled must be a bool")


class _ConfirmationDialog(QDialog):
    def __init__(
        self,
        presentation: ConfirmationPresentation,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._presentation = presentation
        self.setWindowTitle(presentation.title)
        self.setModal(True)
        self.setMinimumSize(680, 520)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setAccessibleName(presentation.title)

        layout = QVBoxLayout(self)

        heading = QLabel(presentation.title, self)
        heading.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        heading.setWordWrap(True)
        heading.setAccessibleName("Confirmation title")
        layout.addWidget(heading)

        if presentation.explanatory_text:
            explanation = QLabel(presentation.explanatory_text, self)
            explanation.setWordWrap(True)
            explanation.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            explanation.setAccessibleName("Confirmation explanation")
            layout.addWidget(explanation)

        if presentation.blocking_errors:
            layout.addWidget(
                _message_group(
                    "Blocking errors",
                    presentation.blocking_errors,
                    parent=self,
                )
            )

        if presentation.warnings:
            layout.addWidget(_message_group("Warnings", presentation.warnings, parent=self))

        plan_group = QGroupBox("Resolved plan", self)
        plan_group.setAccessibleName("Resolved plan")
        plan_layout = QFormLayout(plan_group)
        plan_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        for label_text, value_text in presentation.resolved_plan:
            value_label = QLabel(value_text, plan_group)
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_label.setAccessibleName(label_text)
            plan_layout.addRow(f"{label_text}:", value_label)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(plan_group)
        scroll.setAccessibleName("Resolved plan details")
        layout.addWidget(scroll, 1)

        if presentation.release:
            release_notice = QLabel(
                "Every required stage will execute. This run may take longer. "
                "Gold files will not be modified.",
                self,
            )
            release_notice.setWordWrap(True)
            release_notice.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            release_notice.setAccessibleName("Release confirmation notice")
            layout.addWidget(release_notice)

        buttons = QDialogButtonBox(self)
        self._action_button = buttons.addButton(
            presentation.action_label,
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        cancel_button = buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        self._action_button.setDefault(True)
        self._action_button.setAutoDefault(True)
        self._action_button.setEnabled(not presentation.blocking_errors)
        self._action_button.setAccessibleName(presentation.action_label)
        cancel_button.setAccessibleName("Cancel")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.reject()
        event.accept()


class DialogService:
    def __init__(self, parent: QWidget | None = None) -> None:
        self._parent = parent
        self._last_directories: dict[str, Path] = {}

    @property
    def parent(self) -> QWidget | None:
        return self._parent

    def set_parent(self, parent: QWidget | None) -> None:
        self._parent = parent

    def last_directory(self, purpose: str) -> Path | None:
        return self._last_directories.get(_normalize_purpose(purpose))

    def remember_directory(self, purpose: str, directory: PathLike) -> None:
        checked = _coerce_path(directory, field="directory")
        self._last_directories[_normalize_purpose(purpose)] = checked

    def select_directory(
        self,
        *,
        title: str,
        purpose: str,
        current: PathLike | None = None,
        base_root: PathLike | None = None,
        project_root: PathLike | None = None,
        validator: PathValidator | None = None,
        rejection_message: str = "The selected directory is not permitted.",
    ) -> PathSelection:
        result = select_existing_directory(
            self._parent,
            title=title,
            current=current,
            base_root=base_root,
            project_root=project_root,
            last_directory=self.last_directory(purpose),
            validator=validator,
            rejection_message=rejection_message,
        )
        if not result.cancelled and result.value is not None:
            self.remember_directory(purpose, result.value)
        return result

    def select_file(
        self,
        *,
        title: str,
        purpose: str,
        current: PathLike | None = None,
        base_root: PathLike | None = None,
        project_root: PathLike | None = None,
        file_filter: str = "All files (*)",
        validator: PathValidator | None = None,
        rejection_message: str = "The selected file is not permitted.",
    ) -> PathSelection:
        result = select_existing_file(
            self._parent,
            title=title,
            current=current,
            base_root=base_root,
            project_root=project_root,
            last_directory=self.last_directory(purpose),
            file_filter=file_filter,
            validator=validator,
            rejection_message=rejection_message,
        )
        if not result.cancelled and result.value is not None:
            self.remember_directory(purpose, result.value.parent)
        return result

    def select_language_path(
        self,
        *,
        current: PathLike | None = None,
        rgl_root: PathLike | None = None,
    ) -> PathSelection:
        result = select_language_path(
            self._parent,
            current=current,
            base_root=rgl_root,
            last_directory=self.last_directory("language"),
        )
        if result.cancelled or result.value is None:
            return result
        remembered = result.value if result.value.is_dir() else result.value.parent
        self.remember_directory("language", remembered)
        return result

    def select_validation_profile(
        self,
        *,
        current: PathLike | None = None,
        base_root: PathLike | None = None,
    ) -> PathSelection:
        return self.select_file(
            title="Open GF Wordbench validation profile",
            purpose="validation_profile",
            current=current,
            base_root=base_root,
            file_filter=_VALIDATION_PROFILE_FILTER,
            validator=lambda path: path.name == "project.toml",
            rejection_message="Select a GF Wordbench project.toml validation profile.",
        )

    def select_project_root(
        self,
        *,
        current: PathLike | None = None,
    ) -> PathSelection:
        """Compatibility adapter for the superseded mandatory-project startup flow."""
        result = self.select_validation_profile(current=current, base_root=current)
        if result.cancelled or result.value is None:
            return result
        profile_file = result.value
        root = (
            profile_file.parent.parent
            if profile_file.parent.name == "project"
            else profile_file.parent
        )
        self.remember_directory("project", root)
        return PathSelection(value=root, cancelled=False)

    def confirm_run(self, presentation: ConfirmationPresentation) -> bool:
        return confirm_run(self._parent, presentation)

    def information(self, title: str, message: str, *, details: str = "") -> None:
        show_information(self._parent, title, message, details=details)

    def warning(self, title: str, message: str, *, details: str = "") -> None:
        show_warning(self._parent, title, message, details=details)

    def error(self, presentation: ErrorPresentation) -> None:
        show_error(self._parent, presentation)


def error_presentation_from_exception(
    exc: BaseException,
    *,
    summary: str | None = None,
    recommended_action: str = "Review the details and retry when the cause is resolved.",
    evidence_path: PathLike | None = None,
    include_traceback: bool = True,
    sensitive_values: Iterable[str] = (),
) -> ErrorPresentation:
    if not isinstance(exc, BaseException):
        raise TypeError("exc must be an exception")
    redactions = _redaction_values(sensitive_values)

    if isinstance(exc, GFWordbenchError):
        effective_summary = summary or exc.message
        detail_parts = [exc.detail] if exc.detail else []
        if exc.stage:
            detail_parts.append(f"Stage: {exc.stage}")
        if exc.operation:
            detail_parts.append(f"Operation: {exc.operation}")
        if exc.subject:
            detail_parts.append(f"Subject: {exc.subject}")
        if exc.evidence_paths:
            detail_parts.append("Evidence:\n" + "\n".join(exc.evidence_paths))
        code = exc.code
    else:
        effective_summary = summary or "GF Wordbench encountered an unexpected error."
        detail_parts = [f"{type(exc).__name__}: {exc}"]
        code = None

    if include_traceback:
        detail_parts.append("".join(format_exception(type(exc), exc, exc.__traceback__)))

    details = _sanitize_text("\n\n".join(part for part in detail_parts if part), redactions)
    effective_summary = _sanitize_text(effective_summary, redactions, maximum=_MAX_SUMMARY_TEXT)
    action = _sanitize_text(recommended_action, redactions, maximum=_MAX_SUMMARY_TEXT)

    return ErrorPresentation(
        summary=effective_summary,
        recommended_action=action,
        technical_details=details,
        evidence_path=None if evidence_path is None else _coerce_path(evidence_path),
        code=code,
    )


def show_information(
    parent: QWidget | None,
    title: str,
    message: str,
    *,
    details: str = "",
) -> None:
    _show_message(
        parent,
        severity=DialogSeverity.INFORMATION,
        title=title,
        message=message,
        details=details,
    )


def show_warning(
    parent: QWidget | None,
    title: str,
    message: str,
    *,
    details: str = "",
) -> None:
    _show_message(
        parent,
        severity=DialogSeverity.WARNING,
        title=title,
        message=message,
        details=details,
    )


def show_error(parent: QWidget | None, presentation: ErrorPresentation) -> None:
    _show_message(
        parent,
        severity=DialogSeverity.ERROR,
        title="GF Wordbench error",
        message=presentation.summary,
        informative_text=presentation.recommended_action,
        details=presentation.details_text(),
    )


def show_fatal_error(parent: QWidget | None, presentation: ErrorPresentation) -> None:
    _show_message(
        parent,
        severity=DialogSeverity.CRITICAL,
        title="GF Wordbench fatal error",
        message=presentation.summary,
        informative_text=presentation.recommended_action,
        details=presentation.details_text(),
    )


def confirm_action(
    parent: QWidget | None,
    *,
    title: str,
    message: str,
    accept_label: str,
    details: str = "",
    destructive: bool = False,
) -> bool:
    _require_text(title, field="title", allow_empty=False)
    _require_text(message, field="message", allow_empty=False)
    _require_text(accept_label, field="accept_label", allow_empty=False)
    _require_text(details, field="details", allow_empty=True, maximum=_MAX_DIALOG_TEXT)

    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setIcon(
        QMessageBox.Icon.Warning if destructive else QMessageBox.Icon.Question
    )
    box.setText(message)
    box.setTextFormat(Qt.TextFormat.PlainText)
    if details:
        box.setDetailedText(details)
    accept = box.addButton(accept_label, QMessageBox.ButtonRole.AcceptRole)
    cancel = box.addButton(QMessageBox.StandardButton.Cancel)
    box.setDefaultButton(cancel)
    box.setEscapeButton(cancel)
    box.exec()
    return box.clickedButton() is accept


def confirm_run(
    parent: QWidget | None,
    presentation: ConfirmationPresentation,
) -> bool:
    if not isinstance(presentation, ConfirmationPresentation):
        raise TypeError("presentation must be ConfirmationPresentation")
    dialog = _ConfirmationDialog(presentation, parent)
    return dialog.exec() == QDialog.DialogCode.Accepted


def select_existing_directory(
    parent: QWidget | None,
    *,
    title: str,
    current: PathLike | None = None,
    base_root: PathLike | None = None,
    project_root: PathLike | None = None,
    last_directory: PathLike | None = None,
    validator: PathValidator | None = None,
    rejection_message: str = "The selected directory is not permitted.",
) -> PathSelection:
    _require_text(title, field="title", allow_empty=False)
    initial = resolve_initial_location(
        current=current,
        base_root=base_root,
        project_root=project_root,
        last_directory=last_directory,
    )
    selected = QFileDialog.getExistingDirectory(
        parent,
        title,
        str(initial),
        QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
    )
    if not selected:
        return PathSelection(value=_optional_path(current), cancelled=True)
    candidate = Path(selected)
    if not candidate.is_dir():
        show_warning(parent, "Invalid directory", "The selected directory does not exist.")
        return PathSelection(value=_optional_path(current), cancelled=True)
    if validator is not None and not validator(candidate):
        show_warning(parent, "Invalid directory", rejection_message)
        return PathSelection(value=_optional_path(current), cancelled=True)
    return PathSelection(value=candidate, cancelled=False)


def select_output_directory(
    parent: QWidget | None,
    *,
    title: str,
    current: PathLike | None = None,
    base_root: PathLike | None = None,
    project_root: PathLike | None = None,
    last_directory: PathLike | None = None,
    validator: PathValidator | None = None,
    rejection_message: str = "The selected output directory is not permitted.",
) -> PathSelection:
    _require_text(title, field="title", allow_empty=False)
    initial = resolve_initial_location(
        current=current,
        base_root=base_root,
        project_root=project_root,
        last_directory=last_directory,
    )
    selected = QFileDialog.getExistingDirectory(
        parent,
        title,
        str(initial),
        QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
    )
    if not selected:
        return PathSelection(value=_optional_path(current), cancelled=True)
    candidate = Path(selected)
    if validator is not None and not validator(candidate):
        show_warning(parent, "Invalid output directory", rejection_message)
        return PathSelection(value=_optional_path(current), cancelled=True)
    return PathSelection(value=candidate, cancelled=False)


def select_existing_file(
    parent: QWidget | None,
    *,
    title: str,
    current: PathLike | None = None,
    base_root: PathLike | None = None,
    project_root: PathLike | None = None,
    last_directory: PathLike | None = None,
    file_filter: str = "All files (*)",
    validator: PathValidator | None = None,
    rejection_message: str = "The selected file is not permitted.",
) -> PathSelection:
    _require_text(title, field="title", allow_empty=False)
    _require_text(file_filter, field="file_filter", allow_empty=False)
    initial = resolve_initial_location(
        current=current,
        base_root=base_root,
        project_root=project_root,
        last_directory=last_directory,
    )
    selected, _ = QFileDialog.getOpenFileName(parent, title, str(initial), file_filter)
    if not selected:
        return PathSelection(value=_optional_path(current), cancelled=True)
    candidate = Path(selected)
    if not candidate.is_file():
        show_warning(parent, "Invalid file", "The selected file does not exist.")
        return PathSelection(value=_optional_path(current), cancelled=True)
    if validator is not None and not validator(candidate):
        show_warning(parent, "Invalid file", rejection_message)
        return PathSelection(value=_optional_path(current), cancelled=True)
    return PathSelection(value=candidate, cancelled=False)



def select_language_path(
    parent: QWidget | None,
    *,
    title: str = "Open GF language",
    current: PathLike | None = None,
    base_root: PathLike | None = None,
    last_directory: PathLike | None = None,
) -> PathSelection:
    """Collect one explicit language directory or GF source-file path.

    This adapter validates only the selected path kind. Language identity,
    source inventory, RGL-root discovery, module-role classification and GF-path
    resolution belong to the shared LanguageProbeService.
    """
    _require_text(title, field="title", allow_empty=False)

    prompt = QMessageBox(parent)
    prompt.setWindowTitle(title)
    prompt.setIcon(QMessageBox.Icon.Question)
    prompt.setText("Choose a GF language directory or a .gf source file.")
    prompt.setInformativeText(
        "Wordbench will validate the selected path and resolve the language context "
        "before opening the main window."
    )
    prompt.setTextFormat(Qt.TextFormat.PlainText)

    directory_button = prompt.addButton(
        "Choose Language Directory",
        QMessageBox.ButtonRole.ActionRole,
    )
    file_button = prompt.addButton(
        "Choose GF File",
        QMessageBox.ButtonRole.ActionRole,
    )
    cancel_button = prompt.addButton(QMessageBox.StandardButton.Cancel)

    directory_button.setAccessibleName("Choose language directory")
    file_button.setAccessibleName("Choose GF file")
    cancel_button.setAccessibleName("Cancel language selection")

    prompt.exec()
    clicked = prompt.clickedButton()

    if clicked is directory_button:
        result = select_existing_directory(
            parent,
            title="Choose GF language directory",
            current=current,
            base_root=base_root,
            last_directory=last_directory,
        )
    elif clicked is file_button:
        result = select_existing_file(
            parent,
            title="Choose GF source file",
            current=current,
            base_root=base_root,
            last_directory=last_directory,
            file_filter=_GF_SOURCE_FILTER,
            validator=_is_gf_source_file,
            rejection_message="Select a readable Grammatical Framework source file ending in .gf.",
        )
    else:
        return PathSelection(value=None, cancelled=True)

    if result.cancelled:
        return PathSelection(value=None, cancelled=True)
    return result


def resolve_initial_location(
    *,
    current: PathLike | None = None,
    base_root: PathLike | None = None,
    project_root: PathLike | None = None,
    last_directory: PathLike | None = None,
    home: PathLike | None = None,
) -> Path:
    root = _coalesce_base_root(base_root=base_root, project_root=project_root)
    candidates = (current, root, last_directory, home or Path.home())
    for raw in candidates:
        if raw is None:
            continue
        candidate = _coerce_path(raw)
        if candidate.is_file():
            candidate = candidate.parent
        if candidate.is_dir():
            return candidate
    return Path.home()


def _show_message(
    parent: QWidget | None,
    *,
    severity: DialogSeverity,
    title: str,
    message: str,
    informative_text: str = "",
    details: str = "",
) -> None:
    _require_text(title, field="title", allow_empty=False, maximum=512)
    _require_text(message, field="message", allow_empty=False, maximum=_MAX_SUMMARY_TEXT)
    _require_text(
        informative_text,
        field="informative_text",
        allow_empty=True,
        maximum=_MAX_SUMMARY_TEXT,
    )
    _require_text(details, field="details", allow_empty=True, maximum=_MAX_DIALOG_TEXT)

    icons = {
        DialogSeverity.INFORMATION: QMessageBox.Icon.Information,
        DialogSeverity.WARNING: QMessageBox.Icon.Warning,
        DialogSeverity.ERROR: QMessageBox.Icon.Critical,
        DialogSeverity.CRITICAL: QMessageBox.Icon.Critical,
    }
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setIcon(icons[severity])
    box.setText(message)
    box.setTextFormat(Qt.TextFormat.PlainText)
    if informative_text:
        box.setInformativeText(informative_text)
    if details:
        box.setDetailedText(details)
        copy_button = box.addButton("Copy Details", QMessageBox.ButtonRole.ActionRole)
        copy_button.clicked.connect(lambda: _copy_to_clipboard(details))
    box.addButton(QMessageBox.StandardButton.Ok)
    box.exec()


def _message_group(
    title: str,
    messages: Sequence[str],
    *,
    parent: QWidget,
) -> QGroupBox:
    group = QGroupBox(title, parent)
    group.setAccessibleName(title)
    layout = QVBoxLayout(group)
    text = QPlainTextEdit(group)
    text.setReadOnly(True)
    text.setPlainText("\n".join(f"• {message}" for message in messages))
    text.setMaximumBlockCount(max(1, len(messages) + 1))
    text.setMinimumHeight(min(180, 42 + 22 * len(messages)))
    text.setAccessibleName(title)
    layout.addWidget(text)
    return group


def _copy_to_clipboard(text: str) -> None:
    application = QApplication.instance()
    if application is None:
        return
    QApplication.clipboard().setText(text)



def _is_gf_source_file(path: Path) -> bool:
    return path.is_file() and path.suffix.casefold() == ".gf"


def _coalesce_base_root(
    *,
    base_root: PathLike | None,
    project_root: PathLike | None,
) -> Path | None:
    if base_root is None:
        return _optional_path(project_root)
    checked = _coerce_path(base_root, field="base_root")
    if project_root is not None:
        compatibility_root = _coerce_path(project_root, field="project_root")
        if checked != compatibility_root:
            raise ValueError("base_root and project_root must identify the same path")
    return checked


def _optional_path(value: PathLike | None) -> Path | None:
    return None if value is None else _coerce_path(value)


def _coerce_path(value: PathLike, *, field: str = "path") -> Path:
    if isinstance(value, Path):
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string or pathlib.Path")
    _require_text(value, field=field, allow_empty=False, maximum=32_768)
    return Path(value)


def _normalize_purpose(value: str) -> str:
    checked = _require_text(value, field="purpose", allow_empty=False, maximum=128)
    return checked.strip().lower().replace("-", "_")


def _require_text(
    value: object,
    *,
    field: str,
    allow_empty: bool,
    maximum: int = _MAX_DIALOG_TEXT,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field} must not be empty")
    if len(value) > maximum:
        raise ValueError(f"{field} exceeds the supported length")
    return value


def _validate_messages(values: Sequence[str], *, field: str) -> None:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(f"{field} must be a sequence of strings")
    if len(values) > _MAX_PLAN_ITEMS:
        raise ValueError(f"{field} contains too many items")
    for index, value in enumerate(values):
        _require_text(value, field=f"{field}[{index}]", allow_empty=False)


def _redaction_values(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError("sensitive_values must be an iterable of strings")
    result: list[str] = []
    for value in values:
        checked = _require_text(value, field="sensitive value", allow_empty=False)
        if checked not in result:
            result.append(checked)
    result.sort(key=len, reverse=True)
    return tuple(result)


def _sanitize_text(
    value: str,
    redactions: Sequence[str],
    *,
    maximum: int = _MAX_DIALOG_TEXT,
) -> str:
    text = value.replace("\x00", "\\x00")
    for secret in redactions:
        text = text.replace(secret, "[REDACTED]")
    if len(text) > maximum:
        text = f"{text[: maximum - 20]}\n… [truncated]"
    return text
