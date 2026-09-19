"""Unit tests for structured process-request validation and display rendering."""

from __future__ import annotations

from dataclasses import fields, replace
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from collections.abc import Collection
from typing import Any, cast

import pytest

from gf_wordbench.infrastructure.process.models import (
    ArtifactExpectation,
    ArtifactKind,
    ProcessInput,
    ProcessOperationKind,
    ProcessRequest,
)
from gf_wordbench.infrastructure.process.requests import (
    render_command_for_display,
    validate_process_request,
)
from gf_wordbench.kernel.errors import ContractViolationError, PathSecurityError


def _request(tmp_path: Path, **changes: object) -> ProcessRequest:
    root = tmp_path.resolve()
    stdin_path = root / "inputs" / "scenario.gfs"
    stdin_path.parent.mkdir(parents=True, exist_ok=True)
    stdin_path.write_text("parse -lang=Eng 'hello world'\n", encoding="utf-8")

    request = ProcessRequest(
        request_id="request-001",
        tool_id="gf",
        operation_id="compile-001",
        operation_kind=ProcessOperationKind.COMPILE,
        executable=Path(sys.executable).resolve(strict=True),
        args=("--make", "Grammar", "argument with spaces", ";literal-shell-text"),
        cwd=root,
        stdout_path=root / "captures" / "stdout.bin",
        stderr_path=root / "captures" / "stderr.bin",
        timeout_sec=30.0,
        approved_read_roots=(root,),
        approved_write_roots=(root,),
        evidence_policy="retain-raw-streams-v1",
        stdin=ProcessInput.from_file(stdin_path),
        environment_policy="controlled-inherit-v1",
        env_overrides={"GF_TEST_MODE": "1", "GF_TEST_TOKEN": "secret"},
        env_removals=frozenset({"GF_REMOVE_ME"}),
        sensitive_env_keys=frozenset({"GF_TEST_TOKEN"}),
        sensitive_arg_indexes=frozenset({1}),
        termination_grace_sec=2.0,
        output_limit_bytes=1024 * 1024,
        expected_artifacts=(
            ArtifactExpectation(
                path=root / "artifacts" / "Grammar.pgf",
                role="pgf",
                required=True,
                kind=ArtifactKind.FILE,
                minimum_size_bytes=1,
            ),
        ),
        metadata={"project_id": "example", "entrypoint": "Grammar"},
        mutability_class="run_artifacts_only",
        network_policy="denied",
    )
    return cast(ProcessRequest, cast(Any, replace)(request, **changes))


def _raw_request(request: ProcessRequest, **changes: object) -> ProcessRequest:
    """Return a request-shaped object that bypasses model-level normalization."""

    values = {field.name: getattr(request, field.name) for field in fields(ProcessRequest)}
    values.update(changes)
    return cast("ProcessRequest", SimpleNamespace(**values))


def _artifact_like(
    *,
    path: object,
    role: object = "artifact",
    required: object = True,
    kind: object = ArtifactKind.FILE,
    minimum_size_bytes: object = 0,
) -> object:
    return SimpleNamespace(
        path=path,
        role=role,
        required=required,
        kind=kind,
        minimum_size_bytes=minimum_size_bytes,
    )


def _stdin_like(
    *,
    kind: object,
    text: object = None,
    path: object = None,
    encoding: object = "utf-8",
) -> object:
    return SimpleNamespace(kind=kind, text=text, path=path, encoding=encoding)


def _symlink_or_skip(link: Path, target: Path, *, directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symbolic links are unavailable: {exc}")


def test_valid_request_passes_without_reserving_capture_paths(tmp_path: Path) -> None:
    request = _request(tmp_path)

    validate_process_request(request)

    assert request.command == (str(request.executable), *request.args)
    assert request.working_directory == request.cwd
    assert not request.stdout_path.exists()
    assert not request.stderr_path.exists()
    assert not request.stdout_path.parent.exists()


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    (
        ("request_id", "bad/request", "request_id must use"),
        ("request_id", " request-001", "outer whitespace"),
        ("tool_id", "GF", "tool_id must use"),
        ("operation_id", "compile request", "operation_id must use"),
        ("evidence_policy", "", "evidence_policy must be non-empty"),
        ("evidence_policy", " raw-v1 ", "outer whitespace"),
    ),
)
def test_identifiers_and_evidence_policy_are_strict(
    tmp_path: Path,
    field_name: str,
    value: object,
    message: str,
) -> None:
    request = _raw_request(_request(tmp_path), **{field_name: value})

    with pytest.raises(ContractViolationError, match=message):
        validate_process_request(request)


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    (
        ("operation_kind", "unknown", "unknown operation kind"),
        ("environment_policy", "inherit-everything", "unknown environment policy"),
        ("mutability_class", "unrestricted", "unknown mutability class"),
        ("network_policy", "internet", "unknown network policy"),
    ),
)
def test_registered_policy_vocabularies_are_enforced(
    tmp_path: Path,
    field_name: str,
    value: str,
    message: str,
) -> None:
    request = _raw_request(_request(tmp_path), **{field_name: value})

    with pytest.raises(ContractViolationError, match=message):
        validate_process_request(request)


def test_all_registered_operation_kinds_are_accepted(tmp_path: Path) -> None:
    base = _request(tmp_path)

    for operation_kind in ProcessOperationKind:
        validate_process_request(replace(base, operation_kind=operation_kind))


def test_executable_must_be_an_existing_absolute_regular_file(tmp_path: Path) -> None:
    request = _request(tmp_path)

    with pytest.raises(ContractViolationError, match="absolute path"):
        validate_process_request(replace(request, executable=Path("python")))

    missing = (tmp_path / "missing-tool").resolve()
    with pytest.raises(ContractViolationError, match="Executable does not resolve"):
        validate_process_request(replace(request, executable=missing))

    with pytest.raises(ContractViolationError, match="not a regular file"):
        validate_process_request(replace(request, executable=tmp_path.resolve()))


@pytest.mark.posix
@pytest.mark.skipif(os.name == "nt", reason="POSIX executable permission contract")
def test_posix_executable_permission_is_required(tmp_path: Path) -> None:
    tool = tmp_path / "tool"
    tool.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    tool.chmod(0o600)

    with pytest.raises(ContractViolationError, match="Executable permission is missing"):
        validate_process_request(replace(_request(tmp_path), executable=tool.resolve()))


def test_batch_launchers_require_a_separate_contract(tmp_path: Path) -> None:
    batch = tmp_path / "tool.CMD"
    batch.write_text("@echo off\r\n", encoding="utf-8")

    with pytest.raises(ContractViolationError, match="Batch executable"):
        validate_process_request(replace(_request(tmp_path), executable=batch.resolve()))


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    (
        ("approved_read_roots", (), "at least one approved root"),
        ("approved_write_roots", (), "at least one approved root"),
        ("approved_read_roots", "not-a-root-list", "iterable of directory paths"),
    ),
)
def test_approved_root_collections_are_explicit_and_non_empty(
    tmp_path: Path,
    field_name: str,
    value: object,
    message: str,
) -> None:
    request = _raw_request(_request(tmp_path), **{field_name: value})

    with pytest.raises(ContractViolationError, match=message):
        validate_process_request(request)


def test_approved_roots_must_resolve_to_directories(tmp_path: Path) -> None:
    request = _request(tmp_path)
    missing = (tmp_path / "missing-root").resolve()
    ordinary_file = tmp_path / "ordinary-file"
    ordinary_file.write_text("not a directory", encoding="utf-8")

    with pytest.raises(PathSecurityError, match="Approved root does not resolve"):
        validate_process_request(replace(request, approved_read_roots=(missing,)))

    with pytest.raises(PathSecurityError, match="not a directory"):
        validate_process_request(replace(request, approved_read_roots=(ordinary_file.resolve(),)))


def test_working_directory_must_exist_and_stay_inside_approved_roots(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    missing = (tmp_path / "missing-cwd").resolve()
    ordinary_file = tmp_path / "not-a-directory"
    ordinary_file.write_text("x", encoding="utf-8")
    approved = tmp_path / "approved"
    approved.mkdir()

    with pytest.raises(ContractViolationError, match="Working directory does not resolve"):
        validate_process_request(replace(request, cwd=missing))

    with pytest.raises(ContractViolationError, match="not a directory"):
        validate_process_request(replace(request, cwd=ordinary_file.resolve()))

    with pytest.raises(PathSecurityError, match="Working directory escapes approved roots"):
        validate_process_request(
            replace(
                request,
                approved_read_roots=(approved.resolve(),),
                approved_write_roots=(approved.resolve(),),
            )
        )


def test_duplicate_approved_roots_do_not_change_validation(tmp_path: Path) -> None:
    request = _request(tmp_path)
    root = tmp_path.resolve()

    validate_process_request(
        replace(
            request,
            approved_read_roots=(root, root),
            approved_write_roots=(root, root),
        )
    )


@pytest.mark.parametrize(
    ("args", "message"),
    (
        (["--make"], "ordered tuple"),
        (("--make", 7), r"args\[1\] must be a string"),
        (("--make", "bad\x00argument"), r"args\[1\].*NUL"),
    ),
)
def test_arguments_must_be_a_nul_free_ordered_tuple(
    tmp_path: Path,
    args: object,
    message: str,
) -> None:
    request = _raw_request(_request(tmp_path), args=args)

    with pytest.raises(ContractViolationError, match=message):
        validate_process_request(request)


def test_empty_spaces_unicode_and_shell_metacharacters_are_literal_arguments(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "must-not-exist"
    args = (
        "",
        "path with spaces/Grammaire Française.gf",
        f"; touch {marker}",
        "$(echo not-executed)",
    )
    request = replace(
        _request(tmp_path),
        args=args,
        sensitive_arg_indexes=frozenset(),
    )

    validate_process_request(request)
    rendered = render_command_for_display(request.executable, request.args)

    assert "Grammaire Française.gf" in rendered
    assert "not-executed" in rendered
    assert not marker.exists()


def test_capture_paths_must_be_absolute_distinct_owned_and_unreserved(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    outside = (tmp_path.parent / f"{tmp_path.name}-outside" / "stdout.bin").resolve()

    with pytest.raises(ContractViolationError, match="absolute path"):
        validate_process_request(replace(request, stdout_path=Path("stdout.bin")))

    with pytest.raises(ContractViolationError, match="must be distinct"):
        validate_process_request(_raw_request(request, stderr_path=request.stdout_path))

    with pytest.raises(PathSecurityError, match="Stdout capture path escapes approved roots"):
        validate_process_request(replace(request, stdout_path=outside))

    request.stdout_path.parent.mkdir(parents=True)
    request.stdout_path.write_bytes(b"reserved")
    with pytest.raises(ContractViolationError, match="stdout_path already exists"):
        validate_process_request(request)


def test_absolute_paths_with_parent_traversal_segments_are_rejected(tmp_path: Path) -> None:
    request = _request(tmp_path)
    traversing = tmp_path.resolve() / "captures" / ".." / "stdout.bin"

    with pytest.raises(PathSecurityError, match="parent traversal"):
        validate_process_request(replace(request, stdout_path=traversing))


@pytest.mark.security
def test_capture_path_cannot_escape_through_a_directory_symlink(tmp_path: Path) -> None:
    request = _request(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    link = tmp_path / "linked-output"
    _symlink_or_skip(link, outside, directory=True)

    with pytest.raises(PathSecurityError, match="escapes approved roots"):
        validate_process_request(replace(request, stdout_path=link / "stdout.bin"))


@pytest.mark.security
def test_dangling_capture_symlink_is_rejected(tmp_path: Path) -> None:
    request = _request(tmp_path)
    link = tmp_path / "dangling-output"
    _symlink_or_skip(link, tmp_path / "missing-target")

    with pytest.raises(PathSecurityError, match="unresolved symbolic link"):
        validate_process_request(replace(request, stdout_path=link))


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    (
        ("timeout_sec", 0, "timeout_sec must be a finite number greater than zero"),
        ("timeout_sec", math.inf, "timeout_sec must be a finite number greater than zero"),
        ("timeout_sec", True, "timeout_sec must be a finite number greater than zero"),
        (
            "termination_grace_sec",
            -0.1,
            "termination_grace_sec must be a finite non-negative number",
        ),
        (
            "termination_grace_sec",
            math.nan,
            "termination_grace_sec must be a finite non-negative number",
        ),
        ("output_limit_bytes", 0, "output_limit_bytes must be a positive integer"),
        ("output_limit_bytes", True, "output_limit_bytes must be a positive integer"),
    ),
)
def test_execution_limits_are_finite_and_bounded(
    tmp_path: Path,
    field_name: str,
    value: object,
    message: str,
) -> None:
    request = _raw_request(_request(tmp_path), **{field_name: value})

    with pytest.raises(ContractViolationError, match=message):
        validate_process_request(request)


def test_explicit_none_and_text_stdin_modes_are_valid(tmp_path: Path) -> None:
    base = _request(tmp_path)

    validate_process_request(replace(base, stdin=ProcessInput.none()))
    validate_process_request(replace(base, stdin=ProcessInput.from_text("")))
    validate_process_request(
        replace(base, stdin=ProcessInput.from_text("café 日本語 🙂\n", encoding="utf-8"))
    )


@pytest.mark.parametrize(
    ("stdin", "message"),
    (
        (
            _stdin_like(kind="unknown", encoding="utf-8"),
            "Unknown stdin kind",
        ),
        (
            _stdin_like(kind="none", text="unexpected", encoding="utf-8"),
            "cannot contain text",
        ),
        (
            _stdin_like(kind="text", text="q", path=Path("input.gfs")),
            "forbids a file path",
        ),
        (
            _stdin_like(kind="file", text="q", path=Path("input.gfs")),
            "forbids inline text",
        ),
        (
            _stdin_like(kind="file", path=None),
            "stdin.path must be a pathlib.Path",
        ),
    ),
)
def test_stdin_modes_are_mutually_exclusive(
    tmp_path: Path,
    stdin: object,
    message: str,
) -> None:
    request = _raw_request(_request(tmp_path), stdin=stdin)

    with pytest.raises(ContractViolationError, match=message):
        validate_process_request(request)


def test_stdin_encoding_and_file_contracts_are_validated(tmp_path: Path) -> None:
    request = _request(tmp_path)

    with pytest.raises(ContractViolationError, match="Unknown stdin encoding"):
        validate_process_request(
            replace(request, stdin=ProcessInput.from_text("q", encoding="no-such-codec"))
        )

    with pytest.raises(ContractViolationError, match="cannot be encoded"):
        validate_process_request(
            replace(request, stdin=ProcessInput.from_text("café", encoding="ascii"))
        )

    missing = (tmp_path / "missing.gfs").resolve()
    with pytest.raises(ContractViolationError, match="stdin file does not resolve"):
        validate_process_request(replace(request, stdin=ProcessInput.from_file(missing)))

    directory = tmp_path / "stdin-directory"
    directory.mkdir()
    with pytest.raises(ContractViolationError, match="not a regular file"):
        validate_process_request(replace(request, stdin=ProcessInput.from_file(directory)))


def test_stdin_file_must_stay_inside_an_approved_read_root(tmp_path: Path) -> None:
    request = _request(tmp_path)
    approved = tmp_path / "approved"
    approved.mkdir()
    outside = tmp_path / "outside" / "scenario.gfs"
    outside.parent.mkdir()
    outside.write_text("q\n", encoding="utf-8")

    with pytest.raises(PathSecurityError, match="Stdin file escapes approved roots"):
        validate_process_request(
            replace(
                request,
                stdin=ProcessInput.from_file(outside.resolve()),
                cwd=approved.resolve(),
                approved_read_roots=(approved.resolve(),),
                approved_write_roots=(approved.resolve(),),
                stdout_path=approved / "stdout.bin",
                stderr_path=approved / "stderr.bin",
                expected_artifacts=(),
            )
        )


def test_environment_overrides_and_removals_are_validated(tmp_path: Path) -> None:
    request = _request(tmp_path)

    with pytest.raises(ContractViolationError, match="env_overrides must be a mapping"):
        validate_process_request(_raw_request(request, env_overrides=[]))

    for key in ("", "BAD=KEY", "BAD\nKEY"):
        with pytest.raises(ContractViolationError, match="env_overrides key"):
            validate_process_request(_raw_request(request, env_overrides={key: "value"}))

    with pytest.raises(ContractViolationError, match="must be a string"):
        validate_process_request(_raw_request(request, env_overrides={"VALID": 7}))

    with pytest.raises(ContractViolationError, match="contains a NUL"):
        validate_process_request(_raw_request(request, env_overrides={"VALID": "bad\x00value"}))

    with pytest.raises(ContractViolationError, match="both overridden and removed"):
        validate_process_request(
            replace(
                request,
                env_overrides={"GF_CONFLICT": "1"},
                env_removals=frozenset({"GF_CONFLICT"}),
            )
        )


def test_environment_key_collections_reject_scalars_and_invalid_keys(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)

    with pytest.raises(ContractViolationError, match="env_removals must be a collection"):
        validate_process_request(_raw_request(request, env_removals="PATH"))

    with pytest.raises(ContractViolationError, match="sensitive_env_keys"):
        validate_process_request(_raw_request(request, sensitive_env_keys=frozenset({"BAD=KEY"})))


def test_environment_keys_cannot_collide_on_case_insensitive_platforms(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request(tmp_path)
    monkeypatch.setattr(os.path, "normcase", str.casefold)

    with pytest.raises(ContractViolationError, match="collide on this platform"):
        validate_process_request(
            _raw_request(request, env_overrides={"Path": "one", "PATH": "two"})
        )


@pytest.mark.parametrize(
    ("indexes", "message"),
    (
        ("1", "collection of integers"),
        (frozenset({True}), "must be integers"),
        (frozenset({-1}), "outside the argument vector"),
        (frozenset({99}), "outside the argument vector"),
    ),
)
def test_sensitive_argument_indexes_are_bounded_integers(
    tmp_path: Path,
    indexes: object,
    message: str,
) -> None:
    request = _raw_request(_request(tmp_path), sensitive_arg_indexes=indexes)

    with pytest.raises(ContractViolationError, match=message):
        validate_process_request(request)


def test_expected_artifacts_must_be_an_ordered_tuple(tmp_path: Path) -> None:
    request = _raw_request(_request(tmp_path), expected_artifacts=[])

    with pytest.raises(ContractViolationError, match="must be a tuple"):
        validate_process_request(request)


@pytest.mark.parametrize(
    ("artifact", "error_type", "message"),
    (
        (
            _artifact_like(path=Path("relative.pgf")),
            ContractViolationError,
            "absolute path",
        ),
        (
            _artifact_like(path=Path("/tmp/artifact.bin"), role=""),
            ContractViolationError,
            "role must be non-empty",
        ),
        (
            _artifact_like(path=Path("/tmp/artifact.bin"), kind="socket"),
            ContractViolationError,
            "unknown kind",
        ),
        (
            _artifact_like(path=Path("/tmp/artifact.bin"), required=1),
            ContractViolationError,
            "required must be a boolean",
        ),
        (
            _artifact_like(path=Path("/tmp/artifact.bin"), minimum_size_bytes=-1),
            ContractViolationError,
            "minimum_size_bytes must be a non-negative integer",
        ),
    ),
)
def test_expected_artifact_fields_are_strict(
    tmp_path: Path,
    artifact: object,
    error_type: type[Exception],
    message: str,
) -> None:
    request = _raw_request(_request(tmp_path), expected_artifacts=(artifact,))

    with pytest.raises(error_type, match=message):
        validate_process_request(request)


def test_expected_artifacts_stay_owned_and_cannot_reuse_sensitive_paths(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    outside = (tmp_path.parent / f"{tmp_path.name}-artifact" / "result.bin").resolve()
    gold = ArtifactExpectation(
        path=(tmp_path / "expected.GOLD").resolve(),
        role="gold",
        required=True,
        kind=ArtifactKind.FILE,
    )
    capture_reuse = ArtifactExpectation(
        path=request.stdout_path,
        role="capture-reuse",
        required=True,
        kind=ArtifactKind.FILE,
    )

    with pytest.raises(PathSecurityError, match="Expected artifact.*escapes approved roots"):
        validate_process_request(
            replace(
                request,
                expected_artifacts=(
                    ArtifactExpectation(
                        path=outside,
                        role="outside",
                        required=True,
                        kind=ArtifactKind.FILE,
                    ),
                ),
            )
        )

    with pytest.raises(PathSecurityError, match=r"\.gold"):
        validate_process_request(replace(request, expected_artifacts=(gold,)))

    with pytest.raises(ContractViolationError, match="cannot reuse a raw capture path"):
        validate_process_request(replace(request, expected_artifacts=(capture_reuse,)))


def test_duplicate_expected_artifact_paths_are_rejected(tmp_path: Path) -> None:
    request = _request(tmp_path)
    artifact = request.expected_artifacts[0]
    duplicate = replace(artifact, role="same-path-second-role")

    with pytest.raises(ContractViolationError, match="declared more than once"):
        validate_process_request(replace(request, expected_artifacts=(artifact, duplicate)))


def test_directory_artifact_expectation_is_valid_before_launch(tmp_path: Path) -> None:
    request = _request(tmp_path)
    directory = ArtifactExpectation(
        path=(tmp_path / "artifacts" / "generated-directory").resolve(),
        role="generated-directory",
        required=False,
        kind=ArtifactKind.DIRECTORY,
        minimum_size_bytes=0,
    )

    validate_process_request(replace(request, expected_artifacts=(directory,)))


@pytest.mark.parametrize(
    ("metadata", "message"),
    (
        ([], "metadata must be a mapping"),
        ({"": "value"}, "metadata key must be non-empty"),
        ({"key": 7}, "Metadata value.*must be a string"),
        ({"key": "bad\x00value"}, "Metadata value.*contains a NUL"),
    ),
)
def test_metadata_is_a_nul_free_string_mapping(
    tmp_path: Path,
    metadata: object,
    message: str,
) -> None:
    request = _raw_request(_request(tmp_path), metadata=metadata)

    with pytest.raises(ContractViolationError, match=message):
        validate_process_request(request)


def test_display_rendering_is_deterministic_and_redacts_only_declared_arguments(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    original_args = request.args

    first = render_command_for_display(
        request.executable,
        request.args,
        sensitive_arg_indexes=request.sensitive_arg_indexes,
    )
    second = render_command_for_display(
        request.executable,
        request.args,
        sensitive_arg_indexes=request.sensitive_arg_indexes,
    )

    assert first == second
    assert "Grammar" not in first
    assert "<redacted>" in first
    assert "argument with spaces" in first
    assert ";literal-shell-text" in first
    assert request.args == original_args


@pytest.mark.parametrize(
    ("indexes", "message"),
    (
        ("1", "collection of integers"),
        (frozenset({True}), "must be integers"),
        (frozenset({-1}), "outside the argument vector"),
        (frozenset({99}), "outside the argument vector"),
    ),
)
def test_display_rendering_validates_redaction_indexes(
    tmp_path: Path,
    indexes: object,
    message: str,
) -> None:
    request = _request(tmp_path)

    with pytest.raises(ContractViolationError, match=message):
        render_command_for_display(
            request.executable,
            request.args,
            sensitive_arg_indexes=cast(Collection[int], indexes),
        )


def test_display_rendering_requires_an_absolute_executable_and_safe_arguments(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)

    with pytest.raises(ContractViolationError, match="absolute path"):
        render_command_for_display(Path("gf"), request.args)

    with pytest.raises(ContractViolationError, match="NUL"):
        render_command_for_display(request.executable, ("bad\x00argument",))
