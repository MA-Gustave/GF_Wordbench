"""Unit tests for finalized artifact-manifest verification.

The suite exercises the verifier as a read-only integrity boundary.  It covers
standard, strict, and release verification; schema and path safety; artifact
integrity; required declarations; canonical text; unlisted finalized files;
and machine-summary consistency.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from gf_wordbench.kernel.statuses import ValidationStatus
from gf_wordbench.reporting.manifest import verifier as verifier_module
from gf_wordbench.reporting.manifest.verifier import verify_manifest


_SCHEMA_ID = "gf-wordbench.artifact-manifest"
_SCHEMA_VERSION = "1.0"
_HASH_ALGORITHM = "sha256"
_CREATOR = "gf-wordbench.tests"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _write(root: Path, relative_path: str, payload: bytes) -> Path:
    path = root.joinpath(*relative_path.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _entry(
    path: str,
    payload: bytes,
    *,
    role: str = "detail",
    media_type: str = "application/octet-stream",
    required: bool = True,
    created_by: str = _CREATOR,
    size_bytes: int | None = None,
    sha256: str | None = None,
) -> dict[str, object]:
    return {
        "path": path,
        "role": role,
        "media_type": media_type,
        "required": required,
        "size_bytes": len(payload) if size_bytes is None else size_bytes,
        "sha256": _sha256(payload) if sha256 is None else sha256,
        "created_by": created_by,
    }


def _document(
    *,
    run_id: str = "run-001",
    artifacts: list[dict[str, object]] | None = None,
    schema_id: str = _SCHEMA_ID,
    schema_version: str = _SCHEMA_VERSION,
    producer: object | None = None,
    generated_at: object = "2026-07-25T19:04:23Z",
    hash_algorithm: str = _HASH_ALGORITHM,
) -> dict[str, object]:
    return {
        "schema_id": schema_id,
        "schema_version": schema_version,
        "producer": (
            {"name": "gf-wordbench", "version": "1.0.0"}
            if producer is None
            else producer
        ),
        "run_id": run_id,
        "generated_at": generated_at,
        "hash_algorithm": hash_algorithm,
        "artifacts": list(artifacts or []),
    }


def _policy(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "mode": "standard",
        "expected_run_id": "run-001",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _write_manifest(
    run_root: Path,
    document: object,
    *,
    name: str = "manifest.json",
    final_lf: bool = True,
    bom: bool = False,
) -> Path:
    text = json.dumps(
        document,
        ensure_ascii=False,
        indent=2,
        allow_nan=True,
    )
    if final_lf:
        text += "\n"
    payload = text.encode("utf-8")
    if bom:
        payload = b"\xef\xbb\xbf" + payload
    return _write(run_root, name, payload)


def _verify_document(
    run_root: Path,
    document: object,
    *,
    policy: object | None = None,
    name: str = "manifest.json",
    final_lf: bool = True,
    bom: bool = False,
):
    manifest_path = _write_manifest(
        run_root,
        document,
        name=name,
        final_lf=final_lf,
        bom=bom,
    )
    return verify_manifest(
        manifest_path,
        run_root,
        _policy() if policy is None else policy,
    )


def _diagnostics(result: object) -> str:
    return "\n".join(
        (
            str(getattr(result, "message", "")),
            *(str(item) for item in getattr(result, "warnings", ())),
        )
    )


def _assert_code(result: object, code: str) -> None:
    assert code in _diagnostics(result)


def test_standard_verification_accepts_valid_manifest_and_preserves_bytes(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    payload = "résultat final\n".encode()
    artifact = _write(run_root, "details/result.txt", payload)
    original = artifact.read_bytes()
    document = _document(
        artifacts=[
            _entry(
                "details/result.txt",
                payload,
                media_type="text/plain; charset=utf-8",
            )
        ]
    )

    result = _verify_document(run_root, document)

    assert result.status is ValidationStatus.OK
    assert result.verified is True
    assert result.schema_version == _SCHEMA_VERSION
    assert result.artifacts_checked == 1
    assert result.required_artifacts_checked == 1
    assert result.missing_paths == ()
    assert result.mismatched_paths == ()
    assert result.unsafe_paths == ()
    assert result.warnings == ()
    assert artifact.read_bytes() == original


def test_string_paths_are_coerced_at_public_boundary(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    payload = b"ok"
    _write(run_root, "detail.bin", payload)
    manifest_path = _write_manifest(
        run_root,
        _document(artifacts=[_entry("detail.bin", payload)]),
    )

    result = verify_manifest(str(manifest_path), str(run_root), _policy())

    assert result.status is ValidationStatus.OK
    assert result.manifest_path == manifest_path.resolve()


def test_run_id_is_inferred_from_canonical_run_directory(tmp_path: Path) -> None:
    run_root = tmp_path / "run_20260725_190423"
    run_root.mkdir()

    result = _verify_document(
        run_root,
        _document(run_id="20260725_190423"),
        policy=_policy(expected_run_id=None),
    )

    assert result.status is ValidationStatus.OK


@pytest.mark.parametrize(
    ("document", "code"),
    [
        (_document(schema_id="other"), "MANIFEST_SCHEMA_ID_INVALID"),
        (
            _document(schema_version="2.0"),
            "MANIFEST_SCHEMA_VERSION_UNSUPPORTED",
        ),
        (
            _document(schema_version="not-a-version"),
            "MANIFEST_SCHEMA_VERSION_UNSUPPORTED",
        ),
        (
            _document(hash_algorithm="sha512"),
            "MANIFEST_HASH_ALGORITHM_INVALID",
        ),
        (
            _document(producer={"name": "", "version": "1.0.0"}),
            "MANIFEST_ARTIFACT_ENTRY_INVALID",
        ),
        (
            _document(run_id="other-run"),
            "MANIFEST_RUN_ID_MISMATCH",
        ),
    ],
)
def test_invalid_root_contracts_are_errors(
    tmp_path: Path,
    document: dict[str, object],
    code: str,
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()

    result = _verify_document(run_root, document)

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, code)


def test_supported_schema_minor_is_recorded(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()

    result = _verify_document(
        run_root,
        _document(schema_version="1.99"),
    )

    assert result.status is ValidationStatus.OK
    assert result.schema_version == "1.99"


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        (b"{", "MANIFEST_JSON_INVALID"),
        (b"[]\n", "MANIFEST_JSON_INVALID"),
        (b'{"value": NaN}\n', "MANIFEST_JSON_INVALID"),
        (b"\xff\n", "MANIFEST_JSON_INVALID"),
    ],
)
def test_invalid_manifest_encoding_or_json_is_an_error(
    tmp_path: Path,
    payload: bytes,
    code: str,
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    manifest_path = _write(run_root, "manifest.json", payload)

    result = verify_manifest(manifest_path, run_root, _policy())

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, code)


def test_utf8_bom_is_rejected_in_every_mode(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()

    result = _verify_document(
        run_root,
        _document(),
        bom=True,
    )

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, "MANIFEST_JSON_INVALID")


def test_strict_mode_requires_canonical_manifest_name_and_final_lf(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()

    wrong_name = _verify_document(
        run_root,
        _document(),
        policy=_policy(mode="strict"),
        name="artifact-manifest.json",
    )
    no_final_lf = _verify_document(
        run_root,
        _document(),
        policy=_policy(mode="strict"),
        final_lf=False,
    )

    assert wrong_name.status is ValidationStatus.ERROR
    _assert_code(wrong_name, "MANIFEST_ARTIFACT_PATH_SELF")
    assert no_final_lf.status is ValidationStatus.ERROR
    _assert_code(no_final_lf, "MANIFEST_JSON_INVALID")


def test_standard_mode_accepts_manifest_without_final_lf(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()

    result = _verify_document(
        run_root,
        _document(),
        final_lf=False,
    )

    assert result.status is ValidationStatus.OK


@pytest.mark.parametrize(
    ("path", "code"),
    [
        ("", "MANIFEST_ARTIFACT_PATH_EMPTY"),
        ("/absolute.txt", "MANIFEST_ARTIFACT_PATH_ABSOLUTE"),
        (r"C:\absolute.txt", "MANIFEST_ARTIFACT_PATH_ABSOLUTE"),
        ("../escape.txt", "MANIFEST_ARTIFACT_PATH_TRAVERSAL"),
        ("manifest.json", "MANIFEST_ARTIFACT_PATH_SELF"),
    ],
)
def test_unsafe_artifact_paths_are_errors(
    tmp_path: Path,
    path: str,
    code: str,
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    document = _document(artifacts=[_entry(path, b"")])

    result = _verify_document(run_root, document)

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, code)
    assert result.unsafe_paths


def test_duplicate_artifact_path_is_an_error(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    payload = b"same"
    _write(run_root, "same.bin", payload)
    entry = _entry("same.bin", payload)

    result = _verify_document(
        run_root,
        _document(artifacts=[entry, dict(entry)]),
    )

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, "MANIFEST_ARTIFACT_PATH_DUPLICATE")


def test_standard_mode_normalizes_portable_backslash_path(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    payload = b"portable"
    _write(run_root, "raw/result.txt", payload)

    result = _verify_document(
        run_root,
        _document(artifacts=[_entry(r"raw\result.txt", payload)]),
    )

    assert result.status is ValidationStatus.OK
    assert result.artifacts_checked == 1


def test_strict_mode_rejects_noncanonical_path_format(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    payload = b"portable"
    _write(run_root, "raw/result.txt", payload)

    result = _verify_document(
        run_root,
        _document(artifacts=[_entry(r"raw\result.txt", payload)]),
        policy=_policy(mode="strict"),
    )

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, "MANIFEST_ARTIFACT_ENTRY_INVALID")


def test_strict_mode_requires_canonical_entry_order(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    a_payload = b"a"
    z_payload = b"z"
    _write(run_root, "a.bin", a_payload)
    _write(run_root, "z.bin", z_payload)

    result = _verify_document(
        run_root,
        _document(
            artifacts=[
                _entry("z.bin", z_payload),
                _entry("a.bin", a_payload),
            ]
        ),
        policy=_policy(mode="strict"),
    )

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, "MANIFEST_ARTIFACT_ENTRY_INVALID")


@pytest.mark.parametrize(
    "field_overrides",
    [
        {"required": 1},
        {"size_bytes": True},
        {"size_bytes": -1},
        {"role": ""},
        {"media_type": ""},
        {"created_by": ""},
        {"sha256": "not-a-digest"},
    ],
)
def test_invalid_entry_fields_are_errors(
    tmp_path: Path,
    field_overrides: dict[str, object],
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    payload = b"entry"
    _write(run_root, "entry.bin", payload)
    entry = _entry("entry.bin", payload)
    entry.update(field_overrides)

    result = _verify_document(
        run_root,
        _document(artifacts=[entry]),
    )

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, "MANIFEST_ARTIFACT_ENTRY_INVALID")


def test_missing_required_artifact_is_fail(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()

    result = _verify_document(
        run_root,
        _document(
            artifacts=[
                _entry("missing.bin", b"expected", required=True),
            ]
        ),
    )

    assert result.status is ValidationStatus.FAIL
    assert result.missing_paths == ("missing.bin",)
    assert result.artifacts_checked == 0
    _assert_code(result, "MANIFEST_ARTIFACT_MISSING")


def test_missing_optional_artifact_is_warning_not_failure(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()

    result = _verify_document(
        run_root,
        _document(
            artifacts=[
                _entry("optional.bin", b"expected", required=False),
            ]
        ),
    )

    assert result.status is ValidationStatus.OK
    assert result.missing_paths == ("optional.bin",)
    assert result.mismatched_paths == ()
    _assert_code(result, "MANIFEST_ARTIFACT_MISSING")


def test_size_and_hash_mismatches_are_reported_once_per_path(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    actual = b"actual"
    _write(run_root, "result.bin", actual)

    result = _verify_document(
        run_root,
        _document(
            artifacts=[
                _entry(
                    "result.bin",
                    actual,
                    size_bytes=len(actual) + 1,
                    sha256="0" * 64,
                )
            ]
        ),
    )

    assert result.status is ValidationStatus.FAIL
    assert result.artifacts_checked == 1
    assert result.required_artifacts_checked == 1
    assert result.mismatched_paths == ("result.bin",)
    _assert_code(result, "MANIFEST_ARTIFACT_SIZE_MISMATCH")
    _assert_code(result, "MANIFEST_ARTIFACT_HASH_MISMATCH")


def test_uppercase_recorded_sha256_is_compared_case_insensitively(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    payload = b"digest"
    _write(run_root, "digest.bin", payload)

    result = _verify_document(
        run_root,
        _document(
            artifacts=[
                _entry("digest.bin", payload, sha256=_sha256(payload).upper())
            ]
        ),
    )

    assert result.status is ValidationStatus.OK


def test_directory_entry_is_an_error(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    (run_root / "directory").mkdir()

    result = _verify_document(
        run_root,
        _document(artifacts=[_entry("directory", b"")]),
    )

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, "MANIFEST_ARTIFACT_NOT_FILE")


def test_strict_mode_rejects_symlink_artifact(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    payload = b"target"
    target = _write(run_root, "target.bin", payload)
    link = run_root / "link.bin"
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("symlink creation is unavailable")

    result = _verify_document(
        run_root,
        _document(artifacts=[_entry("link.bin", payload)]),
        policy=_policy(mode="strict", allow_symlinks=False),
    )

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, "MANIFEST_ARTIFACT_SYMLINK")


def test_standard_mode_may_verify_in_root_symlink_when_policy_allows_it(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    payload = b"target"
    target = _write(run_root, "target.bin", payload)
    link = run_root / "link.bin"
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("symlink creation is unavailable")

    result = _verify_document(
        run_root,
        _document(artifacts=[_entry("link.bin", payload)]),
        policy=_policy(mode="standard", allow_symlinks=True),
    )

    assert result.status is ValidationStatus.OK


def test_artifact_resolving_outside_run_root_is_an_error(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    outside = _write(tmp_path, "outside.bin", b"outside")
    link = run_root / "link.bin"
    try:
        link.symlink_to(outside)
    except (NotImplementedError, OSError):
        pytest.skip("symlink creation is unavailable")

    result = _verify_document(
        run_root,
        _document(artifacts=[_entry("link.bin", b"outside")]),
    )

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, "MANIFEST_ARTIFACT_PATH_TRAVERSAL")


def test_mutation_during_hash_is_an_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    payload = b"stable"
    artifact = _write(run_root, "artifact.bin", payload)
    original_sha256 = verifier_module._sha256

    def mutate_after_hash(path: Path) -> str:
        digest = original_sha256(path)
        path.write_bytes(path.read_bytes() + b"!")
        return digest

    monkeypatch.setattr(verifier_module, "_sha256", mutate_after_hash)

    result = _verify_document(
        run_root,
        _document(artifacts=[_entry("artifact.bin", payload)]),
    )

    assert artifact.read_bytes().endswith(b"!")
    assert result.status is ValidationStatus.ERROR
    _assert_code(result, "MANIFEST_ARTIFACT_MUTATED_DURING_HASH")


@pytest.mark.parametrize(
    ("role", "media_type", "created_by", "policy_overrides", "code"),
    [
        (
            "unknown_role",
            "application/octet-stream",
            _CREATOR,
            {"allowed_roles": ("detail",)},
            "MANIFEST_ROLE_UNKNOWN",
        ),
        (
            "machine_summary",
            "text/plain; charset=utf-8",
            _CREATOR,
            {},
            "MANIFEST_MEDIA_TYPE_INVALID",
        ),
        (
            "detail",
            "application/octet-stream",
            "unknown.creator",
            {"allowed_creators": (_CREATOR,)},
            "MANIFEST_CREATED_BY_UNKNOWN",
        ),
    ],
)
def test_strict_metadata_registry_and_role_media_contracts(
    tmp_path: Path,
    role: str,
    media_type: str,
    created_by: str,
    policy_overrides: dict[str, object],
    code: str,
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    payload = b"{}\n" if role == "machine_summary" else b"metadata"
    _write(run_root, "artifact.bin", payload)
    policy = _policy(mode="strict", **policy_overrides)

    result = _verify_document(
        run_root,
        _document(
            artifacts=[
                _entry(
                    "artifact.bin",
                    payload,
                    role=role,
                    media_type=media_type,
                    created_by=created_by,
                )
            ]
        ),
        policy=policy,
    )

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, code)


@pytest.mark.parametrize(
    "payload",
    [
        b'{"status":"OK"}',
        b"\xef\xbb\xbf{}\n",
        b"\xff\n",
    ],
)
def test_strict_known_text_roles_require_canonical_utf8_and_final_lf(
    tmp_path: Path,
    payload: bytes,
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    _write(run_root, "summary.json", payload)

    result = _verify_document(
        run_root,
        _document(
            artifacts=[
                _entry(
                    "summary.json",
                    payload,
                    role="machine_summary",
                    media_type="application/json",
                )
            ]
        ),
        policy=_policy(mode="strict"),
    )

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, "MANIFEST_MEDIA_TYPE_INVALID")


def test_standard_mode_does_not_apply_canonical_text_check(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    payload = b'{"status":"OK"}'
    _write(run_root, "summary.json", payload)

    result = _verify_document(
        run_root,
        _document(
            artifacts=[
                _entry(
                    "summary.json",
                    payload,
                    role="machine_summary",
                    media_type="application/json",
                )
            ]
        ),
    )

    assert result.status is ValidationStatus.OK


def test_policy_required_path_must_be_declared_required(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    payload = b"optional"
    _write(run_root, "required.bin", payload)

    result = _verify_document(
        run_root,
        _document(
            artifacts=[
                _entry("required.bin", payload, required=False),
            ]
        ),
        policy=_policy(required_paths=("required.bin",)),
    )

    assert result.status is ValidationStatus.FAIL
    assert result.mismatched_paths == ("required.bin",)
    _assert_code(result, "MANIFEST_REQUIRED_ARTIFACT_UNDECLARED")


def test_strict_unlisted_detection_can_warn_without_failing(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    listed = b"listed"
    _write(run_root, "raw/listed.log", listed)
    _write(run_root, "raw/unlisted.log", b"unlisted")

    result = _verify_document(
        run_root,
        _document(
            artifacts=[
                _entry(
                    "raw/listed.log",
                    listed,
                    role="master_log",
                    media_type="text/plain; charset=utf-8",
                )
            ]
        ),
        policy=_policy(
            mode="strict",
            detect_unlisted_files=True,
            reject_unlisted_files=False,
            owned_directories=("raw",),
        ),
    )

    assert result.status is ValidationStatus.OK
    _assert_code(result, "MANIFEST_REQUIRED_ARTIFACT_UNDECLARED")
    assert "raw/unlisted.log" in _diagnostics(result)


def test_strict_unlisted_detection_can_fail_closed(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    _write(run_root, "raw/unlisted.log", b"unlisted")

    result = _verify_document(
        run_root,
        _document(),
        policy=_policy(
            mode="strict",
            detect_unlisted_files=True,
            reject_unlisted_files=True,
            owned_directories=("raw",),
        ),
    )

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, "MANIFEST_REQUIRED_ARTIFACT_UNDECLARED")


def test_summary_verification_requires_declared_machine_summary(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()

    result = _verify_document(
        run_root,
        _document(),
        policy=_policy(verify_summary=True),
    )

    assert result.status is ValidationStatus.FAIL
    _assert_code(result, "MANIFEST_SUMMARY_INCONSISTENT")


def test_summary_run_id_must_match_manifest(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    summary_payload = json.dumps(
        {"metadata": {"run_id": "different"}},
        ensure_ascii=False,
    ).encode() + b"\n"
    _write(run_root, "summary.json", summary_payload)

    result = _verify_document(
        run_root,
        _document(
            artifacts=[
                _entry(
                    "summary.json",
                    summary_payload,
                    role="machine_summary",
                    media_type="application/json",
                )
            ]
        ),
        policy=_policy(verify_summary=True),
    )

    assert result.status is ValidationStatus.FAIL
    _assert_code(result, "MANIFEST_SUMMARY_INCONSISTENT")


def test_summary_declared_existing_artifact_must_be_manifested(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    _write(run_root, "details/extra.txt", b"extra")
    summary_payload = json.dumps(
        {
            "metadata": {"run_id": "run-001"},
            "artifacts": {
                "manifest": "manifest.json",
                "details": ["details/extra.txt"],
            },
        },
        ensure_ascii=False,
    ).encode() + b"\n"
    _write(run_root, "summary.json", summary_payload)

    result = _verify_document(
        run_root,
        _document(
            artifacts=[
                _entry(
                    "summary.json",
                    summary_payload,
                    role="machine_summary",
                    media_type="application/json",
                )
            ]
        ),
        policy=_policy(verify_summary=True),
    )

    assert result.status is ValidationStatus.FAIL
    assert result.mismatched_paths == ("details/extra.txt",)
    _assert_code(result, "MANIFEST_SUMMARY_INCONSISTENT")


def test_release_mode_requires_framework_artifacts(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()

    result = _verify_document(
        run_root,
        _document(),
        policy=_policy(mode="release"),
    )

    assert result.status is ValidationStatus.FAIL
    _assert_code(result, "MANIFEST_REQUIRED_ARTIFACT_UNDECLARED")
    assert {
        "summary.json",
        "summary.md",
        "AI_READY.md",
        "top_errors.txt",
        "raw/master.log",
    }.issubset(result.mismatched_paths)


def test_release_mode_requires_pgf_when_configured(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    document = _release_document(run_root)

    result = _verify_document(
        run_root,
        document,
        policy=_policy(mode="release", require_pgf=True),
    )

    assert result.status is ValidationStatus.FAIL
    _assert_code(result, "MANIFEST_REQUIRED_ARTIFACT_UNDECLARED")
    assert "release requires a PGF artifact" in _diagnostics(result)


def _release_document(run_root: Path) -> dict[str, object]:
    summary_payload = json.dumps(
        {
            "metadata": {
                "run_id": "run-001",
                "project_id": "demo",
                "project_name": "Demo",
            },
            "artifacts": {"manifest": "manifest.json"},
        },
        ensure_ascii=False,
        indent=2,
    ).encode() + b"\n"
    payloads: dict[str, tuple[bytes, str, str]] = {
        "AI_READY.md": (
            b"# AI handoff\n",
            "ai_handoff",
            "text/markdown; charset=utf-8",
        ),
        "raw/master.log": (
            b"run complete\n",
            "master_log",
            "text/plain; charset=utf-8",
        ),
        "summary.json": (
            summary_payload,
            "machine_summary",
            "application/json",
        ),
        "summary.md": (
            b"# Summary\n",
            "human_summary",
            "text/markdown; charset=utf-8",
        ),
        "top_errors.txt": (
            b"No errors.\n",
            "top_errors",
            "text/plain; charset=utf-8",
        ),
    }
    entries: list[dict[str, object]] = []
    for path in sorted(payloads):
        payload, role, media_type = payloads[path]
        _write(run_root, path, payload)
        entries.append(
            _entry(
                path,
                payload,
                role=role,
                media_type=media_type,
                required=True,
            )
        )
    return _document(artifacts=entries)


def test_release_manifest_with_required_artifacts_and_consistent_summary_is_ok(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    document = _release_document(run_root)

    result = _verify_document(
        run_root,
        document,
        policy=_policy(mode="release"),
    )

    assert result.status is ValidationStatus.OK
    assert result.artifacts_checked == 5
    assert result.required_artifacts_checked == 5
    assert result.failure_paths == ()


def test_release_summary_requires_active_project_identity(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    document = _release_document(run_root)
    summary_path = run_root / "summary.json"
    summary_payload = json.dumps(
        {
            "metadata": {"run_id": "run-001"},
            "artifacts": {"manifest": "manifest.json"},
        },
        indent=2,
    ).encode() + b"\n"
    summary_path.write_bytes(summary_payload)
    for entry in document["artifacts"]:  # type: ignore[index]
        if entry["path"] == "summary.json":
            entry["size_bytes"] = len(summary_payload)
            entry["sha256"] = _sha256(summary_payload)

    result = _verify_document(
        run_root,
        document,
        policy=_policy(mode="release"),
    )

    assert result.status is ValidationStatus.FAIL
    _assert_code(result, "MANIFEST_SUMMARY_INCONSISTENT")


def test_manifest_outside_run_root_is_rejected(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()
    manifest_path = _write_manifest(tmp_path, _document(), name="outside.json")

    result = verify_manifest(manifest_path, run_root, _policy())

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, "MANIFEST_ARTIFACT_PATH_TRAVERSAL")
    assert result.unsafe_paths == (str(manifest_path),)


def test_missing_manifest_is_an_error(tmp_path: Path) -> None:
    run_root = tmp_path / "run_run-001"
    run_root.mkdir()

    result = verify_manifest(
        run_root / "manifest.json",
        run_root,
        _policy(),
    )

    assert result.status is ValidationStatus.ERROR
    _assert_code(result, "MANIFEST_MISSING")


def test_missing_or_non_directory_run_root_is_an_error(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing"
    missing_result = verify_manifest(
        missing_root / "manifest.json",
        missing_root,
        _policy(),
    )

    file_root = _write(tmp_path, "not-a-directory", b"file")
    file_result = verify_manifest(
        file_root / "manifest.json",
        file_root,
        _policy(),
    )

    assert missing_result.status is ValidationStatus.ERROR
    _assert_code(missing_result, "MANIFEST_UNREADABLE")
    assert file_result.status is ValidationStatus.ERROR
    _assert_code(file_result, "MANIFEST_UNREADABLE")
