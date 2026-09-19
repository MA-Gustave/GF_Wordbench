"""Validation and safe display rendering for structured process requests."""

from __future__ import annotations

import codecs
from collections.abc import Collection, Iterable, Mapping, Sequence
from enum import Enum
import math
import os
from pathlib import Path
import re
import shlex
from typing import TYPE_CHECKING, Final

from gf_wordbench.kernel.errors import ContractViolationError, PathSecurityError

if TYPE_CHECKING:
    from gf_wordbench.infrastructure.process.models import (
        ArtifactExpectation,
        ProcessInput,
        ProcessRequest,
    )

__all__ = ["render_command_for_display", "validate_process_request"]

_NUL: Final = "\x00"
_IDENTIFIER_PATTERN: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_TOOL_ID_PATTERN: Final = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")
_ENVIRONMENT_KEY_PATTERN: Final = re.compile(r"^[^=\x00]+$")

_OPERATION_KINDS: Final = frozenset(
    {
        "version_probe",
        "compile",
        "pgf_build",
        "scenario",
        "generation",
        "introspection",
        "optional_tool",
    }
)
_ENVIRONMENT_POLICIES: Final = frozenset(
    {"controlled-inherit-v1", "clean-v1", "explicit-inherit-v1"}
)
_INPUT_KINDS: Final = frozenset({"none", "text", "file"})
_ARTIFACT_KINDS: Final = frozenset({"file", "directory"})
_MUTABILITY_CLASSES: Final = frozenset(
    {"read_only", "run_artifacts_only", "project_mutating", "external_mutating"}
)
_NETWORK_POLICIES: Final = frozenset({"denied", "loopback_only", "approved_endpoints"})
_PROHIBITED_EXECUTABLE_SUFFIXES: Final = frozenset({".bat", ".cmd"})


def validate_process_request(request: ProcessRequest) -> None:
    """Validate a complete process request before any capture file is opened."""

    request_id = _require_identifier(request.request_id, "request_id")
    _require_tool_id(request.tool_id)
    _require_identifier(request.operation_id, "operation_id")
    operation_kind = _enum_text(request.operation_kind, "operation_kind")
    if operation_kind not in _OPERATION_KINDS:
        raise ContractViolationError(
            f"Process request {request_id!r} has unknown operation kind {operation_kind!r}."
        )

    executable = _require_absolute_path(request.executable, "executable")
    cwd = _require_absolute_path(request.cwd, "cwd")
    stdout_path = _require_absolute_path(request.stdout_path, "stdout_path")
    stderr_path = _require_absolute_path(request.stderr_path, "stderr_path")

    read_roots = _validate_roots(request.approved_read_roots, "approved_read_roots")
    write_roots = _validate_roots(request.approved_write_roots, "approved_write_roots")

    _validate_executable(executable)
    _validate_working_directory(cwd, read_roots=read_roots, write_roots=write_roots)
    if not isinstance(request.args, tuple):
        raise ContractViolationError("args must be an ordered tuple of argument strings.")
    _validate_arguments(request.args)
    _validate_positive_finite(request.timeout_sec, "timeout_sec")
    _validate_non_negative_finite(request.termination_grace_sec, "termination_grace_sec")
    _validate_positive_integer(request.output_limit_bytes, "output_limit_bytes")
    # Validate input before touching or rejecting capture destinations so a bad
    # stdin contract is reported deterministically and cannot modify captures.
    _validate_input(request.stdin, read_roots=read_roots)
    _validate_capture_paths(
        stdout_path,
        stderr_path,
        write_roots=write_roots,
    )

    environment_policy = _enum_text(request.environment_policy, "environment_policy")
    if environment_policy not in _ENVIRONMENT_POLICIES:
        raise ContractViolationError(
            f"Process request {request_id!r} has unknown environment policy {environment_policy!r}."
        )

    _validate_environment(
        request.env_overrides,
        request.env_removals,
        request.sensitive_env_keys,
    )
    _validate_sensitive_argument_indexes(request.sensitive_arg_indexes, len(request.args))
    if not isinstance(request.expected_artifacts, tuple):
        raise ContractViolationError("expected_artifacts must be a tuple of expectations.")
    _validate_expected_artifacts(
        request.expected_artifacts,
        write_roots=write_roots,
        capture_paths=(stdout_path, stderr_path),
    )
    _validate_metadata(request.metadata)

    mutability_class = _enum_text(request.mutability_class, "mutability_class")
    if mutability_class not in _MUTABILITY_CLASSES:
        raise ContractViolationError(
            f"Process request {request_id!r} has unknown mutability class {mutability_class!r}."
        )

    network_policy = _enum_text(request.network_policy, "network_policy")
    if network_policy not in _NETWORK_POLICIES:
        raise ContractViolationError(
            f"Process request {request_id!r} has unknown network policy {network_policy!r}."
        )

    _require_nonempty_text(request.evidence_policy, "evidence_policy")


def render_command_for_display(
    executable: Path,
    args: Sequence[str],
    *,
    sensitive_arg_indexes: Collection[int] = (),
) -> str:
    """Render a non-executable, platform-appropriate command display string."""

    executable_path = _require_absolute_path(executable, "executable")
    _validate_arguments(args)
    indexes = _validated_sensitive_indexes(sensitive_arg_indexes, len(args))
    rendered_args = ["<redacted>" if index in indexes else arg for index, arg in enumerate(args)]
    command = [str(executable_path), *rendered_args]

    if os.name == "nt":
        return _windows_list2cmdline(command)
    return shlex.join(command)


def _windows_list2cmdline(arguments: list[str]) -> str:
    """Render arguments using the Microsoft C runtime command-line rules."""

    result: list[str] = []
    for index, argument in enumerate(arguments):
        if index:
            result.append(" ")
        needs_quotes = not argument or " " in argument or "\t" in argument
        if needs_quotes:
            result.append('"')

        backslashes: list[str] = []
        for character in argument:
            if character == "\\":
                backslashes.append(character)
                continue
            if character == '"':
                result.append("".join(backslashes * 2))
                backslashes.clear()
                result.append('\\"')
                continue
            if backslashes:
                result.extend(backslashes)
                backslashes.clear()
            result.append(character)

        if backslashes:
            result.append("".join(backslashes * (2 if needs_quotes else 1)))
        if needs_quotes:
            result.append('"')
    return "".join(result)


def _require_identifier(value: object, field: str) -> str:
    text = _require_nonempty_text(value, field)
    if _IDENTIFIER_PATTERN.fullmatch(text) is None:
        raise ContractViolationError(
            f"{field} must use 1-128 portable ASCII characters: letters, digits, '.', '_', or '-'."
        )
    return text


def _require_tool_id(value: object) -> str:
    text = _require_nonempty_text(value, "tool_id")
    if _TOOL_ID_PATTERN.fullmatch(text) is None:
        raise ContractViolationError(
            "tool_id must use 1-128 lowercase ASCII letters, digits, or hyphens."
        )
    return text


def _require_nonempty_text(value: object, field: str) -> str:
    text = _enum_text(value, field)
    if not text or text != text.strip():
        raise ContractViolationError(
            f"{field} must be non-empty and must not have outer whitespace."
        )
    if _contains_control(text):
        raise ContractViolationError(f"{field} must not contain NUL or control characters.")
    return text


def _enum_text(value: object, field: str) -> str:
    raw = value.value if isinstance(value, Enum) else value
    if not isinstance(raw, str):
        raise ContractViolationError(f"{field} must be a string or string-valued enum.")
    return raw


def _require_absolute_path(value: object, field: str) -> Path:
    if not isinstance(value, Path):
        raise ContractViolationError(f"{field} must be a pathlib.Path instance.")
    if _NUL in str(value):
        raise ContractViolationError(f"{field} must not contain a NUL character.")
    if not value.is_absolute():
        raise ContractViolationError(f"{field} must be an absolute path resolved before launch.")
    if ".." in value.parts:
        raise PathSecurityError(f"{field} must not contain parent traversal segments.")
    return value


def _validate_executable(executable: Path) -> None:
    suffix = executable.suffix.casefold()
    if suffix in _PROHIBITED_EXECUTABLE_SUFFIXES:
        raise ContractViolationError(
            f"Batch executable {executable.name!r} requires a separate reviewed launcher contract."
        )
    try:
        resolved = executable.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ContractViolationError(f"Executable does not resolve: {executable}") from exc
    if not resolved.is_file():
        raise ContractViolationError(f"Executable is not a regular file: {resolved}")
    if os.name != "nt" and not os.access(resolved, os.X_OK):
        raise ContractViolationError(f"Executable permission is missing: {resolved}")


def _validate_working_directory(
    cwd: Path,
    *,
    read_roots: tuple[Path, ...],
    write_roots: tuple[Path, ...],
) -> None:
    try:
        resolved = cwd.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ContractViolationError(f"Working directory does not resolve: {cwd}") from exc
    if not resolved.is_dir():
        raise ContractViolationError(f"Working directory is not a directory: {resolved}")
    _require_contained(resolved, (*read_roots, *write_roots), "working directory")


def _validate_arguments(args: Sequence[str]) -> None:
    if isinstance(args, (str, bytes)):
        raise ContractViolationError("args must be an ordered sequence of argument strings.")
    for index, argument in enumerate(args):
        if not isinstance(argument, str):
            raise ContractViolationError(f"args[{index}] must be a string.")
        if _NUL in argument:
            raise ContractViolationError(f"args[{index}] must not contain a NUL character.")


def _validate_capture_paths(
    stdout_path: Path,
    stderr_path: Path,
    *,
    write_roots: tuple[Path, ...],
) -> None:
    stdout_resolved = _resolve_for_containment(stdout_path)
    stderr_resolved = _resolve_for_containment(stderr_path)
    if _same_path(stdout_resolved, stderr_resolved):
        raise ContractViolationError("stdout_path and stderr_path must be distinct.")
    _require_contained(stdout_resolved, write_roots, "stdout capture path")
    _require_contained(stderr_resolved, write_roots, "stderr capture path")
    if stdout_path.exists():
        raise ContractViolationError(f"stdout_path already exists: {stdout_path}")
    if stderr_path.exists():
        raise ContractViolationError(f"stderr_path already exists: {stderr_path}")


def _validate_input(
    process_input: ProcessInput,
    *,
    read_roots: tuple[Path, ...],
) -> None:
    kind = _enum_text(process_input.kind, "stdin.kind")
    if kind not in _INPUT_KINDS:
        raise ContractViolationError(f"Unknown stdin kind: {kind!r}.")

    encoding = _require_nonempty_text(process_input.encoding, "stdin.encoding")
    try:
        codecs.lookup(encoding)
    except LookupError as exc:
        raise ContractViolationError(f"Unknown stdin encoding: {encoding!r}.") from exc

    text = process_input.text
    path = process_input.path

    if kind == "none":
        if text is not None or path is not None:
            raise ContractViolationError("stdin kind 'none' cannot contain text or a file path.")
        return

    if kind == "text":
        if not isinstance(text, str) or path is not None:
            raise ContractViolationError(
                "stdin kind 'text' requires Unicode text and forbids a file path."
            )
        try:
            text.encode(encoding)
        except UnicodeError as exc:
            raise ContractViolationError(
                f"stdin text cannot be encoded using {encoding!r}."
            ) from exc
        return

    if text is not None:
        raise ContractViolationError("stdin kind 'file' forbids inline text.")
    input_path = _require_absolute_path(path, "stdin.path")
    try:
        resolved = input_path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ContractViolationError(f"stdin file does not resolve: {input_path}") from exc
    if not resolved.is_file():
        raise ContractViolationError(f"stdin path is not a regular file: {resolved}")
    _require_contained(resolved, read_roots, "stdin file")


def _validate_environment(
    overrides: Mapping[str, str],
    removals: Collection[str],
    sensitive_keys: Collection[str],
) -> None:
    if not isinstance(overrides, Mapping):
        raise ContractViolationError("env_overrides must be a mapping of strings to strings.")

    normalized_override_keys: dict[str, str] = {}
    for key, value in overrides.items():
        _validate_environment_key(key, "env_overrides key")
        if not isinstance(value, str):
            raise ContractViolationError(f"Environment value for {key!r} must be a string.")
        if _NUL in value:
            raise ContractViolationError(f"Environment value for {key!r} contains a NUL character.")
        normalized = os.path.normcase(key)
        previous = normalized_override_keys.setdefault(normalized, key)
        if previous != key:
            raise ContractViolationError(
                f"Environment keys {previous!r} and {key!r} collide on this platform."
            )

    removal_keys = _validate_environment_key_collection(removals, "env_removals")
    _validate_environment_key_collection(sensitive_keys, "sensitive_env_keys")
    normalized_overrides = set(normalized_override_keys)
    normalized_removals = {os.path.normcase(key) for key in removal_keys}
    if normalized_overrides & normalized_removals:
        raise ContractViolationError(
            "An environment key cannot be both overridden and removed in one request."
        )


def _validate_environment_key_collection(values: Collection[str], field: str) -> set[str]:
    if isinstance(values, (str, bytes)):
        raise ContractViolationError(f"{field} must be a collection of environment keys.")
    result: set[str] = set()
    normalized: dict[str, str] = {}
    for value in values:
        _validate_environment_key(value, field)
        folded = os.path.normcase(value)
        previous = normalized.setdefault(folded, value)
        if previous != value:
            raise ContractViolationError(
                f"Environment keys {previous!r} and {value!r} collide on this platform."
            )
        result.add(value)
    return result


def _validate_environment_key(value: object, field: str) -> None:
    if (
        not isinstance(value, str)
        or _ENVIRONMENT_KEY_PATTERN.fullmatch(value) is None
        or _contains_control(value)
    ):
        raise ContractViolationError(
            f"{field} must be a non-empty string without '=', NUL, or control characters."
        )


def _validate_sensitive_argument_indexes(indexes: Collection[int], argument_count: int) -> None:
    _validated_sensitive_indexes(indexes, argument_count)


def _validated_sensitive_indexes(indexes: Collection[int], argument_count: int) -> frozenset[int]:
    if isinstance(indexes, (str, bytes)):
        raise ContractViolationError("sensitive_arg_indexes must be a collection of integers.")
    validated: set[int] = set()
    for index in indexes:
        if isinstance(index, bool) or not isinstance(index, int):
            raise ContractViolationError("Sensitive argument indexes must be integers.")
        if index < 0 or index >= argument_count:
            raise ContractViolationError(
                f"Sensitive argument index {index} is outside the argument vector."
            )
        validated.add(index)
    return frozenset(validated)


def _validate_expected_artifacts(
    expectations: Iterable[ArtifactExpectation],
    *,
    write_roots: tuple[Path, ...],
    capture_paths: tuple[Path, Path],
) -> None:
    if isinstance(expectations, (str, bytes)):
        raise ContractViolationError("expected_artifacts must be an iterable of expectations.")

    seen_paths: list[Path] = []
    resolved_captures = tuple(_resolve_for_containment(path) for path in capture_paths)
    for index, expectation in enumerate(expectations):
        # Scalar contract errors outrank path containment errors; this makes
        # diagnostics stable when more than one field is malformed.
        role = _require_nonempty_text(expectation.role, f"expected_artifacts[{index}].role")
        kind = _enum_text(expectation.kind, f"expected_artifacts[{index}].kind")
        if kind not in _ARTIFACT_KINDS:
            raise ContractViolationError(f"Expected artifact {role!r} has unknown kind {kind!r}.")
        if not isinstance(expectation.required, bool):
            raise ContractViolationError(f"expected_artifacts[{index}].required must be a boolean.")
        _validate_non_negative_integer(
            expectation.minimum_size_bytes,
            f"expected_artifacts[{index}].minimum_size_bytes",
        )
        path = _require_absolute_path(
            expectation.path,
            f"expected_artifacts[{index}].path",
        )

        resolved = _resolve_for_containment(path)
        _require_contained(resolved, write_roots, f"expected artifact {role!r}")
        if path.suffix.casefold() == ".gold":
            raise PathSecurityError("Normal process execution cannot write a .gold file.")
        if any(_same_path(resolved, capture) for capture in resolved_captures):
            raise ContractViolationError(
                f"Expected artifact {path} cannot reuse a raw capture path."
            )
        if any(_same_path(resolved, previous) for previous in seen_paths):
            raise ContractViolationError(
                f"Expected artifact path is declared more than once: {path}"
            )
        seen_paths.append(resolved)


def _validate_metadata(metadata: Mapping[str, str]) -> None:
    if not isinstance(metadata, Mapping):
        raise ContractViolationError("metadata must be a mapping of strings to strings.")
    for key, value in metadata.items():
        _require_nonempty_text(key, "metadata key")
        if not isinstance(value, str):
            raise ContractViolationError(f"Metadata value for {key!r} must be a string.")
        if _NUL in value:
            raise ContractViolationError(f"Metadata value for {key!r} contains a NUL character.")


def _validate_roots(values: Iterable[Path], field: str) -> tuple[Path, ...]:
    if isinstance(values, (str, bytes, Path)):
        raise ContractViolationError(f"{field} must be an iterable of directory paths.")

    resolved_roots: list[Path] = []
    for index, value in enumerate(values):
        path = _require_absolute_path(value, f"{field}[{index}]")
        try:
            resolved = path.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise PathSecurityError(f"Approved root does not resolve: {path}") from exc
        if not resolved.is_dir():
            raise PathSecurityError(f"Approved root is not a directory: {resolved}")
        if not any(_same_path(resolved, existing) for existing in resolved_roots):
            resolved_roots.append(resolved)

    if not resolved_roots:
        raise ContractViolationError(f"{field} must contain at least one approved root.")
    return tuple(resolved_roots)


def _require_contained(path: Path, roots: tuple[Path, ...], label: str) -> None:
    if any(_is_relative_to(path, root) for root in roots):
        return
    rendered_roots = ", ".join(str(root) for root in roots)
    raise PathSecurityError(
        f"{label.capitalize()} escapes approved roots: {path}; roots: {rendered_roots}"
    )


def _resolve_for_containment(path: Path) -> Path:
    missing_parts: list[str] = []
    cursor = path
    while not cursor.exists():
        if cursor.is_symlink():
            raise PathSecurityError(f"Path contains an unresolved symbolic link: {path}")
        parent = cursor.parent
        if parent == cursor:
            raise PathSecurityError(f"Path has no existing ancestor: {path}")
        missing_parts.append(cursor.name)
        cursor = parent
    try:
        resolved = cursor.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise PathSecurityError(f"Path cannot be resolved safely: {path}") from exc
    for part in reversed(missing_parts):
        resolved /= part
    return resolved


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(os.path.normpath(str(left))) == os.path.normcase(
        os.path.normpath(str(right))
    )


def _validate_positive_finite(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractViolationError(f"{field} must be a finite number greater than zero.")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ContractViolationError(f"{field} must be a finite number greater than zero.")


def _validate_non_negative_finite(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractViolationError(f"{field} must be a finite non-negative number.")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ContractViolationError(f"{field} must be a finite non-negative number.")


def _validate_positive_integer(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ContractViolationError(f"{field} must be a positive integer.")


def _validate_non_negative_integer(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContractViolationError(f"{field} must be a non-negative integer.")


def _contains_control(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)
