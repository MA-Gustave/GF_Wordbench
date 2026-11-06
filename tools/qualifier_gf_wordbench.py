#!/usr/bin/env python3
"""Revue GF fail-closed : deux campagnes intégrales + 210 avis humains.

Les campagnes fournies par l'utilisateur sont des éléments de preuve, pas une
attestation indépendante. Ce contrôleur ne délivre jamais de certificat.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

FIELDS = ('scenario_id_original', 'language', 'source_lock_sha256',
          'original_text', 'generated_text', 'fidelity', 'grammar',
          'limitations_preserved', 'human_status', 'reviewer', 'review_date_utc')
CASE_FIELDS = ('scenario_id_original', 'language', 'source_lock_sha256',
               'original_text', 'generated_text')
HEX = re.compile(r'^(?:sha256:)?[a-f0-9]{64}$')
LANG = re.compile(r'^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$')
APPROVED = 'APPROVED'


class ProvenanceError(ValueError):
    pass


def _digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 80_000_000:
        raise ProvenanceError('Campagne absente, symbolique ou trop volumineuse')
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def _load_cases(path: Path) -> tuple[dict, str]:
    """Format explicitement défini, pas d'inférence d'identifiants de scénario.

    {"format":"gf-wordbench-campaign-cases/1.0","cases":[{
       "scenario_id_original":"...", "language":"fr", "source_lock_sha256":"...",
       "original_text":"...", "generated_text":"..."}, ...]}
    """
    digest = _digest(path)
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
    except (ValueError, OSError) as exc:
        raise ProvenanceError('Campagne JSON invalide') from exc
    if not isinstance(data, dict) or data.get('format') != 'gf-wordbench-campaign-cases/1.0':
        raise ProvenanceError('Format de campagne non reconnu')
    records = data.get('cases')
    if not isinstance(records, list) or not records:
        raise ProvenanceError('Campagne sans scénarios')
    found = {}
    for index, row in enumerate(records, 1):
        if not isinstance(row, dict) or any(not isinstance(row.get(k), str) or not row[k].strip() for k in CASE_FIELDS):
            raise ProvenanceError(f'Campagne : champs du scénario {index} incomplets')
        key = (row['scenario_id_original'], row['language'])
        if not LANG.fullmatch(key[1]) or not HEX.fullmatch(row['source_lock_sha256']):
            raise ProvenanceError(f'Campagne : langue ou empreinte invalide, scénario {index}')
        if key in found:
            raise ProvenanceError('Campagne avec scénario/langue dupliqué')
        found[key] = tuple(row[k] for k in CASE_FIELDS)
    return found, digest


def verify_campaigns(compare: dict, a: Path | None, b: Path | None) -> dict:
    result = {'status': 'BLOCKED', 'campaigns_independently_verified': False,
              'campaign_a_sha256': None, 'campaign_b_sha256': None,
              'case_count': 0, 'languages': [], 'cases': {}, 'reasons': []}
    if a is None or b is None:
        result['reasons'].append('Deux exports complets des campagnes A et B sont requis')
        return result
    try:
        cases_a, hash_a = _load_cases(a)
        cases_b, hash_b = _load_cases(b)
        result['campaign_a_sha256'] = hash_a
        result['campaign_b_sha256'] = hash_b
    except ProvenanceError as exc:
        result['reasons'].append(str(exc))
        return result
    totals = compare.get('totals', {}) if isinstance(compare, dict) else {}
    expected = totals.get('scenarios')
    languages = sorted({key[1] for key in cases_a})
    result['case_count'] = len(cases_a)
    result['languages'] = languages
    if len(cases_a) != expected or len(cases_b) != expected:
        result['reasons'].append('Comptage non concordant avec le rapport de comparaison')
    if len(languages) != 14:
        result['reasons'].append(f'14 langues attendues, {len(languages)} présentes')
    if cases_a != cases_b:
        result['reasons'].append('Campagnes non identiques : scénario, langue, source ou texte divergent')
    if (totals.get('identical_outputs') != expected or
        totals.get('identical_source_locks') != expected or totals.get('differences') != 0):
        result['reasons'].append('Le rapport de comparaison n’atteste pas la reproductibilité')
    if result['reasons']:
        return result
    result['status'] = 'PASS_TWO_EXPORTED_CAMPAIGNS_MATCH'
    result['campaigns_independently_verified'] = False  # raw exports still require external audit
    result['cases'] = cases_a
    return result


def _date_ok(s: str) -> bool:
    try:
        d = datetime.fromisoformat(s.replace('Z', '+00:00'))
        return d.tzinfo is not None and d.utcoffset() is not None
    except ValueError:
        return False


def review(compare: dict, rows: list[dict], *, campaign_a: Path | None = None,
           campaign_b: Path | None = None) -> dict:
    totals = compare.get('totals', {}) if isinstance(compare, dict) else {}
    count = totals.get('scenarios')
    reproducible = (type(count) is int and count > 0 and
                    totals.get('identical_outputs') == count and
                    totals.get('identical_source_locks') == count and
                    totals.get('differences') == 0)
    reasons = []
    if not reproducible:
        reasons.append('Comparaison non déterministe ou incomplète')
    if type(count) is not int or count <= 0:
        reasons.append('Nombre de scénarios invalide')
        count = 0
    if len(rows) != count:
        reasons.append(f'Revues : {len(rows)} lignes contre {count} scénarios')
    campaigns = verify_campaigns(compare, campaign_a, campaign_b)
    reasons.extend(campaigns['reasons'])
    authoritative_cases = campaigns['cases']
    seen = set()
    approved = 0
    for n, row in enumerate(rows, 1):
        key = (row.get('scenario_id_original', '').strip(), row.get('language', '').strip())
        valid_key = all(key) and key not in seen
        if not valid_key:
            reasons.append(f'Ligne {n} : scénario/langue non identifié ou dupliqué')
        seen.add(key)
        case = tuple(row.get(f, '').strip() for f in CASE_FIELDS)
        # La revue ne fait pas foi si le texte/lock diffère des vrais exports.
        source_ok = bool(authoritative_cases) and authoritative_cases.get(key) == case
        if authoritative_cases and not source_ok:
            reasons.append(f'Ligne {n} : texte, langue ou verrou différents des campagnes')
        checks = [row.get(f, '').strip() for f in ('fidelity','grammar','limitations_preserved')]
        valid = (all(v == APPROVED for v in checks) and
                 HEX.fullmatch(row.get('source_lock_sha256', '').strip()) is not None and
                 all(row.get(f,'').strip() for f in ('original_text','generated_text','reviewer')) and
                 _date_ok(row.get('review_date_utc', '').strip()))
        if row.get('human_status','').strip() == APPROVED and valid and valid_key and source_ok:
            approved += 1
        else:
            reasons.append(f'Ligne {n} : validation humaine ou provenance incomplète')
    complete = (reproducible and campaigns['status'] == 'PASS_TWO_EXPORTED_CAMPAIGNS_MATCH'
                and len(rows) == count and approved == count and len(seen) == count)
    return {'format': 'gf-wordbench-human-review-check/2.0',
            'status': 'REVIEW_DOCUMENTED_NEEDS_INDEPENDENT_RELEASE_AUTHORITY' if complete else 'BLOCKED',
            'reported_reproducible': reproducible,
            'two_campaigns_consistent_with_report': campaigns['status'] == 'PASS_TWO_EXPORTED_CAMPAIGNS_MATCH',
            'campaign_a_sha256': campaigns['campaign_a_sha256'],
            'campaign_b_sha256': campaigns['campaign_b_sha256'],
            'source_languages_observed': campaigns['languages'],
            'independent_gf_execution_performed': False,
            'linguistic_certification_issued': False,
            'rows': len(rows), 'approved_human_rows': approved,
            'expected_scenarios': count, 'blocking_reasons': reasons[:20],
            'more_blockers': max(0, len(reasons)-20),
            'publication_authorized': False}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Revue GF Wordbench ancrée à deux exports A/B, sans certification')
    parser.add_argument('--compare', type=Path, required=True)
    parser.add_argument('--reviews', type=Path, required=True)
    parser.add_argument('--campaign-a', type=Path, default=None, help='Export complet de la première campagne')
    parser.add_argument('--campaign-b', type=Path, default=None, help='Export complet de la deuxième campagne')
    parser.add_argument('--out', type=Path, required=True)
    args=parser.parse_args(argv)
    try:
        compare=json.loads(args.compare.read_text(encoding='utf-8-sig'))
        with args.reviews.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f)
            if reader.fieldnames is None or not set(FIELDS) <= set(reader.fieldnames):
                parser.error('Colonnes de revue humaine manquantes')
            rows=list(reader)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    result=review(compare, rows, campaign_a=args.campaign_a, campaign_b=args.campaign_b)
    result['evaluated_at_utc']=datetime.now(timezone.utc).isoformat()
    if args.out.exists():
        parser.error('Fichier rapport existant : nouveau chemin requis')
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status'].startswith('REVIEW_DOCUMENTED') else 2


if __name__=='__main__':
    raise SystemExit(main())
