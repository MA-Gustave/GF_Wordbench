"""Focused practical-coverage contract tests; GF execution is separately tested."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from gf_wordbench.practical.coverage import assess, load_profile, selected_scenario_ids
from gf_wordbench.practical.cli import build_parser, validate_profile_scenario_scope

PROFILE = Path(__file__).resolve().parents[3] / "profiles" / "practical_generation_v1.json"


def summary_for(profile, *, default='OK'):
    return {
        'schema_id':'gf-wordbench.run-summary', 'schema_version':'1.0',
        'metadata':{'project_id':'Eng','run_id':'test001','no_compile':False},
        'totals':{'overall_status':default},
        'scenario_results':[{'scenario_id':sid, 'status':'OK', 'gold_match':True,
                             'gold_path':f'validation/gold/{sid}.gold',
                             'normalized_output_path':f'raw/{sid}.out',
                             'exit_code':0,'timed_out':False,'sections':[]}
                            for sid in selected_scenario_ids(profile)]
    }


def test_all_required_gold_passes():
    profile = load_profile(PROFILE)
    report = assess(profile, summary_for(profile), language_key='Eng')
    assert report['status'] == 'ready'
    assert {d['status'] for d in report['domains']} == {'ready'}


def test_failed_required_scenario_blocks_only_its_domain():
    profile = load_profile(PROFILE)
    doc = summary_for(profile,default='FAIL')
    for item in doc['scenario_results']:
        if item['scenario_id'] == 'past-event':
            item['status'] = 'FAIL'
    report=assess(profile,doc)
    assert report['status'] == 'needs_work'
    assert any('past-event' in d['missing'] for d in report['domains'])
    assert next(d for d in report['domains'] if d['domain'] == 'procedural')['status'] == 'unverified'


def test_compilation_only_never_ready():
    profile=load_profile(PROFILE)
    doc=summary_for(profile)
    doc['scenario_results']=[]
    report=assess(profile,doc)
    assert report['status'] == 'unverified'
    assert all(d['unverified'] for d in report['domains'])


def test_no_gold_never_ready():
    profile=load_profile(PROFILE)
    doc=summary_for(profile)
    doc['scenario_results'][0]['gold_match']=None
    assert assess(profile,doc)['status'] == 'unverified'


def test_language_identity_protected():
    profile=load_profile(PROFILE)
    with pytest.raises(ValueError,match='identity'):
        assess(profile,summary_for(profile),language_key='Fra')


def test_cli_practical_modes_are_separate_from_general_release_policy():
    request=build_parser().parse_args(['check','--practical-profile',str(PROFILE),'--summary','/tmp/sample.json'])
    assert request.action == 'check'
    run=build_parser().parse_args(['run','--language-path','/tmp/eng','--validation-profile','/tmp/project.toml','--practical-profile',str(PROFILE)])
    assert run.action == 'run'


def test_scope_rejects_unrelated_required_scenarios(tmp_path):
    profile=tmp_path/'project.toml'
    profile.write_text('[modules]\ncheckpoints = ["GrammarEng.gf"]\n[validation]\nrequired_scenarios = ["literary-past"]\noptional_scenarios = ["factual-present"]\n')
    with pytest.raises(ValueError,match='unrelated'):
        validate_profile_scenario_scope(profile,('factual-present',))
