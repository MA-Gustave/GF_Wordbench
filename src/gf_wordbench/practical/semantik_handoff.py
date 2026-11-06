"""Development evidence handoff to SemantiK Architect, never a release manifest.

This tool does not generate a bridge, claim operation conformance, approve a gold,
compile a PGF, or activate a RuntimeSet. It preserves the experimental GF evidence
and makes the unproven semantic-operation boundaries explicit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from zipfile import ZipFile, BadZipFile

LANGUAGES = ('Eng','Fre','Spa','Ger','Dut','Swe','Dan','Nor','Nno','Fin','Est','Afr','Ita','Por')
# Existing SA v1 operations: a suggested correspondence, not an admitted bridge.
CROSSWALK = {
    'factual-present': ('clause.copular_attribute', 'operation_candidate'),
    'past-event': ('clause.intransitive_event', 'feature_conformance_required'),
    'past-state': ('clause.copular_attribute', 'feature_conformance_required'),
    'future-reference': ('clause.intransitive_event', 'feature_conformance_required'),
    'factual-negation': ('clause.copular_attribute', 'feature_conformance_required'),
    'temporal-order': ('clause.intransitive_event', 'contract_extension_or_feature_required'),
    'condition-real': (None, 'contract_extension_required'),
    'possibility': ('clause.intransitive_event', 'feature_conformance_required'),
    'source-attribution': (None, 'contract_extension_required'),
    'quantity': ('clause.transitive_event', 'feature_conformance_required'),
    'location': ('clause.locative', 'operation_candidate'),
    'instruction': ('directive.action', 'operation_candidate'),
    'prohibition': ('directive.action', 'feature_conformance_required'),
    'obligation': ('directive.action', 'feature_conformance_required'),
    'conditional-instruction': (None, 'contract_extension_required'),
}
SHA = re.compile(r'^[a-f0-9]{64}$')
MAX_ARCHIVE_BYTES = 200_000_000


def _load_json(z: ZipFile, path: str) -> dict:
    info = z.getinfo(path)
    if info.file_size > 5_000_000:
        raise ValueError(f'oversized JSON: {path}')
    value = json.loads(z.read(info).decode('utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError(f'expected object: {path}')
    return value


def build_handoff(archive: Path) -> dict:
    archive = Path(archive)
    if not archive.is_file() or archive.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError('archive missing or too large')
    with ZipFile(archive) as z:
        members = z.namelist()
        if len(members) > 4000 or len(set(members)) != len(members):
            raise ValueError('archive entries invalid')
        for name in members:
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name:
                raise ValueError('unsafe archive path')
        summaries = [n for n in members if n == 'batch_summary.json' or n.endswith('/batch_summary.json')]
        if len(summaries) != 1:
            raise ValueError('expected exactly one batch summary')
        batch = _load_json(z, summaries[0])
        if batch.get('schema_id') != 'defluens.pilot-batch' or batch.get('mode') != 'full':
            raise ValueError('requires a full WordBench practical campaign')
        items = []
        seen = set()
        for name in sorted(n for n in members if n.endswith('/pilot_run.json')):
            run = _load_json(z,name)
            lang = run.get('language')
            if lang not in LANGUAGES or lang in seen:
                raise ValueError('invalid or duplicated language report')
            seen.add(lang)
            scenarios = run.get('scenarios')
            if not isinstance(scenarios,list): raise ValueError('missing scenarios')
            seen_scenarios = set()
            for s in scenarios:
                if not isinstance(s,dict): raise ValueError('invalid scenario')
                key = s.get('id')
                if key not in CROSSWALK or key in seen_scenarios: raise ValueError('unknown/duplicate scenario')
                seen_scenarios.add(key)
                source, script = s.get('source_sha256'),s.get('script_sha256')
                if not isinstance(source,str) or not SHA.fullmatch(source) or not isinstance(script,str) or not SHA.fullmatch(script):
                    raise ValueError(f'missing/invalid source identity: {lang} {key}')
                candidate = s.get('candidate')
                if s.get('status') == 'candidate_for_review' and (not isinstance(candidate,str) or not candidate.strip()):
                    raise ValueError(f'missing candidate text: {lang} {key}')
                op, match = CROSSWALK[key]
                items.append({'language':lang, 'scenario_id':key, 'gf_status':s.get('status'),
                              'source_sha256_reported':source, 'script_sha256_reported':script,
                              'candidate_sha256':hashlib.sha256(candidate.encode('utf-8')).hexdigest()
                                  if isinstance(candidate,str) else None,
                              'sa_operation_candidate':op,'mapping_status':match})
            if seen_scenarios != set(CROSSWALK):
                raise ValueError(f'incomplete language workload: {lang}')
        if not items: raise ValueError('no language reports')
        if {e.get('language') for e in batch.get('entries',[]) if isinstance(e,dict)} != seen:
            raise ValueError('batch language inventory differs from the reports')
    count_ok = sum(row['gf_status']=='candidate_for_review' for row in items)
    fully_tested = set(LANGUAGES)==seen and len(items)==len(LANGUAGES)*len(CROSSWALK)
    with archive.open('rb') as input_stream:
        archive_digest=hashlib.file_digest(input_stream, 'sha256').hexdigest()
    return {'schema_id':'defluens.wordbench-sa-development-handoff','schema_version':'1.0',
            'authority':'GF WordBench development evidence only',
            'archive_name':archive.name,'archive_sha256':archive_digest,
            'batch_id':batch.get('batch_id'), 'language_count':len(seen), 'scenario_count':len(items),
            'gf_candidates':count_ok, 'complete_14_language_workload':fully_tested,
            'gf_executed_by_wordbench':True, 'source_hashes_reverified':False,
            'sa_conformance_passed':False,'pgf_artifact_admitted':False,'release_ready':False,
            'publication_authorized':False,
            'next_gate':'build PGF + lexical artifact + versioned SA-GF bridge; run SemantiK candidate conformance',
            'rows':items}


def main(argv: list[str] | None = None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(argv)
    try:
        report=build_handoff(args.archive)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k!='rows'},ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError,BadZipFile) as exc:
        p.exit(2,f'Handoff rejected: {exc}\n')

if __name__=='__main__':raise SystemExit(main())
