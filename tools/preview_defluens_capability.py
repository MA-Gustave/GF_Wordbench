"""One real GF run for one of the 15 Defluens pilot intents, in one prepared language.

This delegates to gf_wordbench.practical.pilot.run_pilot, preserving the real
compiler output and source hashes. No PGF release, no SA semantic request, no
linguistic qualification, and no manipulation of the RGL source checkout.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT/'src') not in sys.path:
    sys.path.insert(0,str(ROOT/'src'))
from gf_wordbench.practical.pilot import LANGUAGE_DIRECTORIES, _validate_pilot, run_pilot
from gf_wordbench.practical.coverage import load_profile, selected_scenario_ids

PROFILE=ROOT/'profiles/practical_generation_v1.json'
INTENTS=selected_scenario_ids(load_profile(PROFILE))

def run_one(*, language: str, capability: str, gf_executable: Path,
            rgl_root: Path, output_root: Path, timeout_sec: float=90) -> dict:
    if language not in LANGUAGE_DIRECTORIES:
        raise ValueError('Unknown prepared RGL language')
    if capability not in INTENTS:
        raise ValueError('Unknown practical semantic intent')
    result=run_pilot(language,gf_executable=gf_executable,rgl_root=rgl_root,
                     output_root=output_root,timeout_sec=timeout_sec,
                     scenarios=(capability,),export_zip=True)
    case=result['scenarios'][0]
    return {'schema_id':'defluens.single-gf-preview','schema_version':'1.0',
            'language':language,'capability':capability,'status':case['status'],
            'candidate':case.get('candidate'), 'reason':case.get('reason'),
            'meaning_en':case.get('meaning_en'),'source_sha256':case.get('source_sha256'),
            'script_sha256':case.get('script_sha256'),
            'run_id':result['run_id'],'archive_path':result['archive_path'],
            'gf_executed':True,'sa_semantic_request_executed':False,
            'sa_bridge_verified':False,'semantic_coverage_verified':False,
            'released':False,'linguistically_certified':False}

def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--language',required=True,choices=tuple(LANGUAGE_DIRECTORIES))
    p.add_argument('--capability',required=True,choices=INTENTS)
    p.add_argument('--gf-executable',type=Path,required=True)
    p.add_argument('--rgl-root',type=Path,required=True)
    p.add_argument('--output-root',type=Path,required=True)
    p.add_argument('--timeout',type=float,default=90)
    p.add_argument('--preflight',action='store_true',help='Check locked source only; do not run GF')
    args=p.parse_args(argv)
    try:
        if args.preflight:
            result=_validate_pilot(args.language)
            out={'schema_id':'defluens.single-gf-preflight','schema_version':'1.0',
                 'language':args.language,'capability':args.capability,
                 'gf_executed':False,'source_locked':True,
                 'gold_approved':False,'status':'PREFLIGHT_OK'}
        else:
            out=run_one(language=args.language,capability=args.capability,
                        gf_executable=args.gf_executable,rgl_root=args.rgl_root,
                        output_root=args.output_root,timeout_sec=args.timeout)
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return 0 if out['status'] in ('PREFLIGHT_OK','candidate_for_review') else 1
    except (ValueError,OSError,KeyError,RuntimeError) as exc:
        print(json.dumps({'status':'BLOCKED','gf_executed':False,
            'error':f'{type(exc).__name__}: {exc}'},ensure_ascii=False))
        return 2

if __name__=='__main__':
    raise SystemExit(main())
