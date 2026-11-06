"""Multi-language Ars Magna Defluens practical pilot campaign (no linguistic golds).

Each language runs the existing WordBench isolated GF pilot. The campaign is
incrementally checkpointed and continues after individual language errors.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import time
from zipfile import ZipFile, ZIP_DEFLATED

from gf_wordbench.practical.pilot import LANGUAGE_DIRECTORIES, _LANGUAGE_CATALOG, _validate_pilot, run_pilot

DEFAULT_LANGUAGES = tuple(_LANGUAGE_CATALOG['default_campaign'])
STATUS_NAMES = ('candidate_for_review', 'probe_failed', 'timeout', 'unverified')


def _json_atomic(path: Path, data: dict) -> None:
    tmp = path.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def _select_languages(languages: list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    requested = list(languages) if languages else list(DEFAULT_LANGUAGES)
    # Permit comma-separated codes or individual positional --languages codes.
    codes = [part.strip() for token in requested for part in token.split(',') if part.strip()]
    if not codes or len(set(codes)) != len(codes):
        raise ValueError('empty or duplicated language selection')
    unknown = [code for code in codes if code not in LANGUAGE_DIRECTORIES]
    if unknown:
        raise ValueError(f'no prepared pilot profile for: {", ".join(unknown)}. '
                         f'Available: {", ".join(LANGUAGE_DIRECTORIES)}')
    return tuple(codes)


def check_campaign(languages: tuple[str, ...]) -> dict:
    entries = []
    for code in languages:
        try:
            check = _validate_pilot(code)
            entries.append({'language': code, 'status': 'preflight_ok',
                            'scenario_count': check['scenario_count'],
                            'lexical_status': check['lexical_status']})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            entries.append({'language': code, 'status': 'preflight_failed',
                            'reason': f'{type(exc).__name__}: {str(exc)[:500]}'})
    return {'schema_id':'defluens.batch-preflight','schema_version':'1.0',
            'languages':entries,'ok':all(item['status']=='preflight_ok' for item in entries),
            'gf_executed':False,'semantic_coverage_verified':False}


def _summarize(entries: list[dict], total_languages: int) -> dict:
    totals = {status:sum(int(item.get('totals',{}).get(status,0)) for item in entries)
              for status in STATUS_NAMES}
    totals.update({'languages_requested':total_languages,
                   'languages_attempted':sum(item['status'] not in ('not_run',) for item in entries),
                   'languages_with_candidates':sum(item.get('totals',{}).get('candidate_for_review',0)>0 for item in entries),
                   'languages_with_issues':sum(item['status'] in ('partial','probe_failed','setup_error') for item in entries),
                   'languages_unattempted':total_languages-len(entries)})
    return totals


def _csv_report(entries: list[dict]) -> str:
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer)
    writer.writerow(('language','status','candidate_for_review','probe_failed','timeout','unverified','lexical_status','pilot_run','reason'))
    for item in entries:
        totals = item.get('totals',{})
        writer.writerow((item['language'],item['status'],*(totals.get(x,0) for x in STATUS_NAMES),
                         item.get('lexical_status',''),item.get('pilot_run',''),item.get('reason','')))
    return '\ufeff'+buffer.getvalue()


def _archive_campaign(batch_root: Path, archive_path: Path) -> None:
    """Portable evidence archive without duplicated per-language ZIP/.gfo files."""
    # No traversal outside batch; only reports, raw traces and review templates.
    with ZipFile(archive_path, 'w', compression=ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(batch_root.rglob('*')):
            if path.is_symlink():
                raise ValueError(f'not archiving symlink: {path}')
            if not path.is_file() or path.suffix.lower() in ('.zip','.gfo','.gf'):
                continue
            if path.name not in ('batch_summary.json','batch_summary.csv','README.txt','pilot_run.json','review_template.json') \
                    and 'scenarios' not in path.relative_to(batch_root).parts:
                continue
            z.write(path, arcname=(Path(batch_root.name)/path.relative_to(batch_root)).as_posix())


def run_campaign(*, languages: tuple[str,...], gf_executable: Path, rgl_root: Path,
                 output_root: Path, mode: str='smoke', timeout_sec: float=90,
                 max_minutes: float=45) -> dict:
    if mode not in ('smoke','full'):
        raise ValueError('mode must be smoke or full')
    if not 0 < max_minutes <= 1440:
        raise ValueError('max_minutes must be within 0 < max_minutes <= 1440')
    if not 0 < timeout_sec <= 3600:
        raise ValueError('timeout_sec must be within 0 < timeout_sec <= 3600')
    output_root=output_root.expanduser().resolve()
    # The campaign must not create even its checkpoint files in source trees.
    protected=(rgl_root.expanduser().resolve(),gf_executable.expanduser().resolve().parent,
               Path(__file__).resolve().parents[3] / 'pilots')
    for source in protected:
        if output_root == source or output_root.is_relative_to(source):
            raise ValueError(f'output directory must remain outside protected sources: {source}')
    if not gf_executable.is_file():
        raise ValueError(f'GF executable not found: {gf_executable}')
    if not (rgl_root/'src').is_dir() and not rgl_root.is_dir():
        raise ValueError(f'RGL directory not found: {rgl_root}')
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(time.time_ns())[-7:]
    batch_root=output_root/f'defluens-batch-{mode}-{run_id}'
    languages_root=batch_root/'languages'
    languages_root.mkdir(parents=True,exist_ok=False)
    start_monotonic=time.monotonic()
    archive_path=output_root/(batch_root.name+'.zip')
    summary={'schema_id':'defluens.pilot-batch','schema_version':'1.0','batch_id':run_id,
             'mode':mode,'languages_requested':list(languages),
             'started_at':datetime.now(timezone.utc).isoformat(),
             'batch_root':str(batch_root),'archive_path':str(archive_path),
             'gf_executable':str(gf_executable),'rgl_root':str(rgl_root),
             'semantic_coverage_verified':False,
             'note':'These are experimental generation probes. No native-speaker-approved golds or semantic readiness claims.',
             'entries':[],'status':'running'}
    note=(
        'ARS MAGNA DEFLUENS — CAMPAGNE PRATIQUE MULTILINGUE\n'
        'Rapports GF candidats seulement. Aucun résultat n’est un gold approuvé.\n'
        'La présence de texte ne prouve pas que la langue couvre la capacité.\n'
        'La campagne est sauvegardée après chaque langue. Un échec ne stoppe pas le lot.\n'
        'Les dossiers complets et les ZIP par langue restent dans languages/.\n'
        'Le ZIP global contient les rapports JSON, candidats et journaux, sans les .gfo.\n'
        'La revue linguistique humaine et les preuves WordBench officielles restent nécessaires.\n'
    )
    (batch_root/'README.txt').write_text(note,encoding='utf-8')

    def save() -> None:
        summary['totals']=_summarize(summary['entries'],len(languages))
        _json_atomic(batch_root/'batch_summary.json',summary)
        (batch_root/'batch_summary.csv').write_text(_csv_report(summary['entries']),encoding='utf-8')

    save()
    for index, code in enumerate(languages, 1):
        if time.monotonic()-start_monotonic >= 60*max_minutes:
            summary['status']='time_budget_reached'
            print(f'Limite de {max_minutes:g} minutes atteinte : les langues restantes ne sont pas lancées.',flush=True)
            break
        print(f'[{index}/{len(languages)}] {code} — {mode}: lancement GF...',flush=True)
        try:
            kwargs={'gf_executable':gf_executable,'rgl_root':rgl_root,'output_root':languages_root,
                    'timeout_sec':timeout_sec,'export_zip':True,
                    'on_progress':lambda n,total,sid,status: print(
                        f'           ({n:02}/{total:02}) {sid}: {status}', flush=True)}
            if mode=='smoke':
                kwargs['scenarios']=('factual-present',)
            result=run_pilot(code,**kwargs)
            counts=result['totals']
            attempted=len(result['scenarios'])
            candidates=counts['candidate_for_review']
            status='candidate_for_review' if candidates==attempted else ('partial' if candidates else 'probe_failed')
            item={'language':code,'status':status,'totals':counts,
                  'scenarios_attempted':attempted,'lexical_status':result['lexical_status'],
                  'pilot_run':str(Path(result['archive_path']).with_suffix('')/'pilot_run.json'),
                  'language_archive_path':result['archive_path'],
                  'reason':'linguistic_review_missing' if candidates else 'gf_probe_failed_or_timeout'}
            print(f'           {candidates}/{attempted} candidates, '
                  f"{counts['probe_failed']} erreurs, {counts['timeout']} délais.",flush=True)
        except (Exception) as exc:
            item={'language':code,'status':'setup_error','totals':{},
                  'scenarios_attempted':0,'reason':f'{type(exc).__name__}: {str(exc)[:700]}'}
            print(f'           CONFIGURATION/EXÉCUTION IMPOSSIBLE : {item["reason"]}',flush=True)
        summary['entries'].append(item)
        save()
    if summary['status']=='running':
        summary['status']='completed_unverified'
    summary['finished_at']=datetime.now(timezone.utc).isoformat()
    summary['elapsed_seconds']=round(time.monotonic()-start_monotonic,2)
    save()
    _archive_campaign(batch_root,archive_path)
    return summary


def main(argv:list[str]|None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('check','run'))
    parser.add_argument('--languages',nargs='+',help='codes (spaces or commas); default: 20 prepared languages')
    parser.add_argument('--mode',choices=('smoke','full'),default='smoke')
    parser.add_argument('--gf-executable',type=Path,default=Path(r'C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe'))
    parser.add_argument('--rgl-root',type=Path,default=Path(r'C:\mycode\Grammatical-Framework\gf-rgl'))
    parser.add_argument('--output-root',type=Path,default=Path.home()/'Downloads'/'Ars_Magna_Defluens'/'practical_pilot_runs')
    parser.add_argument('--timeout',type=float,default=90)
    parser.add_argument('--max-minutes',type=float,default=45)
    args=parser.parse_args(argv)
    try:
        languages=_select_languages(args.languages)
        if args.action=='check':
            report=check_campaign(languages)
            print(json.dumps(report,ensure_ascii=False,indent=2))
            return 0 if report['ok'] else 1
        summary=run_campaign(languages=languages,gf_executable=args.gf_executable,
                              rgl_root=args.rgl_root,output_root=args.output_root,
                              mode=args.mode,timeout_sec=args.timeout,max_minutes=args.max_minutes)
        print(json.dumps({'status':summary['status'],'batch_root':summary['batch_root'],
                          'archive_path':summary['archive_path'],'totals':summary['totals']},
                         ensure_ascii=False,indent=2))
        return 0 if summary['status']=='completed_unverified' and not summary['totals']['languages_with_issues'] else 1
    except (OSError,ValueError,KeyError) as exc:
        print(f'Campaign error: {type(exc).__name__}: {exc}',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
