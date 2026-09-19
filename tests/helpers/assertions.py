from __future__ import annotations

from collections.abc import Iterable, Mapping
import errno
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import time
from typing import Protocol, TypeAlias, cast

PathLike: TypeAlias = str | os.PathLike[str]
JsonObject: TypeAlias = Mapping[str, object]


class _Pollable(Protocol):
    def poll(self) -> int | None: ...


class _AliveCheck(Protocol):
    def is_alive(self) -> bool: ...


__all__ = (
    "assert_gold_unchanged",
    "assert_manifest_complete",
    "assert_no_process_leaks",
    "assert_path_contained",
    "assert_valid_summary",
)


def assert_valid_summary(
    summary: object | Path,
    *,
    strict: bool = True,
    check_ordering: bool = True,
) -> JsonObject:
    if type(strict) is not bool:
        raise TypeError("strict must be a boolean")
    if type(check_ordering) is not bool:
        raise TypeError("check_ordering must be a boolean")

    document = _json_object(summary, role="summary")
    try:
        from gf_wordbench.reporting.schemas.summary_v1 import (
            assert_summary_v1_json_safe,
            validate_summary_v1,
        )

        issues = validate_summary_v1(
            document,
            strict=strict,
            check_ordering=check_ordering,
        )
        assert_summary_v1_json_safe(document)
    except AssertionError:
        raise
    except Exception as exc:
        raise AssertionError(f"summary validation could not run: {exc}") from exc

    if issues:
        rendered = "\n".join(
            f"  - {issue.path} [{issue.code}]: {issue.message}" for issue in issues
        )
        raise AssertionError(
            f"summary violates the canonical schema ({len(issues)} issue(s)):\n{rendered}"
        )
    return document


def assert_manifest_complete(
    manifest: object | Path,
    *,
    expected_paths: Iterable[str | PurePosixPath] = (),
    required_paths: Iterable[str | PurePosixPath] = (),
    run_root: PathLike | None = None,
    verify_hashes: bool = True,
) -> object:
    if type(verify_hashes) is not bool:
        raise TypeError("verify_hashes must be a boolean")

    document = _json_object(manifest, role="manifest")
    try:
        from gf_wordbench.reporting.schemas.manifest_v1 import (
            parse_artifact_manifest,
            serialize_artifact_manifest,
        )

        model = parse_artifact_manifest(document, strict=True)
        canonical = serialize_artifact_manifest(model)
    except AssertionError:
        raise
    except Exception as exc:
        raise AssertionError(f"manifest violates the canonical schema: {exc}") from exc

    if dict(document) != dict(canonical):
        raise AssertionError(
            "manifest is structurally valid but is not in canonical serialized form"
        )

    expected = _normalized_manifest_paths(expected_paths, role="expected_paths")
    required = _normalized_manifest_paths(required_paths, role="required_paths")
    entries = {entry.path: entry for entry in model.artifacts}

    missing_expected = tuple(path for path in expected if path not in entries)
    if missing_expected:
        raise AssertionError(
            "manifest is missing expected artifact entries:\n" + _render_lines(missing_expected)
        )

    missing_required = tuple(path for path in required if path not in entries)
    if missing_required:
        raise AssertionError(
            "manifest is missing required artifact entries:\n" + _render_lines(missing_required)
        )

    not_marked_required = tuple(
        path for path in required if path in entries and not entries[path].required
    )
    if not_marked_required:
        raise AssertionError(
            "manifest entries expected to be required are marked optional:\n"
            + _render_lines(not_marked_required)
        )

    resolved_root: Path | None
    if run_root is not None:
        resolved_root = _require_directory(run_root, role="run_root")
    elif isinstance(manifest, Path):
        resolved_root = _require_directory(manifest.parent, role="manifest parent")
    else:
        resolved_root = None

    if resolved_root is not None:
        failures: list[str] = []
        for entry in model.artifacts:
            artifact = resolved_root.joinpath(*PurePosixPath(entry.path).parts)
            try:
                resolved = assert_path_contained(
                    artifact,
                    resolved_root,
                    allow_root=False,
                )
            except AssertionError as exc:
                failures.append(f"{entry.path}: {exc}")
                continue

            if not resolved.exists():
                failures.append(f"{entry.path}: file is missing")
                continue
            if not resolved.is_file():
                failures.append(f"{entry.path}: path is not a regular file")
                continue

            try:
                size = resolved.stat().st_size
            except OSError as exc:
                failures.append(f"{entry.path}: stat failed: {exc}")
                continue

            if size != entry.size_bytes:
                failures.append(f"{entry.path}: size is {size}, expected {entry.size_bytes}")
                continue

            if verify_hashes:
                try:
                    digest = _sha256(resolved)
                except OSError as exc:
                    failures.append(f"{entry.path}: hashing failed: {exc}")
                    continue
                if digest != entry.sha256:
                    failures.append(f"{entry.path}: sha256 is {digest}, expected {entry.sha256}")

        if failures:
            raise AssertionError(
                "manifest entries do not match finalized artifacts:\n" + _render_lines(failures)
            )

    return model


def assert_path_contained(
    path: PathLike,
    root: PathLike,
    *,
    allow_root: bool = False,
    strict: bool = False,
) -> Path:
    if type(allow_root) is not bool:
        raise TypeError("allow_root must be a boolean")
    if type(strict) is not bool:
        raise TypeError("strict must be a boolean")

    candidate = _absolute_path(path, role="path").resolve(strict=strict)
    boundary = _absolute_path(root, role="root").resolve(strict=strict)

    try:
        relative = candidate.relative_to(boundary)
    except ValueError as exc:
        raise AssertionError(
            f"path escapes containment root: {candidate} is not within {boundary}"
        ) from exc

    if not allow_root and not relative.parts:
        raise AssertionError(f"path must be below containment root: {boundary}")

    return candidate


def assert_gold_unchanged(
    before: PathLike,
    after: PathLike,
    *,
    ignore: Iterable[str | PurePosixPath] = (),
) -> None:
    ignored = frozenset(_normalized_relative_path(value, role="ignore") for value in ignore)
    before_root = _absolute_path(before, role="before")
    after_root = _absolute_path(after, role="after")

    before_snapshot = _snapshot(before_root, ignored=ignored)
    after_snapshot = _snapshot(after_root, ignored=ignored)

    before_paths = set(before_snapshot)
    after_paths = set(after_snapshot)
    removed = tuple(sorted(before_paths - after_paths, key=_stable_text_key))
    added = tuple(sorted(after_paths - before_paths, key=_stable_text_key))
    modified = tuple(
        sorted(
            (
                path
                for path in before_paths & after_paths
                if before_snapshot[path] != after_snapshot[path]
            ),
            key=_stable_text_key,
        )
    )

    if not (removed or added or modified):
        return

    sections: list[str] = []
    if removed:
        sections.append("removed:\n" + _render_lines(removed))
    if added:
        sections.append("added:\n" + _render_lines(added))
    if modified:
        sections.append("modified:\n" + _render_lines(modified))

    raise AssertionError("gold content changed:\n" + "\n".join(sections))


def assert_no_process_leaks(
    processes: Iterable[int | _Pollable | _AliveCheck],
    *,
    timeout_sec: float = 1.0,
    poll_interval_sec: float = 0.01,
) -> None:
    timeout = _finite_non_negative_float(timeout_sec, role="timeout_sec")
    interval = _finite_positive_float(
        poll_interval_sec,
        role="poll_interval_sec",
    )
    tracked = tuple(processes)
    if not tracked:
        return

    deadline = time.monotonic() + timeout
    remaining = tuple(item for item in tracked if _process_is_alive(item))
    while remaining and time.monotonic() < deadline:
        time.sleep(min(interval, max(0.0, deadline - time.monotonic())))
        remaining = tuple(item for item in remaining if _process_is_alive(item))

    if remaining:
        rendered = "\n".join(f"  - {_process_label(item)}" for item in remaining)
        raise AssertionError(
            f"owned process leak detected ({len(remaining)} process(es)):\n{rendered}"
        )


def _json_object(source: object | Path, *, role: str) -> JsonObject:
    if isinstance(source, Path):
        try:
            raw = source.read_bytes()
        except OSError as exc:
            raise AssertionError(f"{role} could not be read from {source}: {exc}") from exc
        if raw.startswith(b"\xef\xbb\xbf"):
            raise AssertionError(f"{role} must not contain a UTF-8 BOM: {source}")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AssertionError(f"{role} is not valid UTF-8: {source}: {exc}") from exc
        try:
            value = json.loads(text, parse_constant=_reject_json_constant)
        except (ValueError, json.JSONDecodeError) as exc:
            raise AssertionError(f"{role} is not valid JSON: {source}: {exc}") from exc
    else:
        value = source

    if not isinstance(value, Mapping):
        raise AssertionError(f"{role} root must be a JSON object")
    if any(not isinstance(key, str) for key in value):
        raise AssertionError(f"{role} contains a non-string object key")
    return cast("JsonObject", value)


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number is prohibited: {value}")


def _normalized_manifest_paths(
    values: Iterable[str | PurePosixPath],
    *,
    role: str,
) -> tuple[str, ...]:
    prepared = tuple(_normalized_relative_path(value, role=role) for value in values)
    if len(prepared) != len(set(prepared)):
        raise ValueError(f"{role} must not contain duplicate paths")
    return tuple(sorted(prepared, key=_stable_text_key))


def _normalized_relative_path(
    value: str | PurePosixPath,
    *,
    role: str,
) -> str:
    text = value.as_posix() if isinstance(value, PurePosixPath) else value
    if not isinstance(text, str):
        raise TypeError(f"{role} entries must be strings or PurePosixPath")
    if not text or text != text.strip() or "\x00" in text:
        raise ValueError(f"{role} contains an invalid path: {text!r}")
    if "\\" in text or text.startswith("/") or _has_drive_prefix(text):
        raise ValueError(f"{role} paths must be normalized and relative: {text!r}")

    path = PurePosixPath(text)
    if path.as_posix() != text or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{role} paths must be normalized and relative: {text!r}")
    return text


def _has_drive_prefix(value: str) -> bool:
    return len(value) >= 2 and value[0].isalpha() and value[1] == ":"


def _snapshot(root: Path, *, ignored: frozenset[str]) -> dict[str, tuple[int, str]]:
    if not root.exists():
        raise AssertionError(f"snapshot source does not exist: {root}")

    if root.is_symlink():
        raise AssertionError(f"snapshot source must not be a symlink: {root}")

    if root.is_file():
        return {"": (root.stat().st_size, _sha256(root))}

    if not root.is_dir():
        raise AssertionError(f"snapshot source is not a file or directory: {root}")

    snapshot: dict[str, tuple[int, str]] = {}
    for path in sorted(root.rglob("*"), key=lambda item: _stable_text_key(str(item))):
        relative = path.relative_to(root).as_posix()
        if relative in ignored:
            continue
        if path.is_symlink():
            raise AssertionError(f"gold tree must not contain symlinks: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise AssertionError(f"gold tree contains a non-regular file: {path}")
        snapshot[relative] = (path.stat().st_size, _sha256(path))
    return snapshot


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_directory(value: PathLike, *, role: str) -> Path:
    path = _absolute_path(value, role=role).resolve(strict=True)
    if not path.is_dir():
        raise AssertionError(f"{role} is not a directory: {path}")
    return path


def _absolute_path(value: PathLike, *, role: str) -> Path:
    try:
        path = Path(value)
    except TypeError as exc:
        raise TypeError(f"{role} must be path-like") from exc
    if "\x00" in os.fspath(path):
        raise ValueError(f"{role} must not contain NUL")
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _process_is_alive(process: int | _Pollable | _AliveCheck) -> bool:
    if type(process) is int:
        return _pid_is_alive(process)

    poll = getattr(process, "poll", None)
    if callable(poll):
        try:
            return poll() is None
        except Exception as exc:
            raise AssertionError(f"could not poll {_process_label(process)}: {exc}") from exc

    is_alive = getattr(process, "is_alive", None)
    if callable(is_alive):
        try:
            return bool(is_alive())
        except Exception as exc:
            raise AssertionError(f"could not inspect {_process_label(process)}: {exc}") from exc

    raise TypeError("process entries must be integer PIDs or expose poll() or is_alive()")


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        raise ValueError("process IDs must be positive integers")
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return False
        if exc.errno == errno.EPERM:
            return True
        raise AssertionError(f"could not inspect process {pid}: {exc}") from exc
    return True


def _process_label(process: object) -> str:
    if type(process) is int:
        return f"pid={process}"
    pid = getattr(process, "pid", None)
    if type(pid) is int:
        return f"pid={pid} ({type(process).__name__})"
    name = getattr(process, "name", None)
    if callable(name):
        try:
            resolved = name()
        except Exception:
            resolved = None
        if isinstance(resolved, str) and resolved:
            return f"{resolved} ({type(process).__name__})"
    return repr(process)


def _finite_non_negative_float(value: float, *, role: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{role} must be a finite non-negative number")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{role} must be a finite non-negative number")
    return result


def _finite_positive_float(value: float, *, role: str) -> float:
    result = _finite_non_negative_float(value, role=role)
    if result <= 0:
        raise ValueError(f"{role} must be greater than zero")
    return result


def _stable_text_key(value: str) -> tuple[str, str]:
    return value.casefold(), value


def _render_lines(values: Iterable[str]) -> str:
    return "\n".join(f"  - {value}" for value in values)
