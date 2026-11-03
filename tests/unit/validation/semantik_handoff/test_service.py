import hashlib
import json
from pathlib import Path
import zipfile

from gf_wordbench.validation.semantik_handoff import inspect_semantik_handoff, materialize_verified_handoff


def _bundle(tmp_path: Path, *, tamper: bool = False, surface_tamper: bool = False) -> Path:
    root = tmp_path / "bundle"
    (root / "evidence").mkdir(parents=True)
    report = root / "evidence" / "report.json"
    source = {
        "status": "PASS",
        "migration_gate": {"status": "PASS"},
        "capability_conformance": {"status": "PASS"},
        "languages": [{
            "rgl_code": "Eng",
            "cases": [
                {"case_id": "a", "plain_text": "A"},
                {"case_id": "b", "plain_text": "B"},
            ],
        }],
    }
    report.write_text(json.dumps(source), encoding="utf-8")
    files = {"evidence/report.json": hashlib.sha256(report.read_bytes()).hexdigest()}
    manifest = {
        "schema": "semantik-wordbench-handoff-v1",
        "producer": {"product": "SemantiK Phrase Ops Console", "version": "0.4.0"},
        "status": "CANDIDATE",
        "release_authorized": False,
        "authority": {"wordbench_required": True, "phrase_ops_release_authority": False},
        "source_report": {"path": "evidence/report.json", "sha256": files["evidence/report.json"]},
        "contract": {
            "baseline_required_operations": ["clause.transitive_event"],
            "extension_operation": "clause.passive_event",
        },
        "summary": {"languages": 1, "technical_cases": 2, "advertised_cases": 1, "disabled_cases": 1},
        "languages": [{
            "rgl_code": "Eng", "bcp47": "en", "concrete": "ProbeEng",
            "extension_capabilities": [],
            "cases": [
                {"case_id": "a", "operation": "clause.transitive_event", "plain_text": "CHANGED" if surface_tamper else "A", "technical_ok": True, "capability_advertised": True},
                {"case_id": "b", "operation": "clause.passive_event", "plain_text": "B", "technical_ok": True, "capability_advertised": False},
            ],
        }],
        "files": files,
    }
    (root / "handoff.json").write_text(json.dumps(manifest), encoding="utf-8")
    if tamper:
        report.write_text('{"status":"CHANGED"}\n', encoding="utf-8")
    out = tmp_path / "handoff.zip"
    with zipfile.ZipFile(out, "w") as zf:
        for p in root.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(root).as_posix())
    return out


def test_inspects_valid_handoff_as_non_release_evidence(tmp_path):
    bundle = _bundle(tmp_path)
    result = inspect_semantik_handoff(bundle)
    assert result.valid
    assert result.release_eligible is False
    assert result.language_count == 1
    assert result.technical_cases == 2
    assert result.advertised_cases == 1


def test_rejects_hash_tamper(tmp_path):
    result = inspect_semantik_handoff(_bundle(tmp_path, tamper=True))
    assert not result.valid
    assert any("sha256" in error or "source_report" in error for error in result.errors)


def test_rejects_surface_not_bound_to_source_report(tmp_path):
    result = inspect_semantik_handoff(_bundle(tmp_path, surface_tamper=True))
    assert not result.valid
    assert any("surface differs from source_report" in error for error in result.errors)


def test_materializes_only_after_verification(tmp_path):
    bundle = _bundle(tmp_path)
    dest = tmp_path / "materialized"
    materialize_verified_handoff(bundle, dest)
    assert (dest / "handoff.json").is_file()
    assert (dest / "evidence" / "report.json").is_file()
