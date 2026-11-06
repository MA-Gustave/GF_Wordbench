"""Source-integrity and provenance tests for Defluens lexical stabilization v0.2.1.

A passing test is NOT an actual GF compilation or linguistic certification.
"""
import json
from pathlib import Path

from gf_wordbench.practical.alignment14 import PILOTS, read_policy
from gf_wordbench.practical.pilot import _validate_pilot


def _stabilization():
    return json.loads((PILOTS / 'lexical_stabilization_focus14_v021.json').read_text(encoding='utf8'))


def test_31_patches_focus_with_no_new_tense_scenario():
    plan = _stabilization()
    changes = plan['changes']
    assert plan['scenarios_patched'] == 31
    assert len(changes) == len({(c['lang'], c['scenario']) for c in changes})
    assert set(plan['selected_languages']).issubset(set(read_policy()['languages']))
    assert plan['gold_approved'] is False
    assert set(c['scenario'] for c in changes).issubset({
        'past-event', 'future-reference', 'condition-real', 'temporal-order',
        'past-state', 'quantity', 'conditional-instruction', 'source-attribution'})


def test_all_14_scenarios_remain_hash_locked():
    for lang in read_policy()['languages']:
        assert _validate_pilot(lang)['status'] == 'preflight_ok'
        assert _validate_pilot(lang)['scenario_count'] == 15


def test_applied_sources_match_stabilization_plan():
    for row in _stabilization()['changes']:
        lang, scenario = row['lang'], row['scenario']
        catalog = json.loads((PILOTS / lang / 'pilot_manifest.json').read_text(encoding='utf8'))
        assert catalog['stabilization']['gold_approved'] is False
        entry = next(x for x in catalog['scenarios'] if x['id'] == scenario)
        assert entry['source_sha256'] == row['source_sha256']
        source = (PILOTS / lang / 'validation' / 'inputs' / entry['module']).read_text(encoding='utf8')
        assert 'lexical stabilization v0.2.1' in source
        assert row['previous_sha256'] != row['source_sha256']


def test_irregular_lexemes_and_copula_are_explicit():
    checks = {
        ('Fre', 'past-event'): 'etreV (mkV "arriver")',
        ('Fre', 'future-reference'): 'I.revenir_V',
        ('Ger', 'past-event'): 'I.kommen_V',
        ('Ger', 'quantity'): 'I.tragen_V',
        ('Dut', 'past-event'): 'I.komen_V',
        ('Swe', 'past-event'): '"anländer"',
        ('Nno', 'condition-real'): 'I.komme_V',
        ('Nno', 'quantity'): 'I.bære_V',
        ('Ita', 'past-event'): 'essereV (mkV "arrivare")',
        ('Spa', 'past-state'): 'estarCopula',
        ('Por', 'past-state'): 'estarCopula',
    }
    for (lang, scenario), expected in checks.items():
        manifest = json.loads((PILOTS / lang / 'pilot_manifest.json').read_text(encoding='utf8'))
        entry = next(x for x in manifest['scenarios'] if x['id'] == scenario)
        source = (PILOTS / lang / 'validation' / 'inputs' / entry['module']).read_text(encoding='utf8')
        assert expected in source


def test_no_auto_approved_gold():
    for lang in read_policy()['languages']:
        manifest = json.loads((PILOTS/lang/'pilot_manifest.json').read_text(encoding='utf8'))
        assert not manifest['gold_approved']
        assert all(entry['gold'] == 'not-approved' for entry in manifest['scenarios'])


def test_selected_changed_scenarios_are_unique_and_grouped():
    from gf_wordbench.practical.stabilization021 import selected_changes
    groups = selected_changes()
    assert len(groups) == 10
    assert sum(len(ids) for ids in groups.values()) == 31
    assert len({(lang, sid) for lang, ids in groups.items() for sid in ids}) == 31
    assert all(lang in read_policy()['languages'] for lang in groups)


def test_changed_only_batch_archives_progress_and_does_not_certify(tmp_path, monkeypatch):
    from gf_wordbench.practical import stabilization021 as step
    calls = []
    def fake_run(language, *, scenarios, **kwargs):
        calls.append((language, tuple(scenarios)))
        return {'run_id':f'mock-{language}', 'scenarios':[
            {'id':s, 'candidate':'candidate', 'status':'candidate_for_review'} for s in scenarios],
            'totals':{'candidate_for_review':len(scenarios),'probe_failed':0,'timeout':0,'unverified':0}}
    monkeypatch.setattr(step, 'run_pilot', fake_run)
    result = step.run_changed(gf=tmp_path/'fake-gf.exe',rgl=tmp_path/'rgl',
                              output_root=tmp_path/'out')
    assert result['expected_changes'] == 31
    assert result['status'] == 'completed_candidates_only'
    assert result['totals']['candidate_for_review'] == 31
    assert result['semantic_coverage_verified'] is False
    assert result['gold_approved'] is False
    assert len(calls) == 10
    assert Path(result['archive_path']).is_file()
    from zipfile import ZipFile
    with ZipFile(result['archive_path']) as z:
        content=json.loads(z.read(next(n for n in z.namelist() if n.endswith('stabilization_summary.json'))))
    assert content['expected_changes'] == 31
    assert content['semantic_coverage_verified'] is False


def test_changed_only_batch_continues_after_lang_exception(tmp_path, monkeypatch):
    from gf_wordbench.practical import stabilization021 as step
    def fake_run(language, *, scenarios, **kwargs):
        if language == 'Fre':
            raise RuntimeError('simulated GF failure')
        return {'run_id':language,'scenarios':[{'id':s,'candidate':'x'} for s in scenarios],
                'totals':{'candidate_for_review':len(scenarios),'probe_failed':0,'timeout':0,'unverified':0}}
    monkeypatch.setattr(step,'run_pilot',fake_run)
    result=step.run_changed(gf=tmp_path/'fake',rgl=tmp_path/'rgl',output_root=tmp_path/'out')
    assert result['status'] == 'completed_with_failures'
    assert result['languages']['Fre']['status'] == 'execution_error'
    assert 'Por' in result['languages']
    assert Path(result['archive_path']).exists()
