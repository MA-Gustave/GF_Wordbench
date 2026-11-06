"""Pilot material integrity and isolated GF invocation; no real GF required."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import sys
from zipfile import ZipFile

import pytest

from gf_wordbench.practical.pilot import (
    _validate_pilot,
    run_pilot,
    _gf_paths,
    LANGUAGE_DIRECTORIES,
)
from gf_wordbench.practical.coverage import load_profile


@pytest.mark.parametrize('lang',tuple(LANGUAGE_DIRECTORIES))
def test_each_pilot_has_15_sha_locked_parsed_scenarios(lang):
    check=_validate_pilot(lang)
    assert check['scenario_count']==15
    assert check['status']=='preflight_ok'
    assert check['gf_executed'] is False
    assert check['gold_approved'] is False
    root=Path(check['pilot_root'])
    assert not list((root/'validation/gold').glob('*.gold'))


def test_modified_gf_source_rejected_before_run(tmp_path):
    import gf_wordbench.practical.pilot as pilot
    example=pilot._pilot_root('Eng')
    copy=tmp_path/'pilot'/'Eng'
    shutil.copytree(example,copy)
    source=copy/'validation/inputs/DefluensFactualPresentEng.gf'
    source.write_text(source.read_text(encoding='utf-8')+'\n-- unauthorized edit\n',encoding='utf-8')
    with pytest.raises(ValueError,match='SHA|hash|manifest'):
        _validate_pilot('Eng',pilots_root=copy.parent)


def test_pilot_generates_candidate_not_verified_with_fake_gf(tmp_path):
    import gf_wordbench.practical.pilot as pilot
    mock_gf=tmp_path/'engine'/'gf'
    mock_gf.parent.mkdir()
    mock_gf.write_text('#!'+sys.executable+'\n'
        'import sys\n'
        'for line in sys.stdin:\n'
        ' if line.startswith("ps "):\n'
        '  print(line.split("\\\"",2)[1])\n'
        ' elif line.startswith("l -lang="):\n'
        '  print("Mira is ready")\n', encoding='utf-8')
    mock_gf.chmod(0o755)
    rgl=tmp_path/'rgl'; (rgl/'src/english').mkdir(parents=True)
    outcome=run_pilot('Eng',gf_executable=mock_gf,rgl_root=rgl,output_root=tmp_path/'results',
                      scenarios=('factual-present',),timeout_sec=10,export_zip=True)
    assert outcome['semantic_coverage_verified'] is False
    assert outcome['status']=='unverified'
    assert outcome['scenarios'][0]['status']=='candidate_for_review'
    assert outcome['scenarios'][0]['candidate']=='Mira is ready'
    report=Path(outcome['scenarios'][0]['stdout']).parents[1]/'pilot_run.json'
    assert report.exists()
    review=json.loads((report.parent/'review_template.json').read_text(encoding='utf-8'))
    assert review['decisions'][0]['approved'] is False
    archive=Path(outcome['archive_path'])
    assert archive.parent == tmp_path/'results'
    assert archive.is_file()
    with ZipFile(archive) as handle:
        names=set(handle.namelist())
        assert f'{report.parent.name}/pilot_run.json' in names
        assert f'{report.parent.name}/review_template.json' in names
        assert f'{report.parent.name}/scenarios/factual-present.candidate.txt' in names
        report_in_zip=json.loads(handle.read(f'{report.parent.name}/pilot_run.json'))
        assert report_in_zip['archive_path']==str(archive)


def test_pilot_profiles_match_practical_profile():
    profile=load_profile(Path(__file__).resolve().parents[3]/'profiles/practical_generation_v1.json')
    assert len([c for c in profile['capabilities'] if c['required']])==15
    for code in LANGUAGE_DIRECTORIES:
        run=_validate_pilot(code)
        assert len(run['scenario_ids'])==15

@pytest.mark.parametrize('lang', tuple(LANGUAGE_DIRECTORIES))
def test_six_failing_probe_patterns_are_fixed_and_sha_locked(lang):
    """Regression for real Eng full GF 3.12 results on 2026-11-03.

    This is a static source/manifest test, not proof of GF compilation.
    """
    base = Path(_validate_pilot(lang)['pilot_root']) / 'validation' / 'inputs'
    source = lambda name: (base / f'Defluens{name}{lang}.gf').read_text(encoding='utf-8')
    assert f'Syntax{lang}.mkAdv after_Prep' in source('TemporalOrder')
    assert f'Syntax{lang}.mkAdv if_Subj' in source('ConditionReal')
    assert f'Syntax{lang}.mkAdv in_Prep' in source('Location')
    # Portuguese now uses the RGL's actual future subjunctive morphology;
    # its older if_Subj + present indicative path was not semantically sufficient.
    if lang == 'Por':
        assert 'B.chegar_Besch' in source('ConditionalInstruction')
        assert 'B.Fut B.Sub' in source('ConditionalInstruction')
    else:
        assert f'Syntax{lang}.mkAdv if_Subj' in source('ConditionalInstruction')
    assert 'mkVS (mkV "' in source('SourceAttribution') or 'L.say_VS' in source('SourceAttribution')
    assert 'mkUtt (mkS (Syntax' in source('ConditionReal')
    assert 'mkUtt (mkS (mkS' not in source('ConditionReal')
    quantity = source('Quantity').split('lin Realize = ',1)[1].split(' ;',1)[0]
    assert quantity.count('(') == quantity.count(')')


def test_gf_error_between_markers_is_not_review_candidate(tmp_path):
    """The reported GF process can return 0 even when module compilation fails."""
    mock_gf=tmp_path/'engine'/'gf'
    mock_gf.parent.mkdir()
    mock_gf.write_text('#!'+sys.executable+'\n'
        'import sys\n'
        'for line in sys.stdin:\n'
        ' if line.startswith("ps "):\n'
        '  print(line.split("\\\"",2)[1])\n'
        ' elif line.startswith("l -lang="):\n'
        '  print("empty grammar, no abstract")\n', encoding='utf-8')
    mock_gf.chmod(0o755)
    rgl=tmp_path/'rgl'; (rgl/'src/english').mkdir(parents=True)
    outcome=run_pilot('Eng',gf_executable=mock_gf,rgl_root=rgl,
                      output_root=tmp_path/'results',scenarios=('quantity',),
                      timeout_sec=10,export_zip=True)
    scenario=outcome['scenarios'][0]
    assert scenario['status']=='probe_failed'
    assert scenario['reason']=='gf_reported_error'
    assert scenario['exit_code']==0
    assert scenario['candidate'] is None
    assert 'candidate_path' not in scenario
    run_root=Path(scenario['stdout']).parents[1]
    review=json.loads((run_root/'review_template.json').read_text(encoding='utf-8'))
    assert review['decisions'][0]['candidate'] is None
    assert not list((run_root/'scenarios').glob('*.candidate.txt'))
