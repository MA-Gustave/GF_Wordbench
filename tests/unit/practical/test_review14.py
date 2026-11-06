"""Focus-14 review: 210 evidence items; never silently promotes to gold."""
from __future__ import annotations
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from gf_wordbench.practical.review14 import (
    FOCUS14, EXPECTED_SCENARIOS, digest, load_audit, generate_audit,
    finalize_review, compare_runs,
)


def _archive(tmp: Path, *, suffix: str = 'a', broken: tuple[str, str] | None = None) -> Path:
    dest = tmp / f'batch-{suffix}.zip'
    summary = {'schema_id': 'defluens.pilot-batch', 'mode': 'full', 'batch_id': 'run-' + suffix, 'entries': []}
    member_root = f'defluens-batch-full-{suffix}'
    with ZipFile(dest, 'w') as z:
        for language in FOCUS14:
            root = f'{member_root}/languages/defluens-pilot-{language}-r1'
            run = {'schema_id': 'defluens.pilot-run', 'language': language, 'run_id': 'r1', 'scenarios': []}
            for sid in EXPECTED_SCENARIOS:
                candidate = 'example ' + sid + ' ' + language
                if language == 'Est' and sid in ('instruction', 'conditional-instruction'):
                    candidate = 'oota'
                entry = {'id': sid, 'status': 'candidate_for_review', 'candidate': candidate,
                         'meaning_en': 'An English gloss.', 'module': 'X' + language + '.gf',
                         'source_sha256': '0'*64, 'script_sha256': '0'*64}
                run['scenarios'].append(entry)
                raw_candidate = candidate + '\n'
                if broken == (language, sid):
                    raw_candidate = 'tampered!\n'
                z.writestr(root + '/scenarios/' + sid + '.candidate.txt', raw_candidate)
                z.writestr(root + '/scenarios/' + sid + '.stdout.txt',
                           'GF_WORDBENCH_BEGIN linearize\n' + candidate + '\nGF_WORDBENCH_END linearize')
                z.writestr(root + '/scenarios/' + sid + '.stderr.txt', '')
            z.writestr(root + '/pilot_run.json', json.dumps(run))
            summary['entries'].append({'language': language, 'scenarios_attempted': 15,
                'totals': {'candidate_for_review': 15, 'probe_failed': 0, 'timeout': 0, 'unverified': 0}})
        z.writestr(member_root + '/batch_summary.json', json.dumps(summary))
    return dest


def _review_payload(audit: dict, reviewer: str = '') -> dict:
    return {'schema_id': 'defluens.review14-decisions', 'schema_version': '1.0',
            'batch_id': audit['batch_id'], 'batch_sha256': audit['batch_sha256'],
            'reviewer': reviewer, 'decisions': [
                {'language': r['language'], 'scenario': r['scenario'], 'run_id': r['run_id'],
                 'candidate_sha256': r['candidate_sha256'], 'reference_text': r['candidate'],
                 'decision': 'pending', 'notes': ''} for r in audit['candidates']]}


def test_exactly_fourteen_languages_and_evidence_consistency(tmp_path):
    batch = _archive(tmp_path)
    audit = load_audit(batch)
    assert audit['totals']['technical_candidates'] == 210
    assert audit['totals']['linguistically_approved'] == 0
    assert audit['semantic_coverage_verified'] is False
    assert audit['languages'] == list(FOCUS14)
    assert any('condition' in f.lower() for row in audit['candidates'] if row['language'] == 'Est'
               and row['scenario'] == 'conditional-instruction' for f in row['flags'])
    output, archive = generate_audit(batch, tmp_path)
    assert archive.is_file()
    page = tmp_path / ('defluens-review14-' + audit['batch_id']) / 'Revue_14_langues.html'
    assert 'Exporter mes décisions JSON' in page.read_text(encoding='utf-8')
    assert output['totals']['linguistically_approved'] == 0


def test_tampering_of_raw_candidate_is_rejected(tmp_path):
    with pytest.raises(ValueError, match='Candidate text differs'):
        load_audit(_archive(tmp_path, broken=('Fre', 'quantity')))


def test_no_approvals_without_human_name_and_locked_reference(tmp_path):
    batch = _archive(tmp_path)
    audit = load_audit(batch)
    payload = _review_payload(audit)
    payload['decisions'][0]['decision'] = 'approve'
    decisions_path = tmp_path / 'decisions.json'
    decisions_path.write_text(json.dumps(payload), encoding='utf-8')
    with pytest.raises(ValueError, match='named human'):
        finalize_review(batch, decisions_path, tmp_path)
    payload['reviewer'] = 'Reviewer A'
    payload['decisions'][0]['reference_text'] = 'altered candidate'
    decisions_path.write_text(json.dumps(payload), encoding='utf-8')
    with pytest.raises(ValueError, match='differs from actual GF'):
        finalize_review(batch, decisions_path, tmp_path)
    payload['decisions'][0]['reference_text'] = audit['candidates'][0]['candidate']
    payload['decisions'][1]['decision'] = 'reject'
    payload['decisions'][1]['notes'] = 'Incorrect tense'
    decisions_path.write_text(json.dumps(payload), encoding='utf-8')
    result = finalize_review(batch, decisions_path, tmp_path)
    assert result['totals'] == {
        'human_approved_candidate': 1, 'requires_correction': 1, 'unverified': 208}
    assert result['semantic_coverage_verified'] is False


def test_rejects_unbound_or_duplicate_reviews(tmp_path):
    batch = _archive(tmp_path)
    payload = _review_payload(load_audit(batch), 'Reviewer A')
    decisions_path = tmp_path / 'decisions.json'
    payload['decisions'][2] = payload['decisions'][0]
    decisions_path.write_text(json.dumps(payload), encoding='utf-8')
    with pytest.raises(ValueError, match='duplicated'):
        finalize_review(batch, decisions_path, tmp_path)
    payload = _review_payload(load_audit(batch), 'Reviewer A')
    payload['batch_sha256'] = 'f'*64
    decisions_path.write_text(json.dumps(payload), encoding='utf-8')
    with pytest.raises(ValueError, match='not bound'):
        finalize_review(batch, decisions_path, tmp_path)


def test_repeatability_comparison_is_not_linguistic_certification(tmp_path):
    earlier = _archive(tmp_path, suffix='a')
    later = _archive(tmp_path, suffix='b')
    result = compare_runs(earlier, later, tmp_path)
    assert result['totals']['identical_outputs'] == 210
    assert result['totals']['identical_source_locks'] == 210
    assert result['totals']['differences'] == 0
    assert result['semantic_coverage_verified'] is False
