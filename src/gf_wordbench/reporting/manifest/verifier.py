"""Verification of finalized GF Wordbench artifact manifests."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Final

from gf_wordbench.kernel.statuses import ValidationStatus

from .models import ManifestVerificationPolicy, ManifestVerificationResult

__all__ = ("verify_manifest",)

_SCHEMA_ID: Final = "gf-wordbench.artifact-manifest"
_SUPPORTED_SCHEMA_MAJOR: Final = 1
_HASH_ALGORITHM: Final = "sha256"
_MANIFEST_NAME: Final = "manifest.json"
_VERSION_PATTERN: Final = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_URI_PATTERN: Final = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
_SHA256_PATTERN: Final = re.compile(r"^[0-9A-Fa-f]{64}$")

_ROLES: Final = frozenset(
    {
        "machine_summary",
        "human_summary",
        "ai_handoff",
        "top_errors",
        "master_log",
        "aggregate_log",
        "scan_log",
        "compile_stdout",
        "compile_stderr",
        "scenario_stdout",
        "scenario_stderr",
        "scenario_output",
        "detail",
        "gfo",
        "pgf",
        "other",
    }
)
_FRAMEWORK_REQUIRED: Final = (
    "summary.json",
    "summary.md",
    "AI_READY.md",
    "top_errors.txt",
    "raw/master.log",
)
_TEXT_FINAL_NEWLINE_ROLES: Final = frozenset(
    {"machine_summary", "human_summary", "ai_handoff", "top_errors"}
)
_MEDIA_TYPES_BY_ROLE: Final[Mapping[str, frozenset[str]]] = {
    "machine_summary": frozenset({"application/json"}),
    "human_summary": frozenset({"text/markdown; charset=utf-8"}),
    "ai_handoff": frozenset({"text/markdown; charset=utf-8"}),
    "top_errors": frozenset({"text/plain; charset=utf-8"}),
    "master_log": frozenset({"text/plain; charset=utf-8"}),
    "aggregate_log": frozenset({"text/plain; charset=utf-8"}),
    "scan_log": frozenset({"text/plain; charset=utf-8"}),
    "compile_stdout": frozenset({"text/plain; charset=utf-8"}),
    "compile_stderr": frozenset({"text/plain; charset=utf-8"}),
    "scenario_stdout": frozenset({"text/plain; charset=utf-8"}),
    "scenario_stderr": frozenset({"text/plain; charset=utf-8"}),
    "scenario_output": frozenset({"text/plain; charset=utf-8"}),
    "gfo": frozenset({"application/octet-stream"}),
    "pgf": frozenset({"application/octet-stream"}),
}


class _Verification:
    __slots__ = (
        "manifest_path",
        "run_root",
        "policy",
        "schema_version",
        "checked",
        "required_checked",
        "missing",
        "mismatched",
        "unsafe",
        "warnings",
        "failures",
        "errors",
        "entries",
    )

    def __init__(
        self,
        manifest_path: Path,
        run_root: Path,
        policy: ManifestVerificationPolicy,
    ) -> None:
        self.manifest_path = manifest_path
        self.run_root = run_root
        self.policy = policy
        self.schema_version: str | None = None
        self.checked = 0
        self.required_checked = 0
        self.missing: list[str] = []
        self.mismatched: list[str] = []
        self.unsafe: list[str] = []
        self.warnings: list[str] = []
        self.failures: list[str] = []
        self.errors: list[str] = []
        self.entries: list[dict[str, Any]] = []

    @property
    def mode(self) -> str:
        value = _policy_value(self.policy, "mode", "verification_mode", default="standard")
        if hasattr(value, "value"):
            value = value.value
        return str(value).strip().lower()

    @property
    def strict(self) -> bool:
        return self.mode in {"strict", "release"}

    @property
    def release(self) -> bool:
        return self.mode == "release"

    def error(self, code: str, message: str, *, unsafe_path: str | None = None) -> None:
        self.errors.append(f"{code}: {message}")
        if unsafe_path is not None:
            self.unsafe.append(unsafe_path)

    def fail(self, code: str, message: str, *, path: str | None = None) -> None:
        self.failures.append(f"{code}: {message}")
        if path is not None:
            self.mismatched.append(path)

    def warn(self, code: str, message: str) -> None:
        self.warnings.append(f"{code}: {message}")


def verify_manifest(
    manifest_path: Path,
    run_root: Path,
    policy: ManifestVerificationPolicy,
) -> ManifestVerificationResult:
    """Verify one manifest without modifying it or any listed artifact."""

    if not isinstance(manifest_path, Path):
        manifest_path = Path(manifest_path)
    if not isinstance(run_root, Path):
        run_root = Path(run_root)

    state = _Verification(manifest_path, run_root, policy)
    try:
        _verify(state)
    except Exception as exc:  # defensive containment at the reporting boundary
        state.error("MANIFEST_UNREADABLE", f"unexpected verification error: {exc}")
    return _build_result(state)


def _verify(state: _Verification) -> None:
    try:
        root = state.run_root.resolve(strict=True)
    except OSError as exc:
        state.error("MANIFEST_UNREADABLE", f"run root is unavailable: {exc}")
        return
    if not root.is_dir():
        state.error("MANIFEST_UNREADABLE", "run root is not a directory")
        return
    state.run_root = root

    try:
        manifest = state.manifest_path.resolve(strict=False)
        manifest.relative_to(root)
    except (OSError, ValueError):
        state.error(
            "MANIFEST_ARTIFACT_PATH_TRAVERSAL",
            "manifest path is not contained by the run root",
            unsafe_path=str(state.manifest_path),
        )
        return
    state.manifest_path = manifest

    if state.strict and manifest.name != _MANIFEST_NAME:
        state.error("MANIFEST_ARTIFACT_PATH_SELF", "manifest filename is not canonical")
        return
    if not manifest.exists():
        state.error("MANIFEST_MISSING", "manifest file does not exist")
        return
    if not manifest.is_file():
        state.error("MANIFEST_UNREADABLE", "manifest path is not a regular file")
        return

    try:
        raw = manifest.read_bytes()
    except OSError as exc:
        state.error("MANIFEST_UNREADABLE", f"manifest cannot be read: {exc}")
        return
    if raw.startswith(b"\xef\xbb\xbf"):
        state.error("MANIFEST_JSON_INVALID", "UTF-8 BOM is prohibited")
        return
    if state.strict and not raw.endswith(b"\n"):
        state.error("MANIFEST_JSON_INVALID", "canonical manifest lacks final LF")
        return
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        state.error("MANIFEST_JSON_INVALID", f"manifest is not valid UTF-8: {exc}")
        return
    try:
        document = json.loads(text, parse_constant=_reject_json_constant)
    except (ValueError, json.JSONDecodeError) as exc:
        state.error("MANIFEST_JSON_INVALID", f"invalid JSON: {exc}")
        return
    if not isinstance(document, dict):
        state.error("MANIFEST_JSON_INVALID", "manifest root must be an object")
        return

    if not _verify_root(state, document):
        return
    _verify_entries(state, document["artifacts"])
    if state.errors:
        return
    _verify_required_declarations(state)
    if state.strict:
        _verify_unlisted_files(state)
    if state.release or _policy_bool(state.policy, "verify_summary", default=False):
        _verify_summary_consistency(state, document)


def _verify_root(state: _Verification, document: Mapping[str, Any]) -> bool:
    if document.get("schema_id") != _SCHEMA_ID:
        state.error("MANIFEST_SCHEMA_ID_INVALID", "schema_id is not canonical")

    version = document.get("schema_version")
    if not isinstance(version, str) or not _VERSION_PATTERN.fullmatch(version):
        state.error("MANIFEST_SCHEMA_VERSION_UNSUPPORTED", "schema_version is invalid")
    else:
        state.schema_version = version
        if int(version.split(".", 1)[0]) != _SUPPORTED_SCHEMA_MAJOR:
            state.error("MANIFEST_SCHEMA_VERSION_UNSUPPORTED", f"unsupported schema {version}")

    producer = document.get("producer")
    if not isinstance(producer, dict) or not _nonempty(producer.get("name")) or not _nonempty(
        producer.get("version")
    ):
        state.error("MANIFEST_ARTIFACT_ENTRY_INVALID", "producer is invalid")

    run_id = document.get("run_id")
    if not _nonempty(run_id):
        state.error("MANIFEST_RUN_ID_MISMATCH", "run_id is missing or invalid")
    else:
        expected = _expected_run_id(state)
        if expected is not None and run_id != expected:
            state.error(
                "MANIFEST_RUN_ID_MISMATCH",
                f"manifest run_id {run_id!r} does not match {expected!r}",
            )

    if not _nonempty(document.get("generated_at")):
        state.error("MANIFEST_ARTIFACT_ENTRY_INVALID", "generated_at is missing")
    if document.get("hash_algorithm") != _HASH_ALGORITHM:
        state.error("MANIFEST_HASH_ALGORITHM_INVALID", "hash_algorithm must be sha256")
    if not isinstance(document.get("artifacts"), list):
        state.error("MANIFEST_ARTIFACT_ENTRY_INVALID", "artifacts must be an array")
    return not state.errors


def _verify_entries(state: _Verification, entries: list[Any]) -> None:
    seen: set[str] = set()
    normalized_order: list[str] = []

    for index, raw_entry in enumerate(entries):
        if not isinstance(raw_entry, dict):
            state.error("MANIFEST_ARTIFACT_ENTRY_INVALID", f"artifact {index} is not an object")
            continue
        entry = dict(raw_entry)
        state.entries.append(entry)
        path_value = entry.get("path")
        normalized = _normalize_manifest_path(path_value)
        if normalized is None:
            code = _path_failure_code(path_value)
            display = "" if path_value is None else str(path_value)
            state.error(code, f"artifact {index} has unsafe path {display!r}", unsafe_path=display)
            continue
        if normalized == _MANIFEST_NAME:
            state.error(
                "MANIFEST_ARTIFACT_PATH_SELF",
                "manifest must not contain itself",
                unsafe_path=normalized,
            )
            continue
        comparison_key = normalized.casefold() if os.name == "nt" else normalized
        if comparison_key in seen:
            state.error(
                "MANIFEST_ARTIFACT_PATH_DUPLICATE",
                f"duplicate artifact path {normalized!r}",
                unsafe_path=normalized,
            )
            continue
        seen.add(comparison_key)
        normalized_order.append(normalized)
        if state.strict and path_value != normalized:
            state.error(
                "MANIFEST_ARTIFACT_ENTRY_INVALID",
                f"artifact path is not canonical: {path_value!r}",
                unsafe_path=str(path_value),
            )
            continue

        required = entry.get("required")
        size_bytes = entry.get("size_bytes")
        role = entry.get("role")
        media_type = entry.get("media_type")
        digest = entry.get("sha256")
        created_by = entry.get("created_by")
        if type(required) is not bool or type(size_bytes) is not int or size_bytes < 0:
            state.error("MANIFEST_ARTIFACT_ENTRY_INVALID", f"invalid fields for {normalized}")
            continue
        if not _nonempty(role) or not _nonempty(media_type) or not _nonempty(created_by):
            state.error("MANIFEST_ARTIFACT_ENTRY_INVALID", f"invalid metadata for {normalized}")
            continue
        if not isinstance(digest, str) or not _SHA256_PATTERN.fullmatch(digest):
            state.error("MANIFEST_ARTIFACT_ENTRY_INVALID", f"invalid sha256 for {normalized}")
            continue

        if state.strict:
            _verify_strict_metadata(state, normalized, role, media_type, created_by)
        _verify_file(state, normalized, required, size_bytes, digest, role, media_type)

    if state.strict and normalized_order != sorted(normalized_order):
        state.error("MANIFEST_ARTIFACT_ENTRY_INVALID", "artifact entries are not canonically sorted")


def _verify_strict_metadata(
    state: _Verification,
    path: str,
    role: str,
    media_type: str,
    created_by: str,
) -> None:
    allowed_roles = set(_policy_iterable(state.policy, "allowed_roles", default=_ROLES))
    if role not in allowed_roles:
        state.error("MANIFEST_ROLE_UNKNOWN", f"unknown role {role!r} for {path}")
    expected_media = _MEDIA_TYPES_BY_ROLE.get(role)
    if expected_media is not None and media_type not in expected_media:
        state.error(
            "MANIFEST_MEDIA_TYPE_INVALID",
            f"media type {media_type!r} is incompatible with role {role!r}",
        )
    creators = set(_policy_iterable(state.policy, "allowed_creators", "known_creators", default=()))
    if creators and created_by not in creators:
        state.error("MANIFEST_CREATED_BY_UNKNOWN", f"unknown creator {created_by!r} for {path}")


def _verify_file(
    state: _Verification,
    relative_path: str,
    required: bool,
    expected_size: int,
    expected_hash: str,
    role: str,
    media_type: str,
) -> None:
    candidate = state.run_root.joinpath(*PurePosixPath(relative_path).parts)
    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(state.run_root)
    except (OSError, ValueError):
        state.error(
            "MANIFEST_ARTIFACT_PATH_TRAVERSAL",
            f"artifact escapes run root: {relative_path}",
            unsafe_path=relative_path,
        )
        return

    if not candidate.exists():
        state.missing.append(relative_path)
        if required:
            state.fail("MANIFEST_ARTIFACT_MISSING", f"required artifact is missing: {relative_path}")
        else:
            state.warn("MANIFEST_ARTIFACT_MISSING", f"optional artifact is missing: {relative_path}")
        return

    try:
        lstat = candidate.lstat()
    except OSError as exc:
        state.error("MANIFEST_UNREADABLE", f"cannot inspect {relative_path}: {exc}")
        return
    if stat.S_ISLNK(lstat.st_mode):
        allow_symlinks = _policy_bool(state.policy, "allow_symlinks", default=not state.strict)
        if not allow_symlinks or state.release:
            state.error("MANIFEST_ARTIFACT_SYMLINK", f"symlink artifact is prohibited: {relative_path}")
            return
    if not candidate.is_file():
        state.error("MANIFEST_ARTIFACT_NOT_FILE", f"artifact is not a regular file: {relative_path}")
        return

    try:
        before = candidate.stat()
        actual_hash = _sha256(candidate)
        after = candidate.stat()
    except OSError as exc:
        state.error("MANIFEST_UNREADABLE", f"cannot verify {relative_path}: {exc}")
        return
    if _stat_identity(before) != _stat_identity(after):
        state.error(
            "MANIFEST_ARTIFACT_MUTATED_DURING_HASH",
            f"artifact changed during hashing: {relative_path}",
        )
        return

    state.checked += 1
    if required:
        state.required_checked += 1
    if after.st_size != expected_size:
        state.fail(
            "MANIFEST_ARTIFACT_SIZE_MISMATCH",
            f"size mismatch for {relative_path}: expected {expected_size}, got {after.st_size}",
            path=relative_path,
        )
    if actual_hash != expected_hash.lower():
        state.fail(
            "MANIFEST_ARTIFACT_HASH_MISMATCH",
            f"SHA-256 mismatch for {relative_path}",
            path=relative_path,
        )
    if state.strict and role in _TEXT_FINAL_NEWLINE_ROLES:
        _verify_canonical_text(state, candidate, relative_path, media_type)


def _verify_required_declarations(state: _Verification) -> None:
    entries_by_path = {
        _normalize_manifest_path(entry.get("path")): entry
        for entry in state.entries
        if _normalize_manifest_path(entry.get("path")) is not None
    }
    required = set(_policy_iterable(state.policy, "required_paths", default=()))
    if state.release:
        required.update(_FRAMEWORK_REQUIRED)
    for path in sorted(required):
        normalized = _normalize_manifest_path(path)
        entry = entries_by_path.get(normalized)
        if entry is None or entry.get("required") is not True:
            state.fail(
                "MANIFEST_REQUIRED_ARTIFACT_UNDECLARED",
                f"required artifact is not declared required: {path}",
                path=str(path),
            )
    if state.release and _policy_bool(state.policy, "require_pgf", "release_requires_pgf", default=False):
        pgf_entries = [entry for entry in state.entries if entry.get("role") == "pgf" and entry.get("required")]
        if not pgf_entries:
            state.fail("MANIFEST_REQUIRED_ARTIFACT_UNDECLARED", "release requires a PGF artifact")


def _verify_unlisted_files(state: _Verification) -> None:
    if not _policy_bool(
        state.policy,
        "detect_unlisted_files",
        "reject_unlisted_files",
        default=False,
    ):
        return
    owned = tuple(_policy_iterable(state.policy, "owned_directories", default=()))
    if not owned:
        return
    listed = {
        _normalize_manifest_path(entry.get("path"))
        for entry in state.entries
        if _normalize_manifest_path(entry.get("path")) is not None
    }
    for directory in owned:
        normalized = _normalize_manifest_path(directory)
        if normalized is None:
            state.error("MANIFEST_ARTIFACT_PATH_TRAVERSAL", f"unsafe owned directory: {directory}")
            continue
        base = state.run_root.joinpath(*PurePosixPath(normalized).parts)
        if not base.exists():
            continue
        for file_path in sorted(path for path in base.rglob("*") if path.is_file()):
            relative = file_path.relative_to(state.run_root).as_posix()
            if relative not in listed and relative != _MANIFEST_NAME:
                if state.release or _policy_bool(state.policy, "reject_unlisted_files", default=False):
                    state.error("MANIFEST_REQUIRED_ARTIFACT_UNDECLARED", f"unlisted finalized file: {relative}")
                else:
                    state.warn("MANIFEST_REQUIRED_ARTIFACT_UNDECLARED", f"unlisted finalized file: {relative}")


def _verify_summary_consistency(state: _Verification, manifest: Mapping[str, Any]) -> None:
    summary_entry = next(
        (
            entry
            for entry in state.entries
            if entry.get("role") == "machine_summary" or entry.get("path") == "summary.json"
        ),
        None,
    )
    if summary_entry is None:
        state.fail("MANIFEST_SUMMARY_INCONSISTENT", "machine summary is not declared")
        return
    summary_path = _normalize_manifest_path(summary_entry.get("path"))
    if summary_path is None:
        return
    path = state.run_root.joinpath(*PurePosixPath(summary_path).parts)
    try:
        summary = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_json_constant)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        state.error("MANIFEST_SUMMARY_INCONSISTENT", f"summary cannot be read reliably: {exc}")
        return
    if not isinstance(summary, dict):
        state.error("MANIFEST_SUMMARY_INCONSISTENT", "summary root is not an object")
        return

    summary_run_id = _nested_value(summary, ("metadata", "run_id"), ("run_id",))
    if summary_run_id != manifest.get("run_id"):
        state.fail("MANIFEST_SUMMARY_INCONSISTENT", "summary and manifest run_id differ")
    metadata = summary.get("metadata") if isinstance(summary.get("metadata"), dict) else summary
    if state.release:
        if not _nonempty(metadata.get("project_id")) or not _nonempty(metadata.get("project_name")):
            state.fail("MANIFEST_SUMMARY_INCONSISTENT", "summary lacks active project identity")

    artifact_map = summary.get("artifacts")
    if isinstance(artifact_map, dict):
        manifest_ref = artifact_map.get("manifest")
        if manifest_ref is not None and manifest_ref != _MANIFEST_NAME:
            state.fail("MANIFEST_SUMMARY_INCONSISTENT", "summary manifest path is not manifest.json")
        listed = {
            _normalize_manifest_path(entry.get("path"))
            for entry in state.entries
            if _normalize_manifest_path(entry.get("path")) is not None
        }
        for declared in _artifact_paths(artifact_map):
            normalized = _normalize_manifest_path(declared)
            if normalized in {None, _MANIFEST_NAME}:
                continue
            candidate = state.run_root.joinpath(*PurePosixPath(normalized).parts)
            if candidate.is_file() and normalized not in listed:
                state.fail(
                    "MANIFEST_SUMMARY_INCONSISTENT",
                    f"summary-declared artifact is absent from manifest: {normalized}",
                    path=normalized,
                )


def _verify_canonical_text(
    state: _Verification,
    path: Path,
    relative_path: str,
    media_type: str,
) -> None:
    try:
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raise UnicodeError("UTF-8 BOM is prohibited")
        raw.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        state.error("MANIFEST_MEDIA_TYPE_INVALID", f"invalid UTF-8 text {relative_path}: {exc}")
        return
    if media_type.startswith(("text/", "application/json")) and not raw.endswith(b"\n"):
        state.error("MANIFEST_MEDIA_TYPE_INVALID", f"canonical text lacks final LF: {relative_path}")


def _build_result(state: _Verification) -> ManifestVerificationResult:
    if state.errors:
        status = ValidationStatus.ERROR
        message = state.errors[0]
    elif state.failures:
        status = ValidationStatus.FAIL
        message = state.failures[0]
    else:
        status = ValidationStatus.OK
        message = f"verified {state.checked} artifact(s)"
    warnings = tuple(dict.fromkeys((*state.warnings, *state.failures[1:], *state.errors[1:])))
    return ManifestVerificationResult(
        status=status,
        manifest_path=state.manifest_path,
        schema_version=state.schema_version,
        artifacts_checked=state.checked,
        required_artifacts_checked=state.required_checked,
        missing_paths=tuple(dict.fromkeys(state.missing)),
        mismatched_paths=tuple(dict.fromkeys(state.mismatched)),
        unsafe_paths=tuple(dict.fromkeys(state.unsafe)),
        warnings=warnings,
        message=message,
    )


def _normalize_manifest_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\x00" in value:
        return None
    if _URI_PATTERN.match(value) or PureWindowsPath(value).drive or value.startswith(("/", "\\")):
        return None
    converted = value.replace("\\", "/")
    parts: list[str] = []
    for part in PurePosixPath(converted).parts:
        if part in {"", "."}:
            continue
        if part == "..":
            return None
        parts.append(part)
    return "/".join(parts) or None


def _path_failure_code(value: object) -> str:
    if not isinstance(value, str) or not value:
        return "MANIFEST_ARTIFACT_PATH_EMPTY"
    if _URI_PATTERN.match(value) or PureWindowsPath(value).drive or value.startswith(("/", "\\")):
        return "MANIFEST_ARTIFACT_PATH_ABSOLUTE"
    return "MANIFEST_ARTIFACT_PATH_TRAVERSAL"


def _expected_run_id(state: _Verification) -> str | None:
    configured = _policy_value(state.policy, "expected_run_id", "run_id", default=None)
    if configured is not None:
        return str(configured)
    name = state.run_root.name
    return name[4:] if name.startswith("run_") and len(name) > 4 else None


def _policy_value(policy: object, *names: str, default: Any) -> Any:
    for name in names:
        if hasattr(policy, name):
            return getattr(policy, name)
    return default


def _policy_bool(policy: object, *names: str, default: bool) -> bool:
    return bool(_policy_value(policy, *names, default=default))


def _policy_iterable(policy: object, *names: str, default: Iterable[str]) -> tuple[str, ...]:
    value = _policy_value(policy, *names, default=default)
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_size,
        value.st_mtime_ns,
        getattr(value, "st_ctime_ns", 0),
        getattr(value, "st_dev", 0),
        getattr(value, "st_ino", 0),
    )


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\x00" not in value


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is prohibited: {value}")


def _nested_value(document: Mapping[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        value: Any = document
        for key in path:
            if not isinstance(value, Mapping) or key not in value:
                break
            value = value[key]
        else:
            return value
    return None


def _artifact_paths(value: object) -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, Mapping):
        for item in value.values():
            found.extend(_artifact_paths(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_artifact_paths(item))
    return tuple(found)
