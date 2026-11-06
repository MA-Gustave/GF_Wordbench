"""Static and simulated tests for the three GF 3.12 diagnostic fixes."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest
from gf_wordbench.practical.alignment14 import PILOTS, read_policy
from gf_wordbench.practical.pilot import _validate_pilot
from gf_wordbench.practical import stabilization023


def test_three_diagnostic_fixes_and_14_language_scope():
    assert stabilization023.selected_changes()=={
        'Afr':('obligation','possibility'),
        'Por':('conditional-instruction',),
    }
    assert len(read_policy()['languages'])==14
    assert sum(_validate_pilot(l)['scenario_count'] for l in read_policy()['languages'])==210


def test_source_locks_and_lineage():
    p=json.loads((PILOTS/'lexical_stabilization_focus14_v023.json').read_text(encoding='utf8'))
    assert p['schema_version']=='0.2.3' and p['gold_approved'] is False
    assert p['scenarios_patched']==len(p['changes'])==3
    for c in p['changes']:
        root=PILOTS/c['lang']
        manifest=json.loads((root/'pilot_manifest.json').read_text(encoding='utf8'))
        row=next(r for r in manifest['scenarios'] if r['id']==c['scenario'])
        source=root/'validation/inputs'/row['module']
        script=root/row['script']
        assert hashlib.sha256(source.read_bytes()).hexdigest()==c['source_sha256']==row['source_sha256']
        assert hashlib.sha256(script.read_bytes()).hexdigest()==c['script_sha256']==row['script_sha256']
        assert c['previous_sha256'] != c['source_sha256']
        assert c['source_sha256'] in script.read_text(encoding='utf8')
        assert manifest['gold_approved'] is False


def test_proposed_repair_constructs_and_inherited_parameters():
    afr=PILOTS/'Afr'/'validation'/'inputs'
    po=PILOTS/'Por'/'validation'/'inputs'
    obligation=(afr/'DefluensObligationAfr.gf').read_text(encoding='utf8')
    possibility=(afr/'DefluensPossibilityAfr.gf').read_text(encoding='utf8')
    portuguese=(po/'DefluensConditionalInstructionPor.gf').read_text(encoding='utf8')
    assert 'youSg_Pron.stressed.nom' in obligation
    assert 'obligModal.s ! VPres' in obligation and 'obligWait.s ! VInf' in obligation
    assert 'possModal.s ! VPres' in possibility and 'possReturn.s ! VInf' in possibility
    assert 'mkPN "Mira"' not in possibility
    for x in ['CommonRomance','C.Sg C.P3','B.chegar_Besch','B.Fut B.Sub']:
        assert x in portuguese
    assert 'Mira kan terugkeer' not in possibility
    assert 'jy moet wag' not in obligation


def test_new_runner_simulated_zip(tmp_path,monkeypatch):
    calls=[]
    def run(lang,*,scenarios,**kwargs):
        calls.append((lang,tuple(scenarios)))
        return {'run_id':lang,'scenarios':[{'id':s,'candidate':'simulated'} for s in scenarios],
            'totals':{'candidate_for_review':len(scenarios),'probe_failed':0,'timeout':0,'unverified':0}}
    monkeypatch.setattr(stabilization023,'run_pilot',run)
    report=stabilization023.run_changed(gf=tmp_path/'gf',rgl=tmp_path/'rgl',output_root=tmp_path/'out')
    assert report['status']=='completed_candidates_only'
    assert report['expected_changes']==3
    assert report['totals']['candidate_for_review']==3
    assert len(calls)==2
    assert report['gold_approved'] is False and report['semantic_coverage_verified'] is False
    with ZipFile(report['archive_path']) as archive:
        summary=json.loads(archive.read(next(n for n in archive.namelist() if n.endswith('stabilization_summary.json'))))
    assert summary['schema_version']=='0.2.3'


def test_runner_marks_failures_and_keeps_zip(tmp_path,monkeypatch):
    def run(lang,*,scenarios,**kwargs):
        if lang=='Afr':
            raise RuntimeError('simulated error')
        return {'run_id':lang,'scenarios':[{'id':s,'candidate':'simulated'} for s in scenarios],
            'totals':{'candidate_for_review':len(scenarios),'probe_failed':0,'timeout':0,'unverified':0}}
    monkeypatch.setattr(stabilization023,'run_pilot',run)
    report=stabilization023.run_changed(gf=tmp_path/'gf',rgl=tmp_path/'rgl',output_root=tmp_path/'out')
    assert report['status']=='completed_with_failures'
    assert 'Por' in report['languages']
    assert Path(report['archive_path']).exists()
