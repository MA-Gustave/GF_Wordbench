"""Fail-closed inspection of SemantiK Phrase Ops candidate handoff bundles.

The handoff is *input* to Wordbench validation. It is never release evidence by
itself and never creates golds, PGF release decisions, or linguistic verdicts.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
from typing import Any, Mapping
import zipfile

HANDOFF_SCHEMA = "semantik-wordbench-handoff-v1"
MANIFEST_NAME = "handoff.json"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_rel(value: str) -> str:
    p = PurePosixPath(value)
    if not value or p.is_absolute() or ".." in p.parts or value.startswith(("/", "\\")):
        raise ValueError(f"unsafe handoff path: {value!r}")
    return p.as_posix()


@dataclass(frozen=True, slots=True)
class SemantikHandoffInspection:
    valid: bool
    schema: str
    producer_version: str
    language_count: int
    technical_cases: int
    advertised_cases: int
    disabled_cases: int
    source_report_sha256: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    release_eligible: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "gf-wordbench-semantik-handoff-inspection-v1",
            "valid": self.valid,
            "handoff_schema": self.schema,
            "producer_version": self.producer_version,
            "language_count": self.language_count,
            "technical_cases": self.technical_cases,
            "advertised_cases": self.advertised_cases,
            "disabled_cases": self.disabled_cases,
            "source_report_sha256": self.source_report_sha256,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "release_eligible": False,
            "decision": "ACCEPTED_FOR_WORDBENCH_VALIDATION" if self.valid else "REJECTED",
            "authority_note": (
                "Candidate handoff only. Wordbench must reproduce the GF/scenario evidence; "
                "this inspection cannot establish linguistic correctness or release readiness."
            ),
        }


class _BundleReader:
    def __init__(self, source: Path):
        self.source = source.resolve()
        self._zip: zipfile.ZipFile | None = None
        if self.source.is_file():
            self._zip = zipfile.ZipFile(self.source, "r")
        elif not self.source.is_dir():
            raise ValueError(f"handoff source not found: {self.source}")

    def close(self) -> None:
        if self._zip is not None:
            self._zip.close()

    def names(self) -> set[str]:
        if self._zip is not None:
            return {_safe_rel(i.filename) for i in self._zip.infolist() if not i.is_dir()}
        return {
            p.relative_to(self.source).as_posix()
            for p in self.source.rglob("*") if p.is_file()
        }

    def read(self, rel: str) -> bytes:
        rel = _safe_rel(rel)
        if self._zip is not None:
            try:
                return self._zip.read(rel)
            except KeyError as exc:
                raise FileNotFoundError(rel) from exc
        path = (self.source / rel).resolve()
        if not path.is_relative_to(self.source):
            raise ValueError(f"handoff path escapes root: {rel}")
        return path.read_bytes()


def inspect_semantik_handoff(source: str | Path) -> SemantikHandoffInspection:
    reader = _BundleReader(Path(source))
    errors: list[str] = []
    warnings: list[str] = []
    manifest: Mapping[str, Any] = {}
    try:
        names = reader.names()
        if MANIFEST_NAME not in names:
            raise ValueError(f"missing {MANIFEST_NAME}")
        try:
            raw = json.loads(reader.read(MANIFEST_NAME).decode("utf-8"))
        except Exception as exc:
            raise ValueError(f"invalid {MANIFEST_NAME}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError("handoff manifest must be a JSON object")
        manifest = raw
        if manifest.get("schema") != HANDOFF_SCHEMA:
            errors.append(f"unsupported schema: {manifest.get('schema')!r}")
        if manifest.get("status") != "CANDIDATE":
            errors.append("handoff status must be CANDIDATE")
        if manifest.get("release_authorized") is not False:
            errors.append("handoff must explicitly set release_authorized=false")
        authority = manifest.get("authority") or {}
        if not isinstance(authority, dict) or authority.get("wordbench_required") is not True:
            errors.append("authority.wordbench_required must be true")
        if isinstance(authority, dict) and authority.get("phrase_ops_release_authority") is not False:
            errors.append("authority.phrase_ops_release_authority must be false")

        declared_files = manifest.get("files") or {}
        if not isinstance(declared_files, dict) or not declared_files:
            errors.append("files hash map is missing or empty")
            declared_files = {}
        for rel, expected in sorted(declared_files.items()):
            try:
                rel = _safe_rel(str(rel))
                actual = _sha256_bytes(reader.read(rel))
            except Exception as exc:
                errors.append(f"file:{rel}: {type(exc).__name__}: {exc}")
                continue
            if actual != str(expected).lower():
                errors.append(f"sha256:{rel}:expected={expected}:actual={actual}")

        source_report = manifest.get("source_report") or {}
        source_rel = str(source_report.get("path") or "") if isinstance(source_report, dict) else ""
        source_sha = str(source_report.get("sha256") or "") if isinstance(source_report, dict) else ""
        source_payload: Mapping[str, Any] = {}
        if source_rel:
            try:
                source_bytes = reader.read(source_rel)
                source_actual = _sha256_bytes(source_bytes)
                if source_actual != source_sha:
                    errors.append("source_report sha256 mismatch")
                raw_source = json.loads(source_bytes.decode("utf-8"))
                if not isinstance(raw_source, dict):
                    errors.append("source_report must be a JSON object")
                else:
                    source_payload = raw_source
                    if raw_source.get("status") != "PASS":
                        errors.append("source_report status must be PASS")
                    if (raw_source.get("migration_gate") or {}).get("status") != "PASS":
                        errors.append("source_report migration_gate must be PASS")
                    if (raw_source.get("capability_conformance") or {}).get("status") != "PASS":
                        errors.append("source_report capability_conformance must be PASS")
            except Exception as exc:
                errors.append(f"source_report unreadable: {exc}")
        else:
            errors.append("source_report path missing")

        languages = manifest.get("languages") or []
        summary = manifest.get("summary") or {}
        contract = manifest.get("contract") or {}
        baseline_operations = set(
            str(x) for x in (contract.get("baseline_required_operations") or [])
        ) if isinstance(contract, dict) else set()
        if not isinstance(languages, list) or not languages:
            errors.append("languages must be a non-empty list")
            languages = []
        seen_codes: set[str] = set()
        technical = advertised = disabled = 0
        for item in languages:
            if not isinstance(item, dict):
                errors.append("invalid language row")
                continue
            code = str(item.get("rgl_code") or "")
            if not code or code in seen_codes:
                errors.append(f"invalid/duplicate rgl_code: {code!r}")
            seen_codes.add(code)
            cases = item.get("cases") or []
            if not isinstance(cases, list):
                errors.append(f"{code}:cases must be a list")
                continue
            technical += len(cases)
            exts = item.get("extension_capabilities") or []
            if not isinstance(exts, list) or len(exts) != len(set(str(x) for x in exts)):
                errors.append(f"{code}:extension_capabilities invalid")
                exts = []
            extension_set = set(str(x) for x in exts)
            used_extensions: set[str] = set()
            seen_cases: set[str] = set()
            for case in cases:
                if not isinstance(case, dict):
                    errors.append(f"{code}:invalid case row")
                    continue
                case_id = str(case.get("case_id") or "")
                if not case_id or case_id in seen_cases:
                    errors.append(f"{code}:invalid/duplicate case_id: {case_id!r}")
                seen_cases.add(case_id)
                if case.get("technical_ok") is not True:
                    errors.append(f"{code}/{case_id}:technical_ok must be true")
                if not str(case.get("plain_text") or "").strip():
                    errors.append(f"{code}/{case_id}:plain_text must be non-empty")
                operation = str(case.get("operation") or "")
                is_advertised = case.get("capability_advertised") is True
                if is_advertised:
                    advertised += 1
                    if operation and operation not in baseline_operations:
                        if operation not in extension_set:
                            errors.append(f"{code}/{case_id}:advertised operation outside baseline/extensions: {operation}")
                        else:
                            used_extensions.add(operation)
                else:
                    disabled += 1
            unused_extensions = extension_set - used_extensions
            if unused_extensions:
                errors.append(f"{code}:unused extension_capabilities: {sorted(unused_extensions)}")

            source_rows = {
                str(r.get("rgl_code") or ""): r
                for r in (source_payload.get("languages") or [])
                if isinstance(r, dict)
            } if isinstance(source_payload, Mapping) else {}
            source_row = source_rows.get(code)
            if source_row is None:
                errors.append(f"{code}:missing from source_report")
            else:
                source_cases = {
                    str(c.get("case_id") or ""): str(c.get("plain_text") or "")
                    for c in (source_row.get("cases") or [])
                    if isinstance(c, dict)
                }
                for case in cases:
                    if isinstance(case, dict):
                        case_id = str(case.get("case_id") or "")
                        if source_cases.get(case_id) != str(case.get("plain_text") or ""):
                            errors.append(f"{code}/{case_id}:surface differs from source_report")

        if advertised + disabled != technical:
            errors.append("case accounting mismatch: advertised + disabled != technical")
        if isinstance(summary, dict):
            expected = {
                "languages": len(languages),
                "technical_cases": technical,
                "advertised_cases": advertised,
                "disabled_cases": disabled,
            }
            for key, value in expected.items():
                if int(summary.get(key) or -1) != value:
                    errors.append(f"summary.{key} mismatch: {summary.get(key)!r} != {value}")
        else:
            errors.append("summary must be an object")

        warnings.append(
            "SemantiK observed surfaces are candidate evidence only; Wordbench must rerun GF scenarios before release."
        )
        producer = manifest.get("producer") or {}
        producer_version = str(producer.get("version") or "") if isinstance(producer, dict) else ""
        return SemantikHandoffInspection(
            valid=not errors,
            schema=str(manifest.get("schema") or ""),
            producer_version=producer_version,
            language_count=len(languages),
            technical_cases=technical,
            advertised_cases=advertised,
            disabled_cases=disabled,
            source_report_sha256=source_sha,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )
    finally:
        reader.close()


def materialize_verified_handoff(source: str | Path, destination: str | Path) -> Path:
    """Copy/extract a verified handoff for review tooling; never mutates GF sources."""
    inspection = inspect_semantik_handoff(source)
    if not inspection.valid:
        raise ValueError("cannot materialize invalid SemantiK handoff: " + "; ".join(inspection.errors))
    source_path = Path(source).resolve()
    dest = Path(destination).resolve()
    if dest.exists():
        if any(dest.iterdir()):
            raise ValueError(f"destination is not empty: {dest}")
    else:
        dest.mkdir(parents=True)
    if source_path.is_dir():
        for path in source_path.rglob("*"):
            if path.is_file():
                rel = path.relative_to(source_path)
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
    else:
        with zipfile.ZipFile(source_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                rel = _safe_rel(info.filename)
                target = (dest / rel).resolve()
                if not target.is_relative_to(dest):
                    raise ValueError(f"archive path escapes destination: {rel}")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(info))
    return dest


__all__ = [
    "HANDOFF_SCHEMA",
    "SemantikHandoffInspection",
    "inspect_semantik_handoff",
    "materialize_verified_handoff",
]
