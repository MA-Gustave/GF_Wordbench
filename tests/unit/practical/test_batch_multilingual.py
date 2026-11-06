"""Defluens multilingual batch: integration using a fake GF shell, never language certification."""
from __future__ import annotations
import json
from pathlib import Path
import sys
from zipfile import ZipFile

import pytest

from gf_wordbench.practical.batch import (_select_languages, check_campaign, run_campaign,
                                         DEFAULT_LANGUAGES, _csv_report)
from gf_wordbench.practical.pilot import LANGUAGE_DIRECTORIES


def _fake_gf(tmp_path: Path) -> Path:
    exe = tmp_path/'engine'/'gf'
    exe.parent.mkdir(exist_ok=True)
    exe.write_text('#!'+sys.executable+'\n'
        'import sys\n'
        'for line in sys.stdin:\n'
        ' if line.startswith("ps "):\n'
        '  print(line.split("\\\"", 2)[1])\n'
        ' elif line.startswith("l -lang="):\n'
        '  print("sample output awaiting human review")\n'
        ' elif line.strip()=="q":\n'
        '  break\n',encoding='utf-8')
    exe.chmod(0o755)
    return exe


def _fake_rgl(tmp_path:Path, codes:tuple[str,...]) -> Path:
    rgl=tmp_path/'rgl'
    for code in codes:
        (rgl/'src'/LANGUAGE_DIRECTORIES[code]).mkdir(parents=True,exist_ok=True)
    return rgl


def test_default_campaign_is_20_languages_and_300_sha_locked_probes():
    assert len(DEFAULT_LANGUAGES)==20
    assert len(set(DEFAULT_LANGUAGES))==20
    result=check_campaign(DEFAULT_LANGUAGES)
    assert result['ok'] is True
    assert result['gf_executed'] is False
    assert sum(i['scenario_count'] for i in result['languages'])==300
    assert all(x['lexical_status']=='provisional_unreviewed' for x in result['languages'])


def test_language_selection_and_validation():
    assert _select_languages(['Fre','Sqi'])==('Fre','Sqi')
    assert _select_languages(['Fre,Sqi'])==('Fre','Sqi')
    with pytest.raises(ValueError,match='duplicated'):
        _select_languages(['Fre,Fre'])
    with pytest.raises(ValueError,match='no prepared pilot'):
        _select_languages(['Kal'])


def test_smoke_campaign_generates_combined_zip_and_unverified_status(tmp_path):
    codes=('Eng','Fre','Sqi')
    result=run_campaign(languages=codes,gf_executable=_fake_gf(tmp_path),
                        rgl_root=_fake_rgl(tmp_path,codes),output_root=tmp_path/'downloads',
                        mode='smoke',timeout_sec=10,max_minutes=2)
    assert result['status']=='completed_unverified'
    assert result['semantic_coverage_verified'] is False
    assert result['totals']['candidate_for_review']==3
    assert result['totals']['languages_with_issues']==0
    assert all(entry['lexical_status']=='provisional_unreviewed' for entry in result['entries'])
    for entry in result['entries']:
        assert entry['status']=='candidate_for_review'
        pilot=json.loads(Path(entry['pilot_run']).read_text(encoding='utf-8'))
        assert len(pilot['scenarios'])==1
        assert pilot['scenarios'][0]['candidate']=='sample output awaiting human review'
        assert pilot['semantic_coverage_verified'] is False
        assert Path(entry['language_archive_path']).is_file()
    assert Path(result['batch_root'],'batch_summary.csv').is_file()
    assert _csv_report(result['entries']).startswith('\ufefflanguage,')
    with ZipFile(result['archive_path']) as z:
        names=z.namelist()
        assert any(n.endswith('/batch_summary.json') for n in names)
        assert sum(n.endswith('/pilot_run.json') for n in names)==3
        assert sum(n.endswith('/review_template.json') for n in names)==3
        assert sum(n.endswith('.candidate.txt') for n in names)==3
        assert not any(n.endswith('.gfo') or n.endswith('.zip') for n in names)


def test_failed_language_does_not_stop_next_one(tmp_path):
    codes=('Eng','Fre','Sqi')
    result=run_campaign(languages=codes,gf_executable=_fake_gf(tmp_path),
                        rgl_root=_fake_rgl(tmp_path,('Eng','Sqi')),
                        output_root=tmp_path/'downloads',mode='smoke',timeout_sec=10,max_minutes=2)
    assert [e['status'] for e in result['entries']]==['candidate_for_review','setup_error','candidate_for_review']
    assert result['totals']['languages_with_issues']==1
    assert result['totals']['candidate_for_review']==2
    assert Path(result['archive_path']).exists()


def test_full_campaign_runs_all_15_per_language(tmp_path):
    codes=('Eng','Sqi')
    result=run_campaign(languages=codes,gf_executable=_fake_gf(tmp_path),
                        rgl_root=_fake_rgl(tmp_path,codes),
                        output_root=tmp_path/'downloads',mode='full',timeout_sec=10,max_minutes=2)
    assert len(result['entries'])==2
    assert result['totals']['candidate_for_review']==30
    assert result['semantic_coverage_verified'] is False
    for entry in result['entries']:
        assert entry['scenarios_attempted']==15


def test_campaign_refuses_output_inside_rgl_or_gf_installation(tmp_path):
    codes=('Eng',)
    gf=_fake_gf(tmp_path)
    rgl=_fake_rgl(tmp_path,codes)
    with pytest.raises(ValueError,match='outside protected sources'):
        run_campaign(languages=codes,gf_executable=gf,rgl_root=rgl,
                     output_root=rgl/'src'/'english',mode='smoke')
    with pytest.raises(ValueError,match='outside protected sources'):
        run_campaign(languages=codes,gf_executable=gf,rgl_root=rgl,
                     output_root=gf.parent/'results',mode='smoke')
