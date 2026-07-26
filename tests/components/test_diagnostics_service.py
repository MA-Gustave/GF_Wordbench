"""Component tests for diagnostic parsing and causal classification services."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import pytest

from gf_wordbench.diagnostics import public as diagnostics_public
from gf_wordbench.diagnostics.classification.service import (
    ClassificationService,
    enforce_classification_coherence,
)
from gf_wordbench.diagnostics.models import DiagnosticEvidence
from gf_wordbench.diagnostics.parsing.service import (
    PARSER_VERSION,
    DiagnosticParsingService,
    parse_diagnostics,
)
from gf_wordbench.kernel.errors import ContractViolationError
from gf_wordbench.kernel.statuses import (
    DiagnosticClass,
    ErrorKind,
    ExecutionState,
    ValidationStatus,
)

pytestmark = pytest.mark.component


@dataclass(frozen=True, slots=True)
class _DiagnosticResult:
    subject_id: str
    status: ValidationStatus
    error_kind: ErrorKind
    primary_message: str
    diagnostic_class: DiagnosticClass = DiagnosticClass.AMBIGUOUS
    blocked_by: tuple[str, ...] = ()
    references: tuple[str, ...] = ()
    source_path: Path | None = None
    is_direct: bool = False


def _evidence(
    tmp_path: Path,
    *,
    operation_kind: str = "compile",
    execution_state: ExecutionState = ExecutionState.COMPLETED,
    exit_code: int | None = 0,
    stdout_text: str | None = "",
    stderr_text: str | None = "",
    strict: bool = False,
    stdout_truncated: bool = False,
    stderr_truncated: bool = False,
    decoding_lossy: bool = False,
) -> DiagnosticEvidence:
    supported = {item.name for item in fields(DiagnosticEvidence)}
    values: dict[str, Any] = {
        "operation_kind": operation_kind,
        "execution_state": execution_state,
        "exit_code": exit_code,
        "stdout_path": tmp_path / "stdout.txt",
        "stderr_path": tmp_path / "stderr.txt",
        "artifact_observations": (),
        "metadata": {},
        "stdout_text": stdout_text,
        "stderr_text": stderr_text,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
        "decoding_lossy": decoding_lossy,
        "capture_complete": not (
            stdout_truncated or stderr_truncated or decoding_lossy
        ),
        "strict": strict,
    }
    return DiagnosticEvidence(
        **{name: value for name, value in values.items() if name in supported}
    )


def _status(result: object) -> ValidationStatus:
    value = getattr(result, "status")
    if isinstance(value, ValidationStatus):
        return value
    return ValidationStatus(str(getattr(value, "value", value)))


def _operation(result: object) -> str:
    value = getattr(result, "operation", None)
    if value is None:
        value = getattr(result, "operation_kind")
    return str(getattr(value, "value", value))


def _records(result: object) -> tuple[object, ...]:
    return tuple(getattr(result, "records"))


def _primary(result: object) -> object | None:
    primary = getattr(result, "primary", None)
    if primary is not None:
        return primary
    primary_id = getattr(result, "primary_record_id", None)
    if primary_id is None:
        return None
    return next(
        record
        for record in _records(result)
        if getattr(record, "record_id") == primary_id
    )


def _warning_texts(result: object) -> tuple[str, ...]:
    rendered: list[str] = []
    for warning in tuple(getattr(result, "warnings", ())):
        value = getattr(warning, "message", warning)
        rendered.append(str(value))
    return tuple(rendered)


def _pattern_id(record: object) -> str:
    return str(getattr(getattr(record, "pattern_id"), "value", getattr(record, "pattern_id")))


def _error_kind(record: object) -> ErrorKind:
    value = getattr(record, "error_kind")
    if isinstance(value, ErrorKind):
        return value
    return ErrorKind(str(getattr(value, "value", value)))


def _fail_if_called(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise AssertionError("diagnostics services must not launch external processes")


def test_public_facade_reexports_the_canonical_service_functions() -> None:
    assert diagnostics_public.parse_diagnostics is parse_diagnostics
    assert diagnostics_public.classify_file_results.__module__.endswith(
        ".classification.service"
    )
    assert diagnostics_public.classify_scenario_results.__module__.endswith(
        ".classification.service"
    )
    assert "parse_diagnostics" in diagnostics_public.__all__
    assert "classify_file_results" in diagnostics_public.__all__
    assert "classify_scenario_results" in diagnostics_public.__all__


def test_parsing_service_configuration_is_immutable_and_validated() -> None:
    service = DiagnosticParsingService()

    assert service.max_warnings > 0
    with pytest.raises((AttributeError, TypeError)):
        service.max_warnings = 1  # type: ignore[misc]
    with pytest.raises(TypeError, match="pattern_provider"):
        DiagnosticParsingService(pattern_provider=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="positive"):
        DiagnosticParsingService(max_warnings=0)


def test_launch_failure_without_streams_is_a_complete_skipped_parse(
    tmp_path: Path,
) -> None:
    result = parse_diagnostics(
        _evidence(
            tmp_path,
            execution_state=ExecutionState.LAUNCH_FAILED,
            exit_code=None,
            stdout_text=None,
            stderr_text=None,
        )
    )

    assert _status(result) is ValidationStatus.SKIPPED
    assert getattr(result, "parser_version") == PARSER_VERSION
    assert _operation(result) == "compile"
    assert _records(result) == ()
    assert _primary(result) is None
    assert getattr(result, "parse_complete") is True
    assert any("did not launch" in text for text in _warning_texts(result))


def test_missing_raw_streams_after_execution_is_a_parser_error(
    tmp_path: Path,
) -> None:
    result = parse_diagnostics(
        _evidence(
            tmp_path,
            execution_state=ExecutionState.COMPLETED,
            exit_code=1,
            stdout_text=None,
            stderr_text=None,
        )
    )

    assert _status(result) is ValidationStatus.ERROR
    assert _records(result) == ()
    assert _primary(result) is None
    assert getattr(result, "parse_complete") is False
    assert any("unavailable" in text for text in _warning_texts(result))


def test_recognized_gf_syntax_failure_is_successfully_parsed(
    tmp_path: Path,
) -> None:
    evidence = _evidence(
        tmp_path,
        exit_code=1,
        stderr_text="Syntax error: Unexpected token near line 4\n",
    )

    result = parse_diagnostics(evidence)
    primary = _primary(result)

    assert _status(result) is ValidationStatus.OK
    assert primary is not None
    assert _pattern_id(primary) == "DP-GFSYN-001"
    assert _error_kind(primary) is ErrorKind.SYNTAX
    assert "Unexpected token" in str(getattr(primary, "message"))
    assert getattr(result, "parse_complete") is True
    assert getattr(result, "fatal_detected") is False


def test_multiline_type_diagnostic_retains_expected_and_inferred_context(
    tmp_path: Path,
) -> None:
    evidence = _evidence(
        tmp_path,
        exit_code=1,
        stderr_text=(
            "Happened in linearize Example\n"
            "expected: NP\n"
            "inferred: VP\n"
        ),
    )

    result = parse_diagnostics(evidence)
    primary = _primary(result)

    assert _status(result) is ValidationStatus.OK
    assert primary is not None
    assert _pattern_id(primary) == "DP-GFTYPE-001"
    assert _error_kind(primary) is ErrorKind.TYPE
    combined = "\n".join(
        str(getattr(primary, name, ""))
        for name in ("message", "detail", "raw_excerpt")
    )
    assert "expected" in combined.lower()
    assert "inferred" in combined.lower()
    assert "NP" in combined
    assert "VP" in combined


def test_nonzero_unknown_output_uses_the_documented_fallback(
    tmp_path: Path,
) -> None:
    result = parse_diagnostics(
        _evidence(
            tmp_path,
            exit_code=9,
            stderr_text="Uncatalogued GF failure text\n",
        )
    )
    primary = _primary(result)

    assert _status(result) is ValidationStatus.OK
    assert primary is not None
    assert _pattern_id(primary) in {"DP-FALLBACK-001", "DP-FALLBACK-002"}
    assert getattr(result, "unknown_failure_output") is True


def test_strict_truncated_evidence_is_not_reported_as_complete(
    tmp_path: Path,
) -> None:
    result = parse_diagnostics(
        _evidence(
            tmp_path,
            exit_code=1,
            stderr_text="Syntax error: Unexpected token\n",
            strict=True,
            stderr_truncated=True,
        )
    )

    assert _status(result) is ValidationStatus.ERROR
    assert getattr(result, "parse_complete") is False
    assert getattr(result, "stderr_truncated") is True
    assert any("truncated" in text for text in _warning_texts(result))


def test_parser_output_is_deterministic_for_identical_evidence(
    tmp_path: Path,
) -> None:
    evidence = _evidence(
        tmp_path,
        exit_code=1,
        stderr_text=(
            "Syntax error: Unexpected token\n"
            "Syntax error: Unexpected token\n"
        ),
    )

    first = parse_diagnostics(evidence)
    second = parse_diagnostics(evidence)

    assert first == second
    assert tuple(getattr(item, "record_id") for item in _records(first)) == tuple(
        getattr(item, "record_id") for item in _records(second)
    )


def test_parser_contains_pattern_provider_failures(
    tmp_path: Path,
) -> None:
    def broken_provider(evidence: DiagnosticEvidence) -> tuple[()]:
        del evidence
        raise RuntimeError("provider detail must not escape")

    service = DiagnosticParsingService(pattern_provider=broken_provider)
    result = service.parse(_evidence(tmp_path, exit_code=1))

    assert _status(result) is ValidationStatus.ERROR
    assert getattr(result, "parse_complete") is False
    assert _records(result) == ()
    assert any("RuntimeError" in text for text in _warning_texts(result))
    assert all("provider detail" not in text for text in _warning_texts(result))


def test_parser_does_not_launch_tools_or_read_stream_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(subprocess, "run", _fail_if_called)
    monkeypatch.setattr(subprocess, "Popen", _fail_if_called)
    monkeypatch.setattr(Path, "read_text", _fail_if_called)
    monkeypatch.setattr(Path, "read_bytes", _fail_if_called)

    result = parse_diagnostics(
        _evidence(
            tmp_path,
            exit_code=1,
            stderr_text="Syntax error: Unexpected token\n",
        )
    )

    assert _status(result) is ValidationStatus.OK
    assert _primary(result) is not None


def test_classifier_assigns_ok_direct_downstream_ambiguous_and_skipped() -> None:
    provider = _DiagnosticResult(
        subject_id="project/Provider.gf",
        status=ValidationStatus.FAIL,
        error_kind=ErrorKind.TYPE,
        primary_message="local type error",
    )
    consumer = _DiagnosticResult(
        subject_id="project/Consumer.gf",
        status=ValidationStatus.FAIL,
        error_kind=ErrorKind.OTHER,
        primary_message="consumer failed",
    )
    unknown = _DiagnosticResult(
        subject_id="project/Unknown.gf",
        status=ValidationStatus.ERROR,
        error_kind=ErrorKind.TOOL,
        primary_message="global tool failure",
    )
    successful = _DiagnosticResult(
        subject_id="project/Healthy.gf",
        status=ValidationStatus.OK,
        error_kind=ErrorKind.OK,
        primary_message="",
    )
    skipped = _DiagnosticResult(
        subject_id="project/Skipped.gf",
        status=ValidationStatus.SKIPPED,
        error_kind=ErrorKind.OK,
        primary_message="",
    )

    batch = ClassificationService(strict=True).classify(
        (consumer, unknown, provider, successful, skipped),
        references_by_subject={
            consumer.subject_id: (provider.subject_id,),
        },
    )
    classified = {item.subject_id: item for item in batch.results}

    assert batch.ok
    assert classified[provider.subject_id].diagnostic_class is DiagnosticClass.DIRECT
    assert classified[provider.subject_id].is_direct is True
    assert classified[consumer.subject_id].diagnostic_class is DiagnosticClass.DOWNSTREAM
    assert classified[consumer.subject_id].blocked_by == (provider.subject_id,)
    assert classified[unknown.subject_id].diagnostic_class is DiagnosticClass.AMBIGUOUS
    assert classified[successful.subject_id].diagnostic_class is DiagnosticClass.OK
    assert classified[skipped.subject_id].diagnostic_class is DiagnosticClass.SKIPPED


def test_classifier_orders_multiple_root_blockers_deterministically() -> None:
    alpha = _DiagnosticResult(
        subject_id="project/Alpha.gf",
        status=ValidationStatus.FAIL,
        error_kind=ErrorKind.SYNTAX,
        primary_message="syntax error",
    )
    zeta = _DiagnosticResult(
        subject_id="project/Zeta.gf",
        status=ValidationStatus.FAIL,
        error_kind=ErrorKind.TYPE,
        primary_message="type error",
    )
    consumer = _DiagnosticResult(
        subject_id="project/Consumer.gf",
        status=ValidationStatus.FAIL,
        error_kind=ErrorKind.OTHER,
        primary_message="blocked",
    )

    service = ClassificationService(strict=True)
    forward = service.classify(
        (consumer, zeta, alpha),
        references_by_subject={
            consumer.subject_id: (zeta.subject_id, alpha.subject_id),
        },
    )
    reverse = service.classify(
        (alpha, consumer, zeta),
        references_by_subject={
            consumer.subject_id: (alpha.subject_id, zeta.subject_id),
        },
    )

    forward_consumer = next(
        item for item in forward.results if item.subject_id == consumer.subject_id
    )
    reverse_consumer = next(
        item for item in reverse.results if item.subject_id == consumer.subject_id
    )
    expected = (alpha.subject_id, zeta.subject_id)

    assert forward_consumer.blocked_by == expected
    assert reverse_consumer.blocked_by == expected


def test_classifier_preserves_status_and_raw_error_kind() -> None:
    result = _DiagnosticResult(
        subject_id="project/Main.gf",
        status=ValidationStatus.FAIL,
        error_kind=ErrorKind.SYNTAX,
        primary_message="Syntax error",
    )

    classified = ClassificationService(strict=True).classify((result,)).results[0]

    assert classified.status is result.status
    assert classified.error_kind is result.error_kind
    assert classified.primary_message == result.primary_message
    assert classified.diagnostic_class is DiagnosticClass.DIRECT


def test_classifier_supports_explicit_scan_noise_without_relabeling_failures() -> None:
    noise = _DiagnosticResult(
        subject_id="project/generated/Noise.gf",
        status=ValidationStatus.SKIPPED,
        error_kind=ErrorKind.OK,
        primary_message="",
    )

    classified = ClassificationService(strict=True).classify(
        (noise,),
        noise_subjects=(noise.subject_id,),
    ).results[0]

    assert classified.status is ValidationStatus.SKIPPED
    assert classified.error_kind is ErrorKind.OK
    assert classified.diagnostic_class is DiagnosticClass.NOISE
    assert classified.blocked_by == ()


def test_classifier_does_not_launch_external_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(subprocess, "run", _fail_if_called)
    monkeypatch.setattr(subprocess, "Popen", _fail_if_called)
    result = _DiagnosticResult(
        subject_id="project/Main.gf",
        status=ValidationStatus.FAIL,
        error_kind=ErrorKind.TYPE,
        primary_message="type error",
    )

    classified = ClassificationService(strict=True).classify((result,)).results[0]

    assert classified.diagnostic_class is DiagnosticClass.DIRECT


@pytest.mark.parametrize(
    "result",
    (
        _DiagnosticResult(
            subject_id="project/InvalidOk.gf",
            status=ValidationStatus.OK,
            error_kind=ErrorKind.OK,
            primary_message="",
            diagnostic_class=DiagnosticClass.AMBIGUOUS,
        ),
        _DiagnosticResult(
            subject_id="project/InvalidDownstream.gf",
            status=ValidationStatus.FAIL,
            error_kind=ErrorKind.TYPE,
            primary_message="failure",
            diagnostic_class=DiagnosticClass.DOWNSTREAM,
            blocked_by=(),
        ),
        _DiagnosticResult(
            subject_id="project/InvalidDirect.gf",
            status=ValidationStatus.FAIL,
            error_kind=ErrorKind.TYPE,
            primary_message="failure",
            diagnostic_class=DiagnosticClass.DIRECT,
            blocked_by=("project/Other.gf",),
            is_direct=True,
        ),
    ),
)
def test_classification_coherence_rejects_invalid_relationship_fields(
    result: _DiagnosticResult,
) -> None:
    with pytest.raises(ContractViolationError):
        enforce_classification_coherence(result)
