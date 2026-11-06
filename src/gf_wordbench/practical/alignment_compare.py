"""Compare new 14-language GF outputs to the historical AI-reviewed baseline.

A source-matching replay is required. Differences are *not* automatic fixes or
semantic certification. Read-only ZIP parsing, no GF execution and no .gold.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any
from zipfile import ZipFile

from gf_wordbench.practical.alignment14 import PILOTS, read_policy

BASELINE = Path(__file__).resolve().parents[3] / 'evidence' / 'baselines' / 'AI_14_langues_210_scenarios_20261103.json'


def _batch_items(archive: Path) -> dict[tuple[str, str], dict[str, Any]]:
    archive = archive.resolve(strict=True)
    result: dict[tuple[str, str], dict[str, Any]] = {}
    with ZipFile(archive) as z:
        names = z.namelist()
        reports = [n for n in names if n.endswith('/pilot_run.json') and '/languages/' in n]
        for n in reports:
            raw = json.loads(z.read(n))
            if raw.get('schema_id') != 'defluens.pilot-run':
                raise ValueError(f'Unexpected run schema: {n}')
            code = raw['language']
            for entry in raw['scenarios']:
                key = code, entry['id']
                if key in result:
                    raise ValueError(f'Duplicate scenario in campaign ZIP: {key}')
                item = dict(entry)
                item['language'] = code
                # Confirm each accepted candidate actually appears in a proof file.
                if item['status'] == 'candidate_for_review':
                    proof = n.rsplit('/',1)[0] + '/scenarios/' + entry['id'] + '.candidate.txt'
                    if proof not in names:
                        raise ValueError(f'{code}/{entry["id"]}: candidate proof missing')
                    actual = z.read(proof).decode('utf-8').strip()
                    if actual != (item.get('candidate') or '').strip():
                        raise ValueError(f'{code}/{entry["id"]}: candidate proof differs from report')
                result[key] = item
    return result


def current_hashes(pilots_root: Path = PILOTS) -> dict[tuple[str, str], tuple[str, str]]:
    hashes = {}
    for lang in read_policy()['languages']:
        manifest = json.loads((pilots_root/lang/'pilot_manifest.json').read_text(encoding='utf-8'))
        for entry in manifest['scenarios']:
            hashes[(lang, entry['id'])] = entry['source_sha256'],entry['script_sha256']
    return hashes


def compare_archive(archive: Path, *, baseline: Path = BASELINE,
                    pilots_root: Path = PILOTS) -> dict[str, Any]:
    source = json.loads(baseline.read_text(encoding='utf-8'))
    if len(source.get('assessments', [])) != 210:
        raise ValueError('Historical assessment must contain 210 scenarios')
    old = {(x['language'], x['scenario_id']): x for x in source['assessments']}
    hashes = current_hashes(pilots_root)
    new = _batch_items(archive)
    if set(new) != set(old) or set(new) != set(hashes):
        raise ValueError(f'Archive must contain the exact 14 x 15 scenarios; got {len(new)}')
    stale = [f'{l}/{s}' for (l,s),entry in new.items() if
             (entry['source_sha256'],entry['script_sha256']) != hashes[(l,s)]]
    if stale:
        raise ValueError('Campaign ZIP does not match current aligned WordBench sources: '
                         + ', '.join(stale[:5]) + (' ...' if len(stale)>5 else ''))
    rows=[]
    for key in sorted(old):
        initial, latest = old[key],new[key]
        oldtext=initial['candidate']
        newtext=latest.get('candidate')
        status=latest['status']
        rows.append({'language':key[0], 'scenario_id':key[1],
                     'expected_meaning_en': initial['meaning_en'],
                     'historical_output':oldtext, 'new_output':newtext,
                     'historical_judgement':initial['judgement'],
                     'new_gf_status':status,
                     'output_changed':newtext != oldtext,
                     'source_changed':latest['source_sha256']!=initial['repeated_source_sha256'],
                     'requires_semantic_reassessment':True,
                     'source_sha256':latest['source_sha256'],
                     'script_sha256':latest['script_sha256']})
    return {
        'schema_id':'defluens.rgl-alignment-output-comparison','schema_version':'1.0',
        'archive':str(archive),'historical_ai_assessment':str(baseline),
        'technical_baseline': '210 candidate outputs, 2026-11-03',
        'gold_approved':False, 'semantic_coverage_verified':False,
        'evaluation_note':'Lexical improvements must be judged from new GF outputs; output differences are not semantic certifications.',
        'totals':{'scenarios':len(rows),
                  'candidate_for_review':sum(x['new_gf_status']=='candidate_for_review' for x in rows),
                  'probe_failed_or_timeout':sum(x['new_gf_status']!='candidate_for_review' for x in rows),
                  'source_changed':sum(x['source_changed'] for x in rows),
                  'output_changed':sum(x['output_changed'] for x in rows),
                  'output_unchanged':sum(not x['output_changed'] for x in rows)},
        'by_language':{code:{
            'candidate_for_review':sum(x['new_gf_status']=='candidate_for_review' for x in rows if x['language']==code),
            'output_changed':sum(x['output_changed'] for x in rows if x['language']==code)}
            for code in read_policy()['languages']},
        'rows': rows}


def locate_latest_matching_batch(batch_dir: Path, *, pilots_root: Path = PILOTS) -> Path:
    if not batch_dir.is_dir():
        raise ValueError(f'Reports directory missing: {batch_dir}')
    mismatches=[]
    for zip_path in sorted(batch_dir.glob('defluens-batch-full-*.zip'),key=lambda p:p.name,reverse=True):
        try:
            mapping = _batch_items(zip_path)
            hashes = current_hashes(pilots_root)
            if set(mapping)==set(hashes) and all((item['source_sha256'],item['script_sha256']) == hashes[k]
                                                  for k,item in mapping.items()):
                return zip_path
            mismatches.append(zip_path.name)
        except (ValueError, OSError, KeyError):
            mismatches.append(zip_path.name)
    raise ValueError('No completed 14-language batch ZIP matches the new source hashes. '
                     'Run Lancer_Alignement_14_Langues.bat full first. '
                     f'Archives inspected: {len(mismatches)}')
