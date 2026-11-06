import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
from qualifier_gf_wordbench import FIELDS, review, verify_campaigns


def fixture(tmp_path):
    languages=('fr','en','it','es','de','pt','nl','sv','no','da','fi','pl','sq','ro')
    cases=[]
    for i in range(210):
        cases.append({'scenario_id_original':f'case-{i//14+1:02d}',
                      'language':languages[i%14],
                      'source_lock_sha256':'a'*64,
                      'original_text':f'Source #{i}',
                      'generated_text':f'Target #{i}'})
    path_a=tmp_path/'a.json';path_b=tmp_path/'b.json'
    for p in (path_a,path_b):
        p.write_text(json.dumps({'format':'gf-wordbench-campaign-cases/1.0',
                                  'cases':cases}),encoding='utf-8')
    rows=[]
    for case in cases:
        rows.append({**case,'fidelity':'APPROVED','grammar':'APPROVED',
                     'limitations_preserved':'APPROVED','human_status':'APPROVED',
                     'reviewer':'Test reviewer, NON REEL',
                     'review_date_utc':'2026-11-03T18:10:00Z'})
    totals={'totals':{'scenarios':210,'identical_outputs':210,'identical_source_locks':210,'differences':0}}
    return totals,rows,path_a,path_b


def test_blank_csv_remains_blocked(tmp_path):
    c,rows,a,b=fixture(tmp_path)
    rows=[{f:'' for f in FIELDS} for _ in range(210)]
    assert review(c,rows)['status']=='BLOCKED'
    assert review(c,rows,campaign_a=a,campaign_b=b)['status']=='BLOCKED'


def test_fabricated_approved_csv_without_both_original_exports_is_blocked(tmp_path):
    c,rows,a,b=fixture(tmp_path)
    r=review(c,rows)
    assert r['status']=='BLOCKED'
    assert r['approved_human_rows']==0
    assert r['linguistic_certification_issued'] is False


def test_matching_exports_allow_recorded_review_but_never_issue_certificate(tmp_path):
    c,rows,a,b=fixture(tmp_path)
    r=review(c,rows,campaign_a=a,campaign_b=b)
    assert r['status']=='REVIEW_DOCUMENTED_NEEDS_INDEPENDENT_RELEASE_AUTHORITY'
    assert r['approved_human_rows']==210
    assert r['linguistic_certification_issued'] is False
    assert r['independent_gf_execution_performed'] is False


def test_changed_source_lock_and_text_refused(tmp_path):
    c,rows,a,b=fixture(tmp_path)
    rows[0]['generated_text']='TEXT HAS CHANGED'
    rows[1]['source_lock_sha256']='b'*64
    r=review(c,rows,campaign_a=a,campaign_b=b)
    assert r['status']=='BLOCKED'
    assert r['approved_human_rows']==208
    assert 'différents des campagnes' in ' '.join(r['blocking_reasons'])


def test_campaign_duplicate_and_different_output_refused(tmp_path):
    c,rows,a,b=fixture(tmp_path)
    doc=json.loads(b.read_text())
    doc['cases'][0]['generated_text']='wrong'
    b.write_text(json.dumps(doc))
    assert review(c,rows,campaign_a=a,campaign_b=b)['status']=='BLOCKED'
    doc['cases'][0]['generated_text']='Target #0'
    doc['cases'][1]=doc['cases'][0]
    b.write_text(json.dumps(doc))
    assert review(c,rows,campaign_a=a,campaign_b=b)['status']=='BLOCKED'


def test_timestamp_must_be_real_offset_aware(tmp_path):
    c,rows,a,b=fixture(tmp_path)
    rows[0]['review_date_utc']='today'
    assert review(c,rows,campaign_a=a,campaign_b=b)['status']=='BLOCKED'
    rows[0]['review_date_utc']='2026-11-03'
    assert review(c,rows,campaign_a=a,campaign_b=b)['status']=='BLOCKED'


def test_existing_ai_assessment_is_not_human_certification():
    path = Path(__file__).resolve().parents[3] / 'evidence' / 'baselines' / 'AI_14_langues_210_scenarios_20261103.json'
    doc = json.loads(path.read_text(encoding='utf-8'))
    counts = doc['totals']
    assert counts['acceptable'] + counts['incorrect'] + counts['uncertain'] == 210
    assert doc['official_linguistic_certification'] is False
    assert doc['approved_golds'] == 0
