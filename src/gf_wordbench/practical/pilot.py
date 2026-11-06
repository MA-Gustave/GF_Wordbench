"""Isolated 15-capability RGL pilots using WordBench's native GF process boundary.

This is an experimental probe tool. It emits a pilot-specific result, NOT a
canonical WordBench summary or independently verified semantic readiness.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import time
from zipfile import ZIP_DEFLATED, ZipFile
from types import SimpleNamespace

from gf_wordbench.practical.coverage import load_profile, selected_scenario_ids
from gf_wordbench.validation.scenarios.parser import parse_scenario_text
from gf_wordbench.validation.scenarios.profile_catalog import _verified_input_paths, _expected_sections
from gf_wordbench.validation.scenarios.execution import (
    ScenarioScriptInput, prepare_and_execute_scenario,
)
from gf_wordbench.validation.scenarios.markers import evaluate_scenario_markers

_LANGUAGE_CATALOG = json.loads((_root_path := Path(__file__).resolve().parents[3] /
   'pilots' / 'practical_generation_v1' / 'language_catalog.json').read_text(encoding='utf-8'))
LANGUAGE_DIRECTORIES = {code: entry['rgl_directory']
                        for code, entry in _LANGUAGE_CATALOG['languages'].items()}
SHELL_FAILURE = re.compile(
    r'(?:Internal error|unknown label|constant not found|File .* does not exist|'
    r'error in|error occurred|unknown qualified constant|parse error|type error|'
    r'expected a value of type|cannot find an inflection rule|not in scope|'
    r'unknown function|no concrete syntax|empty grammar, no abstract|'
    r'warning:.*not found|Happened in linearization|no overload instance|Syntax error:|Unexpected token)', re.I,
)


def _root() -> Path:
    return Path(__file__).resolve().parents[3] / 'pilots' / 'practical_generation_v1'


def _pilot_root(language: str, pilots_root: Path | None = None) -> Path:
    if language not in LANGUAGE_DIRECTORIES:
        raise ValueError(f'unsupported pilot language: {language}; prepared pilots: {", ".join(LANGUAGE_DIRECTORIES)}')
    return (pilots_root or _root()) / language


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_pilot(language: str, *, pilots_root: Path | None = None, practical_profile: Path | None = None) -> dict:
    root = _pilot_root(language, pilots_root).resolve(strict=True)
    manifest = json.loads((root / 'pilot_manifest.json').read_text(encoding='utf-8'))
    profile = load_profile(practical_profile or _root().parents[1] / 'profiles' / 'practical_generation_v1.json')
    scenarios = selected_scenario_ids(profile)
    if manifest['language_code'] != language or manifest['rgl_directory'] != LANGUAGE_DIRECTORIES[language]:
        raise ValueError('pilot manifest identity mismatch')
    items = manifest['scenarios']
    if len(items) != len(scenarios) or tuple(entry['id'] for entry in items) != scenarios:
        raise ValueError('pilot manifest does not match the 15 required capabilities')
    for entry in items:
        sid = entry['id']
        path = (root / entry['script']).resolve(strict=True)
        if not path.is_relative_to(root) or path.is_symlink():
            raise ValueError('scenario script escapes pilot root')
        contents = path.read_text(encoding='utf-8')
        parsed = parse_scenario_text(contents, scenario_id=sid, source_path=path)
        if not parsed.valid:
            raise ValueError(f'{sid}: invalid GF script: ' + '; '.join(str(x.code) for x in parsed.issues))
        locked = _verified_input_paths(contents, project_root=root)
        if len(locked) != 2:
            raise ValueError(f'{sid}: expected exactly two locked GF inputs')
        for relative in locked:
            source = (root / relative).resolve(strict=True)
            if not source.is_relative_to(root) or source.is_symlink():
                raise ValueError(f'{sid}: source escapes pilot root')
        if _expected_sections(contents,scenario_id=sid) != ('linearize',):
            raise ValueError(f'{sid}: incomplete linearization section')
        if _sha256(path) != entry['script_sha256']:
            raise ValueError(f'{sid}: script differs from locked manifest')
        source = (root / 'validation' / 'inputs' / entry['module']).resolve(strict=True)
        if _sha256(source) != entry['source_sha256']:
            raise ValueError(f'{sid}: GF module differs from manifest')
    return {'language':language,'pilot_root':str(root),'scenario_count':len(items),
            'scenario_ids':list(scenarios), 'status':'preflight_ok', 'gf_executed':False,
            'gold_approved':bool(manifest.get('gold_approved',False)),
            'lexical_status':manifest.get('lexical_status','provisional_unreviewed')}


def _gf_paths(rgl_root: Path, language: str) -> tuple[Path, ...]:
    src = rgl_root / 'src' if (rgl_root/'src').is_dir() else rgl_root
    if not src.is_dir():
        raise ValueError(f'RGL src not found: {src}')
    dirs = [LANGUAGE_DIRECTORIES[language], 'abstract','api','prelude','common',
            'romance','scandinavian','hindustani','bantu','english','zulu/abstract_ext','.']
    paths = []
    for directory in dirs:
        candidate = (src / directory).resolve()
        if candidate.is_dir() and candidate not in paths:
            paths.append(candidate)
    target = (src / LANGUAGE_DIRECTORIES[language]).resolve()
    if target not in paths:
        raise ValueError(f'language source directory not found: {target}')
    return tuple(paths)


def _candidate(section: object) -> str:
    raw = str(getattr(section, 'text', ''))
    # Keep actual GF shell output; strip only blank outer lines. A human must
    # inspect it before it may become an approved gold reference.
    return raw.strip().replace('\r\n','\n').replace('\r','\n')


def run_pilot(
    language: str, *, gf_executable: Path, rgl_root: Path, output_root: Path,
    pilots_root: Path | None = None, practical_profile: Path | None = None,
    timeout_sec: float = 120.0, scenarios: tuple[str, ...] | None = None,
    export_zip: bool = False,
    on_progress: Callable[[int,int,str,str],None] | None = None,
) -> dict:
    check = _validate_pilot(language,pilots_root=pilots_root, practical_profile=practical_profile)
    root = Path(check['pilot_root'])
    gf = gf_executable.expanduser().resolve(strict=True)
    if not gf.is_file():
        raise ValueError(f'GF executable is not a file: {gf}')
    paths = _gf_paths(rgl_root.expanduser().resolve(strict=True),language)
    if timeout_sec <= 0 or timeout_sec > 3600:
        raise ValueError('timeout_sec must be within 0 < timeout_sec <= 3600')
    ids = tuple(scenarios or check['scenario_ids'])
    if not ids or len(set(ids)) != len(ids) or not set(ids).issubset(check['scenario_ids']):
        raise ValueError('scenario selection is empty, duplicated or unknown')
    output_root = output_root.expanduser().resolve()
    if output_root == root or output_root.is_relative_to(root) or root.is_relative_to(output_root):
        raise ValueError('output root must be separate from the pilot sources')
    if output_root == gf.parent or output_root.is_relative_to(gf.parent):
        raise ValueError('output root cannot be inside GF installation')
    for path in paths:
        if output_root == path or output_root.is_relative_to(path):
            raise ValueError('output root cannot be inside the RGL sources')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + str(time.time_ns())[-7:]
    run_root = output_root / f'defluens-pilot-{language}-{run_id}'
    raw_root = run_root / 'scenarios'
    inputs_root = run_root / 'inputs'
    inputs_root.mkdir(parents=True, exist_ok=False)
    raw_root.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((root / 'pilot_manifest.json').read_text(encoding='utf-8'))
    selected = {item['id']:item for item in manifest['scenarios'] if item['id'] in ids}
    result = {'schema_id':'defluens.pilot-run','schema_version':'1.0','language':language,
              'run_id':run_id, 'source_root':str(root),'rgl_root':str(rgl_root.resolve()),
              'gf_executable':str(gf),'started_at':datetime.now(timezone.utc).isoformat(),
              'status':'unverified','semantic_coverage_verified':False,
              'lexical_status':check['lexical_status'],
              'note':'Experimental GF generation probes. Not a canonical WordBench run. No linguistic readiness certified.',
              'scenarios':[]}
    for sid in ids:
        entry = selected[sid]
        scenario_file = root / entry['script']
        script = ScenarioScriptInput.from_bytes(scenario_id=sid,script_path=scenario_file,content=scenario_file.read_bytes())
        # Copy immutable locked source inputs to a disposable working directory:
        # GF may produce .gfo files, never inside the checked-in pilot sources.
        for name in (entry['module'],entry['abstract_module']):
            target = inputs_root / name
            original = root / 'validation' / 'inputs' / name
            if not target.exists():
                shutil.copyfile(original,target)
        argv = tuple(v for p in (inputs_root, *paths) for v in ('-i',str(p))) + ('--run',)
        dest_stdout = raw_root / f'{sid}.stdout.txt'
        dest_stderr = raw_root / f'{sid}.stderr.txt'
        item = {'id':sid,'semantic_intent':entry['semantic_intent'],
                'meaning_en':entry['meaning_en'], 'status':'unverified',
                'gold_match':None,'review_approved':False,
                'module':entry['module'], 'source_sha256':entry['source_sha256'],
                'script_sha256':entry['script_sha256'],
                'stdout':str(dest_stdout),'stderr':str(dest_stderr),
                'candidate':None,'reason':'gf_not_started'}
        try:
            proc = prepare_and_execute_scenario(
                script, executable=gf, args=argv, working_directory=inputs_root,
                stdout_path=dest_stdout, stderr_path=dest_stderr,
                timeout_sec=timeout_sec, output_limit_bytes=2*1024*1024,
                approved_read_roots=(run_root,gf.parent,*paths),
                approved_write_roots=(run_root,),
                request_id=f"pilot-{sid}", operation_id=f"pilot-{sid}",
            )
            stdout = dest_stdout.read_text(encoding='utf-8',errors='replace') if dest_stdout.exists() else ''
            stderr = dest_stderr.read_text(encoding='utf-8',errors='replace') if dest_stderr.exists() else ''
            marker = evaluate_scenario_markers(SimpleNamespace(expected_sections=('linearize',)),stdout)
            candidate = _candidate(marker.sections[0]) if marker.sections else ''
            item['exit_code']=proc.exit_code
            item['timed_out']=proc.timed_out
            item['duration_ms']=proc.duration_ms
            # GF can print a runtime/compile error *between* valid markers.
            # Such diagnostics are never a linguistic candidate or gold.
            if proc.timed_out:
                item['status']='timeout'; item['reason']='gf_timeout'
            elif proc.exit_code != 0:
                item['status']='probe_failed'; item['reason']='gf_exit_nonzero'
            elif SHELL_FAILURE.search(stdout+'\n'+stderr):
                item['status']='probe_failed'; item['reason']='gf_reported_error'
            elif not marker.complete:
                item['status']='probe_failed'; item['reason']='gf_output_markers_incomplete'
            elif not candidate:
                item['status']='probe_failed'; item['reason']='gf_output_empty'
            else:
                item['status']='candidate_for_review'; item['reason']='gold_and_linguistic_review_missing'
                item['candidate']=candidate
                candidate_path = raw_root / f'{sid}.candidate.txt'
                candidate_path.write_text(candidate+'\n',encoding='utf-8')
                item['candidate_path']=str(candidate_path)
        except Exception as exc:
            item['status']='probe_failed'
            item['reason']=f'{type(exc).__name__}: {str(exc)[:700]}'
            item['exception_type']=type(exc).__name__
        result['scenarios'].append(item)
        _write_report(run_root,result)
        if on_progress is not None:
            on_progress(len(result['scenarios']),len(ids),sid,item['status'])
    result['finished_at']=datetime.now(timezone.utc).isoformat()
    result['totals']={name:sum(x['status']==name for x in result['scenarios'])
                      for name in ('candidate_for_review','probe_failed','timeout','unverified')}
    result['review_template_path']=str(run_root / 'review_template.json')
    (run_root/'review_template.json').write_text(json.dumps({
        'schema_id':'defluens.pilot-review-template','language':language,'run_id':run_id,
        'instructions':'Human review required. Do not approve GF output solely because it was generated.',
        'decisions':[{'id':x['id'],'meaning_en':x['meaning_en'], 'candidate':x['candidate'],
                      'approved':False,'reviewer':'','notes':''} for x in result['scenarios']]
        },ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if export_zip:
        archive = run_root.with_suffix('.zip')
        # Set the future ZIP path in the JSON before archiving it, so the
        # portable report and the on-disk report match byte-for-byte.
        result['archive_path'] = str(archive)
        _write_report(run_root,result)
        with ZipFile(archive, 'w', compression=ZIP_DEFLATED) as handle:
            for file in sorted(run_root.rglob('*')):
                if file.is_symlink():
                    raise ValueError(f'refusing to include symlink in report ZIP: {file}')
                if file.is_file():
                    handle.write(file, arcname=(Path(run_root.name) / file.relative_to(run_root)).as_posix())
    return result


def _write_report(run_root:Path, result:dict) -> None:
    data = run_root / 'pilot_run.json'
    tmp = run_root / 'pilot_run.json.tmp'
    tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    tmp.replace(data)


def main(argv:list[str]|None=None) -> int:
    parser=argparse.ArgumentParser(prog='gf-wordbench-practical-pilot',description=__doc__)
    parser.add_argument('action',choices=('check','run'))
    parser.add_argument('--language',choices=tuple(LANGUAGE_DIRECTORIES),default='Eng')
    parser.add_argument('--gf-executable',type=Path)
    parser.add_argument('--rgl-root',type=Path)
    parser.add_argument('--output-root',type=Path)
    parser.add_argument('--pilots-root',type=Path)
    parser.add_argument('--practical-profile',type=Path)
    parser.add_argument('--timeout',type=float,default=120)
    parser.add_argument('--scenario',action='append',default=[])
    parser.add_argument('--export-zip',action='store_true',help='create a shareable report ZIP beside the run folder')
    args=parser.parse_args(argv)
    try:
        if args.action=='check':
            result=_validate_pilot(args.language,pilots_root=args.pilots_root,practical_profile=args.practical_profile)
        else:
            if not args.gf_executable or not args.rgl_root or not args.output_root:
                parser.error('run requires --gf-executable, --rgl-root and --output-root')
            result=run_pilot(args.language,gf_executable=args.gf_executable,rgl_root=args.rgl_root,
                             output_root=args.output_root,pilots_root=args.pilots_root,
                             practical_profile=args.practical_profile,timeout_sec=args.timeout,
                             scenarios=tuple(args.scenario) if args.scenario else None,
                             export_zip=args.export_zip)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if args.action=='check' else (1 if any(x['status']!='candidate_for_review' for x in result['scenarios']) else 0)
    except (ValueError,OSError,KeyError) as exc:
        print(f'Practical pilot error: {type(exc).__name__}: {exc}',file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
