"""Non-GF tests for the seven v0.2.2 proposals and raw/preview isolation."""
from pathlib import Path
import hashlib
import json
from zipfile import ZipFile
import pytest

from gf_wordbench.practical.alignment14 import PILOTS, read_policy
from gf_wordbench.practical.pilot import _validate_pilot
from gf_wordbench.practical import stabilization022, review022


def test_exactly_seven_cases_and_no_new_tenses():
    groups=stabilization022.selected_changes()
    assert groups == {
        'Afr':('past-event','obligation','possibility','prohibition'),
        'Est':('conditional-instruction',),
        'Por':('conditional-instruction','past-event'),
    }
    assert set(groups) <= set(read_policy()['languages'])


def test_all_210_hash_locked():
    assert sum(_validate_pilot(lang)['scenario_count'] for lang in read_policy()['languages'])==210


def test_modification_provenance_and_gf_patterns():
    policy=json.loads((PILOTS/'lexical_stabilization_focus14_v022.json').read_text(encoding='utf8'))
    assert policy['gold_approved'] is False
    later_policy=json.loads((PILOTS/'lexical_stabilization_focus14_v023.json').read_text(encoding='utf8'))
    successors={(c['lang'],c['scenario']):c for c in later_policy['changes']}
    checks={
        ('Afr','past-event'):['anteriorAnt','"aangekom"'],
        ('Afr','obligation'):['"moet"','VInf'],
        ('Afr','possibility'):['"kan"','VInf'],
        ('Afr','prohibition'):['"moenie"','"nie"'],
        ('Est','conditional-instruction'):['SyntaxEst.mkAdv if_Subj','mkImp'],
        ('Por','conditional-instruction'):['B.chegar_Besch','B.VPB','B.Fut','B.Sub'],
        ('Por','past-event'):['RPasse','lin Tense'],
    }
    for e in policy['changes']:
        m=json.loads((PILOTS/e['lang']/'pilot_manifest.json').read_text(encoding='utf8'))
        item=next(s for s in m['scenarios'] if s['id']==e['scenario'])
        source=(PILOTS/e['lang']/'validation/inputs'/item['module']).read_bytes()
        successor=successors.get((e['lang'],e['scenario']))
        assert hashlib.sha256(source).hexdigest()==(successor['source_sha256'] if successor else e['source_sha256'])
        if successor:
            assert successor['previous_sha256']==e['source_sha256']
        assert e['previous_sha256']!=e['source_sha256']
        if not successor:
            assert all(text in source.decode('utf8') for text in checks[(e['lang'],e['scenario'])])
        assert item['gold']=='not-approved'

@pytest.mark.parametrize('raw,expected',[
    ("Mira n' &+ est pas prête","Mira n'est pas prête"),
    ("n' &+ attends pas","n'attends pas"),
    ("sina pead ootam &+ a","sina pead ootama"),
    ("Mira võib naast &+ a","Mira võib naasta"),
    ("Mira porte deux livres","Mira porte deux livres"),
])
def test_gf_join_preview(raw, expected):
    assert review022.render_preview(raw)==expected


def test_full_v021_archive_audit_is_a_provisional_baseline():
    archive=Path('/mnt/data/defluens-batch-full-20261103T202946Z-8615600.zip')
    if not archive.is_file(): pytest.skip('optional previous-run fixture')
    report=review022.audit_archive(archive)
    assert report['totals']['candidate_for_review']==210
    assert report['totals']['exact_baseline_matches']==210
    assert report['totals']['requires_new_ai_review']==0
    assert report['totals']['token_join_previews']==4
    assert report['gold_approved'] is False
    assert report['semantic_coverage_verified'] is False


def test_changed_only_batch_mock_creates_zip(tmp_path,monkeypatch):
    calls=[]
    def fake_run(lang, *, scenarios, **kwargs):
        calls.append((lang,tuple(scenarios)))
        return {'run_id':lang,'scenarios':[{'id':s,'candidate':s} for s in scenarios],
                'totals':{'candidate_for_review':len(scenarios),'probe_failed':0,'timeout':0,'unverified':0}}
    monkeypatch.setattr(stabilization022,'run_pilot',fake_run)
    run=stabilization022.run_changed(gf=tmp_path/'gf.exe',rgl=tmp_path/'rgl',output_root=tmp_path/'out')
    assert run['status']=='completed_candidates_only'
    assert run['expected_changes']==7
    assert run['totals']['candidate_for_review']==7
    assert len(calls)==3
    assert run['semantic_coverage_verified'] is False
    assert run['gold_approved'] is False
    with ZipFile(run['archive_path']) as z:
        summary=json.loads(z.read(next(n for n in z.namelist() if n.endswith('stabilization_summary.json'))))
    assert summary['expected_changes']==7


def test_selected_batch_continues_after_failed_language(tmp_path,monkeypatch):
    def fake_run(lang, *, scenarios, **kwargs):
        if lang=='Est': raise RuntimeError('test exception')
        return {'run_id':lang,'scenarios':[{'id':s,'candidate':'ok'} for s in scenarios],
                'totals':{'candidate_for_review':len(scenarios),'probe_failed':0,'timeout':0,'unverified':0}}
    monkeypatch.setattr(stabilization022,'run_pilot',fake_run)
    run=stabilization022.run_changed(gf=tmp_path/'gf.exe',rgl=tmp_path/'rgl',output_root=tmp_path/'out')
    assert run['status']=='completed_with_failures'
    assert 'Por' in run['languages']
    assert Path(run['archive_path']).is_file()
