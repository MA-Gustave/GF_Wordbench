"""Read-only Defluens linguistic audit and GF token-join preview.

The GF raw output, stdout, stderr, and source locks remain authoritative.
The preview is NOT a replacement, approved gold, or semantic certification.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile

PILOTS = Path(__file__).resolve().parents[3] / 'pilots' / 'practical_generation_v1'
BASELINE = PILOTS / 'review14_v021_reference.json'
# GF '&+' means join the lexical material on either side without whitespace.
_JOIN = re.compile(r'\s*&\+\s*')


def render_preview(raw: str) -> str:
    """Normalize GF token joins for display only; do not alter candidates."""
    return _JOIN.sub('', raw)


def audit_archive(archive: Path, *, baseline: Path = BASELINE) -> dict:
    baseline_data = json.loads(baseline.read_text(encoding='utf8'))
    ref = {(x['language'],x['scenario_id']):x for x in baseline_data['rows']}
    records = []
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    with ZipFile(archive) as z:
        names = z.namelist()
        runs = [name for name in names if name.endswith('/pilot_run.json')]
        if not runs:
            raise ValueError('No pilot_run.json found in archive')
        for name in runs:
            report = json.loads(z.read(name))
            lang = report['language']
            for item in report['scenarios']:
                sid = item['id']
                key = (lang,sid)
                if key in {(x['language'],x['scenario_id']) for x in records}:
                    raise ValueError(f'Duplicate scenario in archive: {lang}/{sid}')
                raw = item.get('candidate')
                old = ref.get(key)
                identical = bool(old and raw==old['candidate_raw'] and item['source_sha256']==old['source_sha256'] and item['script_sha256']==old['script_sha256'])
                records.append({
                    'language':lang,'scenario_id':sid,'expected_meaning_en':item.get('meaning_en'),
                    'gf_status':item.get('status'),'candidate_raw':raw,
                    'candidate_rendered_preview':render_preview(raw) if isinstance(raw,str) else None,
                    'gf_token_join_present':bool(isinstance(raw,str) and '&+' in raw),
                    'baseline_exact_match':identical,
                    'previous_ai_judgement':old.get('evaluation_ia') if old else None,
                    'requires_new_ai_review':not identical,
                    'source_sha256':item['source_sha256'],'script_sha256':item['script_sha256'],
                    'gold_approved':False,
                })
    rows = sorted(records,key=lambda r:(r['language'],r['scenario_id']))
    counts=Counter(x['gf_status'] for x in rows)
    return {
        'schema_id':'defluens.read-only-linguistic-reassessment',
        'schema_version':'0.2.2','source_archive_sha256':digest,
        'source_archive_name':archive.name,
        'scope':{'languages':len({r['language'] for r in rows}),'scenarios':len(rows)},
        'totals':{
            'candidate_for_review':counts['candidate_for_review'],
            'probe_failed':sum(v for k,v in counts.items() if k!='candidate_for_review'),
            'exact_baseline_matches':sum(r['baseline_exact_match'] for r in rows),
            'requires_new_ai_review':sum(r['requires_new_ai_review'] for r in rows),
            'token_join_previews':sum(r['gf_token_join_present'] for r in rows),
        },
        'evidence_policy':'Candidate_raw and GF logs are immutable. Rendered previews are not golds.',
        'semantic_coverage_verified':False,'gold_approved':False,'rows':rows,
    }


def main(argv: list[str] | None = None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--batch',type=Path,required=True)
    p.add_argument('--baseline',type=Path,default=BASELINE)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(argv)
    report=audit_archive(a.batch,baseline=a.baseline)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':'audit_generated','totals':report['totals'],
                      'semantic_coverage_verified':False,'report_path':str(a.output)},ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
