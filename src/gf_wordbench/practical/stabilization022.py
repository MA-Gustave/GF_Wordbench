"""Run only the 7 changed v0.2.2 GF probes, preserving their raw evidence.

The focus remains 14 languages/15 semantic capabilities; this selective run
compiles only the seven revised scenarios, never declares linguistic readiness.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from zipfile import ZipFile, ZIP_DEFLATED

from gf_wordbench.practical.alignment14 import PILOTS, read_policy
from gf_wordbench.practical.pilot import _validate_pilot, run_pilot

POLICY = PILOTS / 'lexical_stabilization_focus14_v022.json'
DEFAULT_OUT = Path.home() / 'Downloads' / 'Ars_Magna_Defluens' / 'practical_pilot_runs'
DEFAULT_GF = Path(r'C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe')
DEFAULT_RGL = Path(r'C:\mycode\Grammatical-Framework\gf-rgl')


def selected_changes(policy_path: Path = POLICY) -> dict[str, tuple[str, ...]]:
    data=json.loads(policy_path.read_text(encoding='utf-8'))
    if data.get('schema_id')!='defluens.lexical-stabilization' or data.get('schema_version')!='0.2.2':
        raise ValueError('unknown lexical-stabilization policy')
    languages=set(read_policy()['languages'])
    groups: dict[str,list[str]]={}
    for item in data['changes']:
        code,sid=item['lang'],item['scenario']
        if code not in languages or not sid or (sid in groups.get(code,[])):
            raise ValueError('invalid language or duplicated scenario in change policy')
        groups.setdefault(code,[]).append(sid)
    if sum(map(len,groups.values())) != data['scenarios_patched'] or not groups:
        raise ValueError('changed scenario count does not match declared policy')
    return {lang:tuple(ids) for lang,ids in groups.items()}


def run_changed(*, gf:Path, rgl:Path, output_root:Path=DEFAULT_OUT,
                timeout:float=90.0, max_minutes:float=45.0,
                pilots_root:Path=PILOTS, policy_path:Path=POLICY)->dict:
    if timeout<=0 or max_minutes<=0:
        raise ValueError('timeout and max-minutes must be positive')
    groups=selected_changes(policy_path)
    for lang in read_policy()['languages']:
        _validate_pilot(lang,pilots_root=pilots_root)
    started=time.monotonic()
    name='defluens-stabilization-v022-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(time.time_ns())[-7:]
    root=output_root.expanduser().resolve()/name
    root.mkdir(parents=True,exist_ok=False)
    results={'schema_id':'defluens.lexical-stabilization-batch','schema_version':'0.2.2',
             'source_root':str(pilots_root),'gf_executable':str(gf),'rgl_root':str(rgl),
             'started_at':datetime.now(timezone.utc).isoformat(),
             'status':'in_progress','semantic_coverage_verified':False,'gold_approved':False,
             'expected_changes':sum(map(len,groups.values())),
             'languages':{},'totals':{}}
    def save():
        (root/'stabilization_summary.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    save()
    try:
        for lang,ids in groups.items():
            if (time.monotonic()-started)>max_minutes*60:
                results['languages'][lang]={'status':'not_run_budget_exhausted','scenario_count':len(ids)}
                save()
                continue
            print(f'[{lang}] {len(ids)} sondes corrigees',flush=True)
            try:
                def progress(done:int,total:int,sid:str,status:str):
                    print(f'  [{done}/{total}] {sid}: {status}',flush=True)
                report=run_pilot(lang,gf_executable=gf,rgl_root=rgl,
                                 output_root=root/'languages',pilots_root=pilots_root,
                                 timeout_sec=timeout,scenarios=ids,on_progress=progress)
                results['languages'][lang]={
                    'status':'completed','scenario_count':len(report['scenarios']),
                    'run_id':report['run_id'], 'totals':report['totals'],
                    'candidates':{s['id']:s.get('candidate') for s in report['scenarios']},
                }
            except Exception as exc:
                results['languages'][lang]={'status':'execution_error',
                                             'scenario_count':len(ids),
                                             'exception':f'{type(exc).__name__}: {str(exc)[:400]}'}
            save()
    finally:
        counter=Counter()
        for record in results['languages'].values():
            if record['status']=='completed':counter.update(record.get('totals',{}))
            else:counter[record['status']]+=record['scenario_count']
        results['status']='completed_with_failures' if counter.get('probe_failed',0)+counter.get('timeout',0)+counter.get('execution_error',0)+counter.get('not_run_budget_exhausted',0)+counter.get('unverified',0) else 'completed_candidates_only'
        results['totals']=dict(counter)
        results['finished_at']=datetime.now(timezone.utc).isoformat()
        archive=root.with_suffix('.zip')
        results['archive_path']=str(archive)
        save()
        with ZipFile(archive,'w',compression=ZIP_DEFLATED,compresslevel=6) as z:
            for p in sorted(root.rglob('*')):
                if p.is_symlink():raise ValueError(f'refusing symlink in archive: {p}')
                if p.is_file():z.write(p,arcname=(Path(root.name)/p.relative_to(root)).as_posix())
        print('Archive partageable :',archive,flush=True)
    return results


def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('check','run'))
    p.add_argument('--gf-executable',type=Path,default=DEFAULT_GF)
    p.add_argument('--rgl-root',type=Path,default=DEFAULT_RGL)
    p.add_argument('--output-root',type=Path,default=DEFAULT_OUT)
    p.add_argument('--timeout',type=float,default=90.0)
    p.add_argument('--max-minutes',type=float,default=45.0)
    a=p.parse_args(argv)
    try:
        groups=selected_changes()
        if a.action=='check':
            for lang in read_policy()['languages']:_validate_pilot(lang)
            report={'status':'preflight_ok','languages_changed':list(groups),
                    'changed_scenarios':sum(len(v) for v in groups.values()),
                    'gf_executed':False,'gold_approved':False}
        else:
            report=run_changed(gf=a.gf_executable,rgl=a.rgl_root,output_root=a.output_root,
                               timeout=a.timeout,max_minutes=a.max_minutes)
        print(json.dumps(report,ensure_ascii=False,indent=2))
        return 0 if a.action=='check' or report['status']=='completed_candidates_only' else 1
    except (ValueError,OSError,KeyError) as exc:
        print(f'Stabilization error: {type(exc).__name__}: {exc}',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
