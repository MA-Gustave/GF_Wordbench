"""A GF probe campaign cannot bypass SemantiK Architect release conformance."""
from __future__ import annotations
from pathlib import Path
import json
import zipfile
import pytest
from gf_wordbench.practical.semantik_handoff import build_handoff, CROSSWALK


def fixture(tmp_path: Path, *, tamper: bool = False) -> Path:
    zpath=tmp_path/'defluens-batch-full-fixture.zip'
    summary={'schema_id':'defluens.pilot-batch','mode':'full','batch_id':'fixture','entries':[{'language':'Eng'}]}
    scenarios=[{'id':sid,'status':'candidate_for_review','candidate':'Mira arrived',
        'source_sha256':'a'*64,'script_sha256':'b'*64} for sid in CROSSWALK]
    if tamper:scenarios[0]['source_sha256']='not a hash'
    pilot={'language':'Eng','scenarios':scenarios}
    with zipfile.ZipFile(zpath,'w') as z:
        z.writestr('defluens-batch-fixture/batch_summary.json',json.dumps(summary))
        z.writestr('defluens-batch-fixture/languages/defluens-pilot-Eng-fixture/pilot_run.json',json.dumps(pilot))
    return zpath


def test_reports_all_semantic_gaps_without_faking_release(tmp_path):
    report=build_handoff(fixture(tmp_path))
    assert report['scenario_count']==15
    assert report['gf_candidates']==15
    assert report['release_ready'] is False
    assert report['sa_conformance_passed'] is False
    assert report['complete_14_language_workload'] is False
    assert report['source_hashes_reverified'] is False
    assert len([r for r in report['rows'] if r['sa_operation_candidate'] is None])==3


def test_rejects_tampered_source_reference(tmp_path):
    with pytest.raises(ValueError,match='identity'):
        build_handoff(fixture(tmp_path,tamper=True))
