from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, fields
from enum import StrEnum
import importlib.util
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
from types import ModuleType

import pytest

from gf_wordbench.validation.scanning.masking import SourceViews

_COUNT_FIELDS = (
    "single_slash_eq",
    "double_slash_dash",
    "runtime_str_match",
    "untyped_case_str_pat",
    "untyped_table_str_pat",
    "trailing_spaces",
)


class _CompletionState(StrEnum):
    COMPLETED = "completed"


class _EncodingOutcome(StrEnum):
    UTF8 = "utf8"
    UTF8_BOM = "utf8_bom"
    UTF8_REPLACEMENT = "utf8_replacement"


@dataclass(frozen=True, slots=True)
class _Counts:
    single_slash_eq: int = 0
    double_slash_dash: int = 0
    runtime_str_match: int = 0
    untyped_case_str_pat: int = 0
    untyped_table_str_pat: int = 0
    trailing_spaces: int = 0


@dataclass(frozen=True, slots=True)
class _Diagnostic:
    code: str
    message: str
    line: int | None = None


@dataclass(frozen=True, slots=True)
class _Finding:
    rule_id: str
    count_field: str
    source_path: Path
    start_line: int
    end_line: int
    excerpt: str
    message: str


@dataclass(frozen=True, slots=True)
class _Request:
    source_path: Path
    project_relative_path: PurePosixPath
    evidence_path: Path
    rule_set_id: str
    max_source_bytes: int = 1_000_000
    allow_lossy_decode: bool = False
    fingerprint_reference: str | None = None


@dataclass(frozen=True, slots=True)
class _Result:
    completion_state: _CompletionState
    counts: _Counts
    findings: tuple[_Finding, ...]
    diagnostics: tuple[_Diagnostic, ...]
    fingerprint_reference: str | None
    evidence_path: Path
    rule_set_id: str
    rule_set_version: str
    encoding_outcome: _EncodingOutcome
    source_size_bytes: int


RuleScanner = Callable[..., tuple[_Finding, ...]]


@dataclass(frozen=True, slots=True)
class _Rule:
    rule_id: str
    count_field: str
    scanner: RuleScanner

    def scan(
        self,
        views: SourceViews,
        *,
        source_path: Path,
        project_relative_path: PurePosixPath,
    ) -> tuple[_Finding, ...]:
        return self.scanner(
            views,
            source_path=source_path,
            project_relative_path=project_relative_path,
        )


@dataclass(frozen=True, slots=True)
class _Registry:
    rule_set_id: str
    rule_set_version: str
    rules: tuple[_Rule, ...]


def _line_scanner(
    rule_id: str,
    count_field: str,
    token: str,
) -> RuleScanner:
    def scan(
        views: SourceViews,
        *,
        source_path: Path,
        project_relative_path: PurePosixPath,
    ) -> tuple[_Finding, ...]:
        del source_path
        original = str(views.original)
        findings: list[_Finding] = []
        for line_number, line in enumerate(original.splitlines(), start=1):
            if token not in line:
                continue
            findings.append(
                _Finding(
                    rule_id=rule_id,
                    count_field=count_field,
                    source_path=Path(project_relative_path.as_posix()),
                    start_line=line_number,
                    end_line=line_number,
                    excerpt=line,
                    message=f"matched {token}",
                )
            )
        return tuple(findings)

    return scan


def _canonical_registry() -> _Registry:
    rules = tuple(
        _Rule(
            rule_id=rule_id,
            count_field=count_field,
            scanner=_line_scanner(rule_id, count_field, f"<{count_field}>"),
        )
        for rule_id, count_field in zip(
            (
                "SCAN-NOTATION-001",
                "SCAN-NOTATION-002",
                "SCAN-RUNTIME-001",
                "SCAN-PATTERN-001",
                "SCAN-PATTERN-002",
                "SCAN-STYLE-001",
            ),
            _COUNT_FIELDS,
            strict=True,
        )
    )
    return _Registry(
        rule_set_id="gf-wordbench.static-scanning",
        rule_set_version="2.0.0",
        rules=rules,
    )


def _patch_service_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[ModuleType, ModuleType]:
    import gf_wordbench.validation.scanning.models as models
    import gf_wordbench.validation.scanning.registry as registry

    replacements: dict[str, object] = {
        "ScanCompletionState": _CompletionState,
        "ScanCounts": _Counts,
        "ScanDiagnostic": _Diagnostic,
        "ScanEncodingOutcome": _EncodingOutcome,
        "ScanFinding": _Finding,
        "StaticScanRequest": _Request,
        "StaticScanResult": _Result,
    }
    for name, value in replacements.items():
        monkeypatch.setattr(models, name, value, raising=False)

    monkeypatch.setattr(registry, "ScanRule", _Rule, raising=False)
    monkeypatch.setattr(registry, "ScanRuleRegistry", _Registry, raising=False)
    monkeypatch.setattr(
        registry,
        "CANONICAL_SCAN_RULE_REGISTRY",
        _canonical_registry(),
        raising=False,
    )
    return models, registry


def _load_service(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    _patch_service_dependencies(monkeypatch)
    spec = importlib.util.find_spec("gf_wordbench.validation.scanning.service")
    assert spec is not None
    assert spec.origin is not None
    alias = "gf_wordbench.validation.scanning._service_unit_under_test"
    module_spec = importlib.util.spec_from_file_location(alias, spec.origin)
    assert module_spec is not None
    assert module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[alias] = module
    try:
        module_spec.loader.exec_module(module)
    finally:
        sys.modules.pop(alias, None)
    return module


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> Iterator[ModuleType]:
    yield _load_service(monkeypatch)


def _request(
    tmp_path: Path,
    *,
    source_name: str = "Sample.gf",
    evidence_name: str = "evidence/static_scan/Sample.scan.txt",
    max_source_bytes: int = 1_000_000,
    allow_lossy_decode: bool = False,
    fingerprint_reference: str | None = "sha256:source",
) -> _Request:
    return _Request(
        source_path=tmp_path / source_name,
        project_relative_path=PurePosixPath("src") / source_name,
        evidence_path=tmp_path / evidence_name,
        rule_set_id="gf-wordbench.static-scanning",
        max_source_bytes=max_source_bytes,
        allow_lossy_decode=allow_lossy_decode,
        fingerprint_reference=fingerprint_reference,
    )


def test_service_imports_against_the_canonical_scanning_modules() -> None:
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            "import gf_wordbench.validation.scanning.service",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert process.returncode == 0, process.stderr


def test_static_scan_error_validates_identity_and_preserves_context(
    service: ModuleType,
    tmp_path: Path,
) -> None:
    source = tmp_path / "Source.gf"
    evidence = tmp_path / "Source.scan.txt"
    cause = OSError("disk failure")

    error = service.StaticScanError(
        "GF-WB-SCAN-007",
        "Evidence write failed.",
        source_path=source,
        evidence_path=evidence,
        cause=cause,
    )

    assert str(error) == "Evidence write failed."
    assert error.code == "GF-WB-SCAN-007"
    assert error.source_path == source
    assert error.evidence_path == evidence
    assert error.cause is cause
    with pytest.raises(ValueError, match="code"):
        service.StaticScanError("", "message")
    with pytest.raises(ValueError, match="message"):
        service.StaticScanError("GF-WB-SCAN-001", " ")


def test_scan_text_runs_all_rules_and_orders_findings_deterministically(
    service: ModuleType,
) -> None:
    source = "\n".join(
        (
            "<trailing_spaces>",
            "<single_slash_eq>",
            "<runtime_str_match>",
            "<single_slash_eq>",
            "<untyped_table_str_pat>",
        )
    )

    counts, findings, diagnostics = service.scan_text(
        source,
        project_relative_path="grammar\\Sample.gf",
        registry=_canonical_registry(),
    )

    assert counts == _Counts(
        single_slash_eq=2,
        runtime_str_match=1,
        untyped_table_str_pat=1,
        trailing_spaces=1,
    )
    assert tuple(finding.count_field for finding in findings) == (
        "single_slash_eq",
        "single_slash_eq",
        "runtime_str_match",
        "untyped_table_str_pat",
        "trailing_spaces",
    )
    assert tuple(finding.start_line for finding in findings) == (2, 4, 3, 5, 1)
    assert diagnostics == ()


def test_canonical_scan_text_bounds_long_pattern_evidence() -> None:
    from gf_wordbench.validation.scanning.service import scan_text

    source = (
        "lin x = case y of {\n"
        + '  "a" + _ => "'
        + ("z" * 3_000)
        + '" ;\n}\n'
    )

    counts, findings, diagnostics = scan_text(
        source,
        project_relative_path="LongPattern.gf",
    )

    pattern_findings = tuple(
        finding for finding in findings if finding.rule_id == "SCAN-PATTERN-001"
    )
    assert counts.untyped_case_str_pat == 1
    assert len(pattern_findings) == 1
    assert len(pattern_findings[0].excerpt) == 240
    assert pattern_findings[0].excerpt.endswith("…")
    assert diagnostics == ()


def test_scan_text_rejects_invalid_input_path_and_registry_identity(
    service: ModuleType,
) -> None:
    with pytest.raises(TypeError, match="source_text"):
        service.scan_text(
            b"resource",
            project_relative_path="src/Sample.gf",
        )
    for path in ("", ".", "/absolute.gf", "../escape.gf", "src/not_gf.txt"):
        with pytest.raises((TypeError, ValueError)):
            service.scan_text("resource", project_relative_path=path)

    registry = _canonical_registry()
    with pytest.raises(ValueError, match="rule_set_id"):
        service.scan_text(
            "resource",
            project_relative_path="src/Sample.gf",
            rule_set_id="different-rule-set",
            registry=registry,
        )


def test_scan_file_empty_utf8_source_creates_complete_lf_log(
    service: ModuleType,
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    request.source_path.write_bytes(b"")

    result = service.scan_file(request, registry=_canonical_registry())

    assert result.completion_state is _CompletionState.COMPLETED
    assert result.encoding_outcome is _EncodingOutcome.UTF8
    assert result.source_size_bytes == 0
    assert result.counts == _Counts()
    assert result.findings == ()
    assert result.fingerprint_reference == "sha256:source"
    assert request.source_path.read_bytes() == b""
    log_bytes = request.evidence_path.read_bytes()
    assert log_bytes.endswith(b"\n")
    assert b"\r" not in log_bytes
    log = log_bytes.decode("utf-8")
    assert "completion_state: completed" in log
    assert "encoding_outcome: utf8" in log
    assert "Findings" in log
    assert "Diagnostics\nnone\n" in log


def test_scan_file_accepts_utf8_bom_and_never_mutates_source(
    service: ModuleType,
    tmp_path: Path,
) -> None:
    request = _request(tmp_path, source_name="Source with spaces.gf")
    original = b"\xef\xbb\xbfresource Demo = {\n<single_slash_eq>\n}\n"
    request.source_path.write_bytes(original)

    result = service.scan_file(request, registry=_canonical_registry())

    assert result.encoding_outcome is _EncodingOutcome.UTF8_BOM
    assert result.counts.single_slash_eq == 1
    assert result.source_size_bytes == len(original)
    assert request.source_path.read_bytes() == original
    assert request.evidence_path.is_file()


def test_scan_file_rejects_invalid_utf8_in_strict_mode(
    service: ModuleType,
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    request.source_path.write_bytes(b"resource \xff")

    with pytest.raises(service.StaticScanError) as captured:
        service.scan_file(request, registry=_canonical_registry())

    assert captured.value.code == "GF-WB-SCAN-005"
    assert isinstance(captured.value.cause, UnicodeDecodeError)
    assert not request.evidence_path.exists()


def test_scan_file_records_lossy_decoding_explicitly(
    service: ModuleType,
    tmp_path: Path,
) -> None:
    request = _request(tmp_path, allow_lossy_decode=True)
    request.source_path.write_bytes(b"resource \xff\n")

    result = service.scan_file(request, registry=_canonical_registry())

    assert result.encoding_outcome is _EncodingOutcome.UTF8_REPLACEMENT
    assert len(result.diagnostics) == 1
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == "GF-WB-SCAN-ENCODING-001"
    assert "lossy" in diagnostic.message
    assert "encoding_outcome: utf8_replacement" in request.evidence_path.read_text(encoding="utf-8")


def test_scan_file_reports_missing_non_regular_and_oversized_sources(
    service: ModuleType,
    tmp_path: Path,
) -> None:
    missing = _request(tmp_path, source_name="Missing.gf")
    with pytest.raises(service.StaticScanError) as captured:
        service.scan_file(missing, registry=_canonical_registry())
    assert captured.value.code == "GF-WB-SCAN-001"

    directory_request = _request(tmp_path, source_name="Directory.gf")
    directory_request.source_path.mkdir()
    with pytest.raises(service.StaticScanError) as captured:
        service.scan_file(directory_request, registry=_canonical_registry())
    assert captured.value.code == "GF-WB-SCAN-002"

    oversized = _request(
        tmp_path,
        source_name="Large.gf",
        max_source_bytes=3,
    )
    oversized.source_path.write_bytes(b"1234")
    with pytest.raises(service.StaticScanError) as captured:
        service.scan_file(oversized, registry=_canonical_registry())
    assert captured.value.code == "GF-WB-SCAN-003"


def test_scan_file_rejects_symbolic_link_sources_when_supported(
    service: ModuleType,
    tmp_path: Path,
) -> None:
    target = tmp_path / "Target.gf"
    target.write_text("resource Target = {}\n", encoding="utf-8")
    request = _request(tmp_path, source_name="Link.gf")
    try:
        request.source_path.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("symbolic links are unavailable")

    with pytest.raises(service.StaticScanError) as captured:
        service.scan_file(request, registry=_canonical_registry())

    assert captured.value.code == "GF-WB-SCAN-002"
    assert target.read_text(encoding="utf-8") == "resource Target = {}\n"


def test_scan_file_wraps_rule_failures_with_rule_identity(
    service: ModuleType,
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    request.source_path.write_text("resource Demo = {}\n", encoding="utf-8")

    def explode(*args: object, **kwargs: object) -> tuple[_Finding, ...]:
        del args, kwargs
        raise RuntimeError("scanner exploded")

    rules = list(_canonical_registry().rules)
    rules[2] = _Rule(
        rule_id=rules[2].rule_id,
        count_field=rules[2].count_field,
        scanner=explode,
    )
    registry = _Registry(
        rule_set_id="gf-wordbench.static-scanning",
        rule_set_version="2.0.0",
        rules=tuple(rules),
    )

    with pytest.raises(service.StaticScanError) as captured:
        service.scan_file(request, registry=registry)

    assert captured.value.code == "GF-WB-SCAN-006"
    assert "SCAN-RUNTIME-001" in str(captured.value)
    assert isinstance(captured.value.cause, RuntimeError)
    assert not request.evidence_path.exists()


def test_scan_file_rejects_invalid_rule_output(
    service: ModuleType,
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    request.source_path.write_text("resource Demo = {}\n", encoding="utf-8")

    def invalid(*args: object, **kwargs: object) -> tuple[object, ...]:
        del args, kwargs
        return (object(),)

    rules = list(_canonical_registry().rules)
    rules[0] = _Rule(
        rule_id=rules[0].rule_id,
        count_field=rules[0].count_field,
        scanner=invalid,  # type: ignore[arg-type]
    )
    registry = _Registry(
        rule_set_id="gf-wordbench.static-scanning",
        rule_set_version="2.0.0",
        rules=tuple(rules),
    )

    with pytest.raises(service.StaticScanError) as captured:
        service.scan_file(request, registry=registry)

    assert captured.value.code == "GF-WB-SCAN-006"
    assert "invalid finding" in str(captured.value)


def test_evidence_replacement_is_atomic_and_cleans_temporary_file(
    service: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    request.source_path.write_text("resource Demo = {}\n", encoding="utf-8")
    request.evidence_path.parent.mkdir(parents=True)
    request.evidence_path.write_text("previous\n", encoding="utf-8")

    def fail_replace(source: os.PathLike[str], destination: os.PathLike[str]) -> None:
        del source, destination
        raise OSError("replace denied")

    monkeypatch.setattr(service.os, "replace", fail_replace)

    with pytest.raises(service.StaticScanError) as captured:
        service.scan_file(request, registry=_canonical_registry())

    assert captured.value.code == "GF-WB-SCAN-007"
    assert request.evidence_path.read_text(encoding="utf-8") == "previous\n"
    assert tuple(request.evidence_path.parent.glob("*.tmp")) == ()


def test_render_scan_log_uses_registry_and_count_field_order(
    service: ModuleType,
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    finding = _Finding(
        rule_id="SCAN-NOTATION-001",
        count_field="single_slash_eq",
        source_path=Path("src/Sample.gf"),
        start_line=4,
        end_line=5,
        excerpt="x" * 400,
        message="suspicious notation",
    )
    result = _Result(
        completion_state=_CompletionState.COMPLETED,
        counts=_Counts(single_slash_eq=1),
        findings=(finding,),
        diagnostics=(
            _Diagnostic("GF-WB-SCAN-900", "later", None),
            _Diagnostic("GF-WB-SCAN-100", "earlier", 2),
        ),
        fingerprint_reference=None,
        evidence_path=request.evidence_path,
        rule_set_id="gf-wordbench.static-scanning",
        rule_set_version="2.0.0",
        encoding_outcome=_EncodingOutcome.UTF8,
        source_size_bytes=42,
    )

    rendered = service.render_scan_log(
        request,
        result,
        registry=_canonical_registry(),
    )

    positions = [rendered.index(f"{field_name}:") for field_name in _COUNT_FIELDS]
    assert positions == sorted(positions)
    assert "line: 4-5" in rendered
    assert "excerpt: " + "x" * 239 + "…" in rendered
    assert rendered.endswith("\n")
    assert "\r" not in rendered


def test_request_and_registry_validation_fail_closed(
    service: ModuleType,
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    same_path = _Request(
        source_path=request.source_path,
        project_relative_path=request.project_relative_path,
        evidence_path=request.source_path,
        rule_set_id=request.rule_set_id,
    )
    with pytest.raises(ValueError, match="different"):
        service.scan_file(same_path, registry=_canonical_registry())

    with pytest.raises(TypeError, match="StaticScanRequest"):
        service.scan_file(object(), registry=_canonical_registry())

    registry = _canonical_registry()
    duplicated = _Registry(
        rule_set_id=registry.rule_set_id,
        rule_set_version=registry.rule_set_version,
        rules=(registry.rules[0], registry.rules[0], *registry.rules[2:]),
    )
    request.source_path.write_text("resource Demo = {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        service.scan_file(request, registry=duplicated)

    wrong_order = _Registry(
        rule_set_id=registry.rule_set_id,
        rule_set_version=registry.rule_set_version,
        rules=(registry.rules[1], registry.rules[0], *registry.rules[2:]),
    )
    with pytest.raises(ValueError, match="order"):
        service.scan_file(request, registry=wrong_order)


def test_public_service_exports_are_exact(service: ModuleType) -> None:
    assert service.__all__ == (
        "StaticScanError",
        "render_scan_log",
        "scan_file",
        "scan_text",
    )
    assert tuple(field.name for field in fields(_Counts)) == _COUNT_FIELDS
